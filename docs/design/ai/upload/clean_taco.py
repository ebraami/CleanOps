#!/usr/bin/env python3
"""
clean_taco.py — Audit and clean the TACO (YOLO format, Roboflow v3 export) dataset.

Pipeline
--------
1. AUDIT   Parse every label file and every image; collect statistics and defects
           (malformed lines, bad class ids, out-of-bounds / degenerate / duplicate
           boxes, corrupt images, orphan images/labels, image resolutions).
2. CLEAN   Fix what can be fixed safely (clip slightly out-of-bounds boxes, drop
           degenerate and exactly-duplicated boxes, drop corrupt/orphan files).
3. GROUP   Fingerprint every image with a flip/rotation-invariant perceptual hash
           (dHash) and group images that are the same photograph. The Roboflow export
           contains flipped/rotated copies of the same photo, and those copies are
           spread across train/valid/test (data leakage).
4. SPLIT   Either keep the original splits (and only report leakage) or re-split
           group-aware so that all copies of one photo land in the same split.
5. EXPORT  Write the cleaned dataset (images, labels, data.yaml), a JSON report and
           (optionally) PNG charts.

Usage
-----
  # Audit only (nothing is written except report + charts):
  python scripts/ai/clean_taco.py --src data/TACO --out data/TACO_clean \
         --report docs/design/ai/taco_report.json \
         --figures-dir docs/design/ai/figures --audit-only

  # Full clean with a leakage-free, group-aware re-split (default):
  python scripts/ai/clean_taco.py --src data/TACO --out data/TACO_clean \
         --report data/TACO_clean/taco_report.json --figures-dir data/TACO_clean/figures

  # Detection-only variant (single class "litter"; classification handled by a
  # separate classifier, as in the project's two-stage architecture):
  python scripts/ai/clean_taco.py --src data/TACO --out data/TACO_litter \
         --classes-mode single

Requirements: numpy, Pillow, PyYAML (matplotlib optional, for charts).
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageOps

SPLITS = ("train", "valid", "test")
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
COCO_SMALL_PX2 = 32 * 32
COCO_MEDIUM_PX2 = 96 * 96


def load_names(src: Path) -> list[str]:
    cfg = yaml.safe_load((src / "data.yaml").read_text(encoding="utf-8"))
    names = cfg["names"]
    if isinstance(names, dict):  # {0: 'a', 1: 'b'} form
        names = [names[k] for k in sorted(names)]
    if int(cfg.get("nc", len(names))) != len(names):
        print(f"[warn] data.yaml nc={cfg.get('nc')} but {len(names)} names listed")
    return list(names)


def list_images(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT) if folder.is_dir() else []


def pct(values, q):
    return float(np.percentile(values, q)) if len(values) else 0.0


def dhash_bits(img: Image.Image, n: int = 8) -> np.ndarray:
    g = img.convert("L").resize((n + 1, n), Image.LANCZOS)
    a = np.asarray(g, dtype=np.int16)
    return (a[:, 1:] > a[:, :-1]).flatten()


def canonical_hash(img: Image.Image) -> int:
    """64-bit dHash, minimised over the 8 flip/rotation variants (dihedral group),
    so a photo and its flipped/rotated copies receive the same fingerprint."""
    best = None
    for flip in (False, True):
        im = ImageOps.mirror(img) if flip else img
        for r in range(4):
            bits = dhash_bits(im.rotate(90 * r, expand=True))
            val = int("".join("1" if b else "0" for b in bits), 2)
            best = val if best is None else min(best, val)
    return best


_POP16 = np.array([bin(i).count("1") for i in range(1 << 16)], dtype=np.uint8)


def hamming_matrix_row(h: np.uint64, others: np.ndarray) -> np.ndarray:
    x = np.bitwise_xor(others, h)
    parts = x.view(np.uint16).reshape(-1, 4)
    return _POP16[parts].sum(axis=1)


class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


# --------------------------------------------------------------------------- #
# 1 + 2. Audit and clean labels / images
# --------------------------------------------------------------------------- #
def audit_and_clean(src: Path, nc: int, min_box_px: float, oob_tol: float):
    """Returns (records, defects). records: list of dicts, one per kept image."""
    defects = Counter()
    defect_examples = defaultdict(list)

    def flag(kind, where):
        defects[kind] += 1
        if len(defect_examples[kind]) < 5:
            defect_examples[kind].append(str(where))

    records = []
    for split in SPLITS:
        img_dir, lbl_dir = src / split / "images", src / split / "labels"
        images = {p.stem: p for p in list_images(img_dir)}
        labels = {p.stem: p for p in (lbl_dir.glob("*.txt") if lbl_dir.is_dir() else [])}

        for stem in sorted(set(labels) - set(images)):
            flag("orphan_label_dropped", labels[stem])

        for stem, ipath in sorted(images.items()):
            # image integrity + size
            try:
                with Image.open(ipath) as im:
                    im.verify()
                with Image.open(ipath) as im:
                    w_px, h_px = im.size
            except Exception:
                flag("corrupt_image_dropped", ipath)
                continue

            if stem not in labels:
                flag("orphan_image_dropped", ipath)
                continue

            boxes, seen = [], set()
            for ln, raw in enumerate(labels[stem].read_text(encoding="utf-8").splitlines(), 1):
                raw = raw.strip()
                if not raw:
                    continue
                parts = raw.split()
                if len(parts) != 5:
                    flag("malformed_line_dropped", f"{labels[stem]}:{ln}")
                    continue
                try:
                    cid_f = float(parts[0])
                    x, y, w, h = (float(v) for v in parts[1:])
                except ValueError:
                    flag("non_numeric_line_dropped", f"{labels[stem]}:{ln}")
                    continue
                if cid_f != int(cid_f) or not (0 <= int(cid_f) < nc):
                    flag("invalid_class_id_dropped", f"{labels[stem]}:{ln}")
                    continue
                cid = int(cid_f)
                if w <= 0 or h <= 0:
                    flag("non_positive_size_dropped", f"{labels[stem]}:{ln}")
                    continue
                x1, y1, x2, y2 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
                if x1 < -oob_tol or y1 < -oob_tol or x2 > 1 + oob_tol or y2 > 1 + oob_tol:
                    flag("out_of_bounds_clipped", f"{labels[stem]}:{ln}")
                x1, y1, x2, y2 = max(0.0, x1), max(0.0, y1), min(1.0, x2), min(1.0, y2)
                w, h = x2 - x1, y2 - y1
                if w * w_px < min_box_px or h * h_px < min_box_px:
                    flag("degenerate_box_dropped", f"{labels[stem]}:{ln}")
                    continue
                key = (cid, round(x1, 5), round(y1, 5), round(x2, 5), round(y2, 5))
                if key in seen:
                    flag("duplicate_box_dropped", f"{labels[stem]}:{ln}")
                    continue
                seen.add(key)
                boxes.append((cid, (x1 + x2) / 2, (y1 + y2) / 2, w, h))

            if not boxes:
                flag("no_valid_boxes_image_dropped", ipath)
                continue
            records.append(dict(split=split, image=ipath, stem=stem, size=(w_px, h_px), boxes=boxes))
    return records, defects, defect_examples


# --------------------------------------------------------------------------- #
# 3. Group same-photo images (leakage detection)
# --------------------------------------------------------------------------- #
def assign_groups(records, hamming: int):
    hashes = []
    for r in records:
        with Image.open(r["image"]) as im:
            hashes.append(canonical_hash(im))
    n = len(records)
    uf = UnionFind(n)
    if hamming <= 0:
        first = {}
        for i, h in enumerate(hashes):
            if h in first:
                uf.union(first[h], i)
            else:
                first[h] = i
    else:
        arr = np.array(hashes, dtype=np.uint64)
        for i in range(n):
            d = hamming_matrix_row(arr[i], arr[i + 1:])
            for j in np.nonzero(d <= hamming)[0]:
                uf.union(i, i + 1 + int(j))
    gid = {}
    for i, r in enumerate(records):
        r["group"] = gid.setdefault(uf.find(i), len(gid))
        r["hash"] = hashes[i]
    return len(gid)


def leakage_report(records):
    by_group = defaultdict(set)
    for r in records:
        by_group[r["group"]].add(r["split"])
    out = {"groups_total": len(by_group), "groups_in_multiple_splits": 0, "images_in_leaking_groups": {}}
    leaking = {g for g, s in by_group.items() if len(s) > 1}
    out["groups_in_multiple_splits"] = len(leaking)
    train_groups = {r["group"] for r in records if r["split"] == "train"}
    for s in ("valid", "test"):
        total = sum(1 for r in records if r["split"] == s)
        leaked = sum(1 for r in records if r["split"] == s and r["group"] in train_groups)
        out["images_in_leaking_groups"][s] = {"leaked_images": leaked, "total_images": total,
                                              "share": round(leaked / total, 4) if total else 0.0}
    return out


# --------------------------------------------------------------------------- #
# 4. Split
# --------------------------------------------------------------------------- #
def regroup_split(records, ratios, seed):
    """Group-aware, class-stratified split.

    * Every image of one photo group goes to the same split (no leakage).
    * Groups are processed rarest-class-first and each is given to the split that is
      currently furthest below its target for the classes the group contains, so rare
      classes (e.g. Broken glass) still reach valid/test instead of vanishing by chance.
    """
    groups = defaultdict(list)
    for r in records:
        groups[r["group"]].append(r)
    rng = random.Random(seed)

    g_cls = {}  # group -> Counter(class -> instances)
    for g, rs in groups.items():
        c = Counter()
        for r in rs:
            for b in r["boxes"]:
                c[b[0]] += 1
        g_cls[g] = c
    total_cls = Counter()
    for c in g_cls.values():
        total_cls.update(c)

    desired = {s: {c: total_cls[c] * ratios[i] for c in total_cls} for i, s in enumerate(SPLITS)}
    cur = {s: Counter() for s in SPLITS}
    n_target = {s: ratios[i] * len(records) for i, s in enumerate(SPLITS)}
    n_cur = {s: 0 for s in SPLITS}

    gids = sorted(groups)
    rng.shuffle(gids)
    gids.sort(key=lambda g: min(total_cls[c] for c in g_cls[g]))  # rarest class first (stable)

    for g in gids:
        def score(s):
            cls_part = sum((desired[s][c] - cur[s][c]) / max(desired[s][c], 1.0) for c in g_cls[g])
            img_part = (n_target[s] - n_cur[s]) / max(n_target[s], 1.0)
            return cls_part + img_part
        best = max(SPLITS, key=score)
        for r in groups[g]:
            r["new_split"] = best
        cur[best].update(g_cls[g])
        n_cur[best] += len(groups[g])


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
def compute_stats(records, names, split_key):
    stats = {}
    for s in SPLITS:
        rs = [r for r in records if r[split_key] == s]
        inst, img_with = Counter(), Counter()
        areas_px, n_per_img = [], []
        for r in rs:
            w_px, h_px = r["size"]
            n_per_img.append(len(r["boxes"]))
            for c in {b[0] for b in r["boxes"]}:
                img_with[c] += 1
            for c, _, _, w, h in r["boxes"]:
                inst[c] += 1
                areas_px.append((w * w_px) * (h * h_px))
        a = np.array(areas_px) if areas_px else np.array([0.0])
        stats[s] = dict(
            images=len(rs),
            annotations=int(sum(inst.values())),
            boxes_per_image=dict(mean=round(float(np.mean(n_per_img)), 2) if n_per_img else 0,
                                 median=float(np.median(n_per_img)) if n_per_img else 0,
                                 max=int(max(n_per_img)) if n_per_img else 0),
            instances_per_class={names[c]: int(inst[c]) for c in range(len(names))},
            images_per_class={names[c]: int(img_with[c]) for c in range(len(names))},
            box_area_px=dict(p10=round(pct(a, 10), 1), median=round(pct(a, 50), 1), p90=round(pct(a, 90), 1)),
            box_size_buckets=dict(
                small=round(float((a < COCO_SMALL_PX2).mean()), 4),
                medium=round(float(((a >= COCO_SMALL_PX2) & (a < COCO_MEDIUM_PX2)).mean()), 4),
                large=round(float((a >= COCO_MEDIUM_PX2).mean()), 4)),
        )
    return stats


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def make_charts(stats, names, fig_dir: Path, tag: str):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[warn] matplotlib not installed - skipping charts")
        return []
    fig_dir.mkdir(parents=True, exist_ok=True)
    made = []

    # class balance (train instances, sorted)
    tr = stats["train"]["instances_per_class"]
    order = sorted(tr, key=tr.get)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(order, [tr[k] for k in order], color="#2a7f62")
    for i, k in enumerate(order):
        ax.text(tr[k], i, f" {tr[k]}", va="center", fontsize=8)
    ax.set_xlabel("Annotated instances (train split)")
    ax.set_title(f"TACO class balance - {tag}")
    fig.tight_layout()
    p = fig_dir / f"class_balance_train_{tag}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    made.append(p)

    # per split share per class
    fig, ax = plt.subplots(figsize=(9, 6))
    tot = {k: sum(stats[s]["instances_per_class"][k] for s in SPLITS) for k in names}
    order = sorted(names, key=lambda k: tot[k])
    left = np.zeros(len(order))
    colors = {"train": "#2a7f62", "valid": "#e0a030", "test": "#c0504d"}
    for s in SPLITS:
        vals = np.array([stats[s]["instances_per_class"][k] / max(tot[k], 1) * 100 for k in order])
        ax.barh(order, vals, left=left, label=s, color=colors[s])
        left += vals
    ax.set_xlabel("Share of each class's instances per split (%)")
    ax.set_title(f"Class share per split - {tag}")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, frameon=False)
    fig.tight_layout()
    p = fig_dir / f"class_share_per_split_{tag}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    made.append(p)
    return made


# --------------------------------------------------------------------------- #
# 5. Export
# --------------------------------------------------------------------------- #
def export(records, names, out: Path, split_key, single_class: bool, link: bool):
    if out.exists():
        shutil.rmtree(out)
    for s in SPLITS:
        (out / s / "images").mkdir(parents=True)
        (out / s / "labels").mkdir(parents=True)
    for r in records:
        s = r[split_key]
        dst_img = out / s / "images" / r["image"].name
        if link:
            dst_img.symlink_to(r["image"].resolve())
        else:
            shutil.copy2(r["image"], dst_img)
        lines = []
        for c, x, y, w, h in r["boxes"]:
            cid = 0 if single_class else c
            lines.append(f"{cid} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
        (out / s / "labels" / (r["stem"] + ".txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_names = ["litter"] if single_class else names
    cfg = {"train": "train/images", "val": "valid/images", "test": "test/images",
           "nc": len(out_names), "names": out_names}
    (out / "data.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, type=Path, help="TACO dataset root (contains data.yaml, train/ valid/ test/)")
    ap.add_argument("--out", type=Path, help="output folder for the cleaned dataset")
    ap.add_argument("--report", type=Path, help="path of the JSON report to write")
    ap.add_argument("--figures-dir", type=Path, help="folder for PNG charts")
    ap.add_argument("--audit-only", action="store_true", help="audit and report only; do not write a cleaned dataset")
    ap.add_argument("--split-mode", choices=["regroup", "keep"], default="regroup",
                    help="regroup: leakage-free group-aware re-split (default); keep: original splits (leakage only reported)")
    ap.add_argument("--ratios", type=float, nargs=3, default=(0.8, 0.1, 0.1), metavar=("TRAIN", "VALID", "TEST"))
    ap.add_argument("--dedupe-groups", action="store_true",
                    help="keep ONE image per same-photo group (drops flipped/rotated copies)")
    ap.add_argument("--classes-mode", choices=["original", "single"], default="original",
                    help="single: collapse all classes to one 'litter' class (detection-only)")
    ap.add_argument("--hamming", type=int, default=0, help="max dHash Hamming distance to treat images as the same photo (0 = identical hash)")
    ap.add_argument("--min-box-px", type=float, default=1.0, help="drop boxes thinner than this many pixels")
    ap.add_argument("--oob-tol", type=float, default=0.01, help="normalised tolerance before a box counts as out-of-bounds")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--link", action="store_true", help="symlink images instead of copying")
    args = ap.parse_args()

    if not args.audit_only and not args.out:
        ap.error("--out is required unless --audit-only is set")
    if not (args.src / "data.yaml").exists():
        sys.exit(f"data.yaml not found in {args.src}")

    names = load_names(args.src)
    print(f"[1/5] Auditing {args.src}  ({len(names)} classes)")
    records, defects, examples = audit_and_clean(args.src, len(names), args.min_box_px, args.oob_tol)
    print(f"      kept {len(records)} images; defects: {dict(defects) or 'none'}")

    before = compute_stats(records, names, "split")
    for r in records:
        r["new_split"] = r["split"]

    print(f"[2/5] Fingerprinting images (hamming<={args.hamming}) ...")
    n_groups = assign_groups(records, args.hamming)
    leak = leakage_report(records)
    print(f"      {n_groups} distinct photos among {len(records)} images; "
          f"leakage into valid/test: {leak['images_in_leaking_groups']}")

    if args.dedupe_groups:
        seen, kept = set(), []
        for r in sorted(records, key=lambda r: (r["group"], r["split"] != "train", str(r["image"]))):
            if r["group"] in seen:
                continue
            seen.add(r["group"])
            kept.append(r)
        print(f"      --dedupe-groups: {len(records)} -> {len(kept)} images")
        records = kept

    print(f"[3/5] Split mode: {args.split_mode}")
    if args.split_mode == "regroup":
        regroup_split(records, args.ratios, args.seed)
    after = compute_stats(records, names, "new_split")

    post_leak = defaultdict(set)
    for r in records:
        post_leak[r["group"]].add(r["new_split"])
    post_leaking = sum(1 for s in post_leak.values() if len(s) > 1)

    sizes = Counter(f"{r['size'][0]}x{r['size'][1]}" for r in records)
    report = dict(source=str(args.src), classes=names, image_sizes=dict(sizes), defects=dict(defects),
                  defect_examples=examples, leakage_before=leak,
                  groups_still_in_multiple_splits_after=post_leaking,
                  stats_before=before, stats_after=after,
                  options=dict(split_mode=args.split_mode, ratios=list(args.ratios), dedupe_groups=args.dedupe_groups,
                               classes_mode=args.classes_mode, hamming=args.hamming, seed=args.seed))

    print("[4/5] Charts / report")
    if args.figures_dir:
        make_charts(before, names, args.figures_dir, "original_split")
        if args.split_mode == "regroup":
            make_charts(after, names, args.figures_dir, "clean_split")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"      report -> {args.report}")

    if args.audit_only:
        print("[5/5] --audit-only: no dataset written. Done.")
        return
    print(f"[5/5] Exporting cleaned dataset -> {args.out}")
    export(records, names, args.out, "new_split", args.classes_mode == "single", args.link)
    print("Done.  after-split image counts:", {s: after[s]["images"] for s in SPLITS},
          "| groups still crossing splits:", post_leaking)


if __name__ == "__main__":
    main()
