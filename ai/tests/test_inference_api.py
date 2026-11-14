"""Automated integration tests for the CleanOps inference API (ai/inference/app.py).

Run from the repository root:
    pip install -r ai/inference/requirements-dev.txt
    pytest ai/tests/test_inference_api.py -v

Most tests use a stub model (fast, no GPU, no weights needed) so the API contract is always tested:
upload handling, validation errors, JSON format, bounding boxes and image-coverage ratios.
One extra test runs the REAL trained weights if ai/models/yolov8n_cleanops_best.pt exists (otherwise it is skipped).
"""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

AI_DIR = Path(__file__).resolve().parents[1]
APP_PATH = AI_DIR / "inference" / "app.py"
WEIGHTS_PATH = AI_DIR / "models" / "yolov8n_cleanops_best.pt"

# load ai/inference/app.py as a module (the folders are not Python packages)
_spec = importlib.util.spec_from_file_location("cleanops_inference_app", APP_PATH)
inference_app = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = inference_app
_spec.loader.exec_module(inference_app)

CLASS_NAMES = {0: "Plastic", 1: "Paper/Cardboard", 2: "Glass", 3: "Metal", 4: "Organic/Trash"}


# --------------------------------------------------------------------------- #
# Stub model: mimics the parts of the Ultralytics API that the service uses
# --------------------------------------------------------------------------- #
class _FakeBoxes:
    def __init__(self, rows):
        arr = np.array(rows, dtype=float).reshape(-1, 6)
        self.xyxy, self.conf, self.cls = arr[:, :4], arr[:, 4], arr[:, 5]


class _FakeResult:
    def __init__(self, rows, image_size):
        self.boxes = _FakeBoxes(rows)
        self.orig_shape = (image_size[1], image_size[0])
        self.names = CLASS_NAMES


class StubModel:
    names = CLASS_NAMES

    def __init__(self, detections):
        self._detections = detections          # list of (x1, y1, x2, y2, conf, class_id), any order

    def predict(self, source, conf=0.25, iou=0.7, imgsz=640, max_det=100, verbose=False):
        keep = [d for d in self._detections if d[4] >= conf]
        keep = sorted(keep, key=lambda d: -d[4])[:max_det]
        return [_FakeResult(keep, source.size)]


def make_client(detections=(), loader=None, **settings_overrides):
    settings = inference_app.Settings(model_path=Path("stub_model.pt"), **settings_overrides)
    app = inference_app.create_app(settings, model_loader=loader or (lambda path: StubModel(list(detections))))
    return TestClient(app)


def png_bytes(width=640, height=480, color=(120, 160, 90)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


def jpeg_bytes_with_orientation(width, height, orientation) -> bytes:
    img = Image.new("RGB", (width, height), (200, 50, 50))
    exif = img.getexif()
    exif[0x0112] = orientation               # EXIF Orientation tag
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def upload(client, data: bytes, filename="street.png", content_type="image/png"):
    return client.post("/api/v1/detect", files={"file": (filename, data, content_type)})


# --------------------------------------------------------------------------- #
# /health
# --------------------------------------------------------------------------- #
def test_health_ok_when_model_loaded():
    with make_client() as client:
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["model_loaded"] is True
    assert body["classes"] == list(CLASS_NAMES.values())
    assert body["model_file"] == "stub_model.pt"          # file name only, never an absolute path


def test_health_degraded_when_weights_missing():
    def missing(path):
        raise FileNotFoundError(f"Model weights not found: {path}")

    with make_client(loader=missing) as client:
        r = client.get("/health")
        assert r.status_code == 503
        body = r.json()
        assert body["status"] == "degraded" and body["model_loaded"] is False
        assert "not found" in body["detail"]
        # detection must also refuse cleanly instead of crashing
        assert upload(client, png_bytes()).status_code == 503


# --------------------------------------------------------------------------- #
# /api/v1/detect - success path and JSON format
# --------------------------------------------------------------------------- #
TWO_BOXES = [
    (150, 150, 250, 250, 0.40, 1),   # lower confidence, listed first on purpose
    (100, 100, 200, 200, 0.90, 0),
]


def test_detect_returns_valid_json_schema():
    with make_client(TWO_BOXES) as client:
        r = upload(client, png_bytes(640, 480))
    assert r.status_code == 200
    body = r.json()

    parsed = inference_app.DetectResponse.model_validate(body)      # contract check: every field and type
    assert parsed.image.width == 640 and parsed.image.height == 480
    assert parsed.summary.detection_count == 2 == len(parsed.detections)
    assert parsed.inference_ms >= 0
    assert set(body) == {"image", "model", "detections", "summary", "report_flags", "inference_ms"}
    assert set(body["detections"][0]) == {"id", "class_id", "class_name", "confidence", "bbox", "bbox_normalized",
                                          "area_px", "coverage_ratio", "flags"}
    assert body["model"] == {"name": "stub_model", "conf_threshold": 0.25, "iou_threshold": 0.7,
                             "max_det": 100, "imgsz": 640}


def test_detections_sorted_by_confidence_with_class_names():
    with make_client(TWO_BOXES) as client:
        body = upload(client, png_bytes()).json()
    first, second = body["detections"]
    assert (first["id"], first["class_name"], first["confidence"]) == (1, "Plastic", 0.9)
    assert (second["id"], second["class_name"], second["confidence"]) == (2, "Paper/Cardboard", 0.4)
    assert body["summary"]["class_counts"] == {"Plastic": 1, "Paper/Cardboard": 1}


def test_bounding_box_coordinates_and_coverage_ratios():
    image_area = 640 * 480
    with make_client(TWO_BOXES) as client:
        body = upload(client, png_bytes(640, 480)).json()
    box = body["detections"][0]
    assert box["bbox"] == {"x1": 100.0, "y1": 100.0, "x2": 200.0, "y2": 200.0}
    assert box["bbox_normalized"] == pytest.approx(
        {"x_center": 150 / 640, "y_center": 150 / 480, "width": 100 / 640, "height": 100 / 480}, abs=1e-6)
    assert box["area_px"] == 10_000.0
    assert box["coverage_ratio"] == pytest.approx(10_000 / image_area, abs=1e-6)
    # the two boxes overlap in a 50x50 square: union = 10000 + 10000 - 2500 = 17500 (overlap counted once)
    assert body["summary"]["total_coverage_ratio"] == pytest.approx(17_500 / image_area, abs=1e-6)


def test_boxes_are_clipped_to_the_image():
    with make_client([(-20, -10, 700, 500, 0.8, 3)]) as client:
        body = upload(client, png_bytes(640, 480)).json()
    assert body["detections"][0]["bbox"] == {"x1": 0.0, "y1": 0.0, "x2": 640.0, "y2": 480.0}
    assert body["detections"][0]["coverage_ratio"] == 1.0
    assert body["summary"]["total_coverage_ratio"] == 1.0


def test_no_detections_is_a_valid_response():
    with make_client([]) as client:
        r = upload(client, png_bytes())
    assert r.status_code == 200
    body = r.json()
    assert body["detections"] == [] and body["summary"]["detection_count"] == 0
    assert body["summary"]["total_coverage_ratio"] == 0.0 and body["summary"]["class_counts"] == {}
    assert body["report_flags"] == ["no_waste_detected"]


def test_low_confidence_flag_and_cutoff():
    dets = [(0, 0, 50, 50, 0.90, 0), (60, 60, 120, 120, 0.30, 0), (200, 200, 250, 250, 0.10, 0)]
    with make_client(dets) as client:
        body = upload(client, png_bytes()).json()
    # 0.10 is below the 0.25 cut-off -> dropped; 0.30 is kept but flagged; 0.90 is confident
    assert [d["confidence"] for d in body["detections"]] == [0.9, 0.3]
    assert [d["flags"] for d in body["detections"]] == [[], ["low_det_conf"]]


def test_dense_scene_flag_when_max_det_reached():
    dets = [(i * 10, 0, i * 10 + 8, 8, 0.9 - i * 0.01, 0) for i in range(5)]
    with make_client(dets, max_det=3) as client:
        body = upload(client, png_bytes()).json()
    assert body["summary"]["detection_count"] == 3
    assert body["report_flags"] == ["dense_scene"]


@pytest.mark.parametrize("orientation, expected_size", [(1, (640, 480)), (6, (480, 640)), (8, (480, 640))])
def test_exif_orientation_is_applied(orientation, expected_size):
    with make_client([]) as client:
        body = upload(client, jpeg_bytes_with_orientation(640, 480, orientation),
                      "photo.jpg", "image/jpeg").json()
    assert (body["image"]["width"], body["image"]["height"]) == expected_size


def test_jpeg_upload_with_octet_stream_content_type_is_accepted():
    buf = io.BytesIO()
    Image.new("RGB", (320, 240)).save(buf, format="JPEG")
    with make_client([]) as client:
        r = upload(client, buf.getvalue(), "photo.jpg", "application/octet-stream")
    assert r.status_code == 200


# --------------------------------------------------------------------------- #
# /api/v1/detect - validation errors
# --------------------------------------------------------------------------- #
def test_rejects_non_image_content_type():
    with make_client() as client:
        r = upload(client, b"hello", "notes.txt", "text/plain")
    assert r.status_code == 415


def test_rejects_corrupt_image():
    with make_client() as client:
        r = upload(client, b"this is definitely not an image", "fake.png", "image/png")
    assert r.status_code == 400
    assert r.json()["detail"] == "The uploaded file is not a valid image"


def test_rejects_truncated_image():
    with make_client() as client:
        r = upload(client, png_bytes()[:60], "cut.png", "image/png")
    assert r.status_code == 400


def test_rejects_empty_file():
    with make_client() as client:
        r = upload(client, b"")
    assert r.status_code == 400
    assert r.json()["detail"] == "Empty file"


def test_rejects_file_over_upload_limit():
    big = png_bytes(1200, 1200)                                  # a few KB, so use a tiny limit
    with make_client(max_upload_mb=0.001) as client:             # 1 KB limit
        r = upload(client, big)
    assert r.status_code == 413


def test_rejects_image_with_too_many_pixels():
    with make_client(max_image_pixels=1000) as client:
        r = upload(client, png_bytes(640, 480))
    assert r.status_code == 413


def test_missing_file_field_returns_422():
    with make_client() as client:
        r = client.post("/api/v1/detect", files={"wrong_field": ("a.png", png_bytes(), "image/png")})
    assert r.status_code == 422


def test_inference_error_returns_500_without_leaking_details():
    class Broken:
        names = CLASS_NAMES

        def predict(self, *args, **kwargs):
            if kwargs.get("conf") is None:                       # warm-up call during startup must succeed
                return []
            raise RuntimeError("CUDA out of memory (secret internal detail)")

    with make_client(loader=lambda path: Broken()) as client:
        r = upload(client, png_bytes())
    assert r.status_code == 500
    assert r.json()["detail"] == "Inference failed"


def test_openapi_documents_both_endpoints():
    with make_client() as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert "/health" in paths and "/api/v1/detect" in paths


# --------------------------------------------------------------------------- #
# Geometry helper
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("boxes, expected", [
    ([], 0.0),
    ([(0, 0, 10, 10)], 100.0),                                   # single box
    ([(0, 0, 10, 10), (20, 20, 30, 30)], 200.0),                 # disjoint
    ([(0, 0, 10, 10), (5, 5, 15, 15)], 175.0),                   # partial overlap
    ([(0, 0, 10, 10), (2, 2, 8, 8)], 100.0),                     # one box inside the other
    ([(0, 0, 10, 10), (0, 0, 10, 10)], 100.0),                   # identical boxes
    ([(0, 0, 10, 10), (10, 0, 20, 10)], 200.0),                  # touching edges
    ([(0, 5, 30, 10), (5, 0, 10, 30)], 150 + 150 - 25),          # plus-shaped cross (overlap 5x5 counted once)
    ([(5, 5, 5, 20)], 0.0),                                      # zero-width box
])
def test_union_area(boxes, expected):
    assert inference_app.union_area(np.array(boxes, dtype=float)) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Real trained weights (skipped automatically when they are not in the repo)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not WEIGHTS_PATH.is_file(), reason="ai/models/yolov8n_cleanops_best.pt not found")
def test_real_weights_end_to_end():
    pytest.importorskip("ultralytics")
    settings = inference_app.Settings(model_path=WEIGHTS_PATH)
    with TestClient(inference_app.create_app(settings)) as client:
        assert client.get("/health").status_code == 200
        noise = np.random.default_rng(0).integers(0, 255, (480, 640, 3), dtype=np.uint8)
        buf = io.BytesIO()
        Image.fromarray(noise).save(buf, format="JPEG")
        r = upload(client, buf.getvalue(), "noise.jpg", "image/jpeg")
    assert r.status_code == 200
    parsed = inference_app.DetectResponse.model_validate(r.json())       # schema holds even with 0 detections
    assert parsed.image.width == 640 and parsed.image.height == 480
