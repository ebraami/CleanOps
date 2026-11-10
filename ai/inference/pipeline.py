"""
CleanStreet AI - Unified inference pipeline (P03 / Package 02)

YOLO detection -> bounding-box area ratios -> severity_calculator -> formatted response.

Usage:
    pipeline = SeverityPipeline(model_path="weights/best.pt")
    result = pipeline.run(image_bytes_or_path)
"""
from __future__ import annotations

import io
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Union

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("cleanstreet.pipeline")

SEVERITY_MIN, SEVERITY_MAX = 0.0, 10.0
LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

ImageInput = Union[bytes, bytearray, str, os.PathLike]


# --------------------------------------------------------------------------
# Severity: standalone calculator + aggregation of detections
# --------------------------------------------------------------------------
try:
    from ai.inference import severity_calculator as _sc
except ImportError:  # when run as a script from inside ai/inference
    import severity_calculator as _sc

calculate_severity = _sc.calculate_severity
HAZARD_WEIGHTS = getattr(_sc, "HAZARD_WEIGHTS", {})
DEFAULT_HAZARD = getattr(_sc, "DEFAULT_HAZARD", 0.3)

TAU_DET = 0.40  # ignore detections below this confidence

# detector (TACO) labels -> calculator waste classes (first keyword match wins)
_LABEL_KEYWORDS = (
    ("batter", "battery"), ("glass", "glass"),
    ("food", "organic"), ("organic", "organic"), ("biolog", "organic"),
    ("aluminium", "metal"), ("can", "metal"), ("pop tab", "metal"), ("metal", "metal"),
    ("paper", "paper"), ("carton", "paper"), ("cardboard", "paper"),
    ("plastic", "plastic"), ("bottle", "plastic"), ("cup", "plastic"), ("lid", "plastic"),
    ("straw", "plastic"), ("styrofoam", "plastic"), ("wrapper", "plastic"),
)


def map_label_to_class(label: str) -> str:
    """Map a detector label to a calculator class ('other' -> default hazard)."""
    low = str(label).lower()
    for kw, cls in _LABEL_KEYWORDS:
        if kw in low:
            return cls
    return "other"


def aggregate_detections(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collapse detections into calculator inputs: total area, most hazardous class, count."""
    classes = [map_label_to_class(d["label"]) for d in items]
    worst = max(classes, key=lambda c: HAZARD_WEIGHTS.get(c, DEFAULT_HAZARD))
    return {
        "area_ratio": round(min(1.0, sum(d["area_ratio"] for d in items)), 4),
        "waste_class": worst,
        "item_count": len(items),
    }


def score_to_level(score: float) -> str:
    fn = getattr(_sc, "severity_level", None)
    if callable(fn):
        return fn(score)
    return "CRITICAL" if score >= 7.5 else "HIGH" if score >= 5.0 else "MEDIUM" if score >= 2.5 else "LOW"


# --------------------------------------------------------------------------
# Detector interface (YOLO by default; any object with .detect() works)
# --------------------------------------------------------------------------
class Detector(Protocol):
    def detect(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Return [{'label': str, 'confidence': float, 'bbox': [x1, y1, x2, y2]}]"""


class YoloDetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf: float = 0.25):
        from ultralytics import YOLO  # lazy import: heavy dependency
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, image: Image.Image) -> List[Dict[str, Any]]:
        results = self.model.predict(image, conf=self.conf, verbose=False)
        out: List[Dict[str, Any]] = []
        for r in results:
            names = r.names
            for box in r.boxes:
                out.append({
                    "label": names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": [float(v) for v in box.xyxy[0].tolist()],
                })
        return out


class PipelineError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------
class SeverityPipeline:
    def __init__(self, detector: Optional[Detector] = None,
                 model_path: str = "yolov8n.pt", conf: float = 0.25,
                 severity_fn=None, tau_det: float = TAU_DET):
        self._detector = detector
        self._model_path = model_path
        self._conf = conf
        self._severity_fn = severity_fn or calculate_severity
        self._tau_det = tau_det

    @property
    def detector(self) -> Detector:
        if self._detector is None:  # lazy load so import/tests stay light
            self._detector = YoloDetector(self._model_path, self._conf)
        return self._detector

    # ---- image loading / validation ----
    @staticmethod
    def _load_image(source: ImageInput) -> Image.Image:
        if source is None:
            raise PipelineError("EMPTY_IMAGE", "No image provided.")
        try:
            if isinstance(source, (bytes, bytearray)):
                if len(source) == 0:
                    raise PipelineError("EMPTY_IMAGE", "Image data is empty.")
                img = Image.open(io.BytesIO(source))
            else:
                path = os.fspath(source)
                if not os.path.isfile(path):
                    raise PipelineError("FILE_NOT_FOUND", f"File not found: {path}")
                if os.path.getsize(path) == 0:
                    raise PipelineError("EMPTY_IMAGE", "Image file is empty.")
                img = Image.open(path)
            img.load()  # forces full decode -> catches truncated/corrupt files
        except PipelineError:
            raise
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as e:
            raise PipelineError("CORRUPTED_IMAGE", f"Cannot decode image: {e}")
        img = img.convert("RGB")
        if img.width == 0 or img.height == 0:
            raise PipelineError("EMPTY_IMAGE", "Image has zero size.")
        return img

    # ---- bbox -> area ratio ----
    @staticmethod
    def _with_area_ratio(raw: List[Dict[str, Any]], w: int, h: int) -> List[Dict[str, Any]]:
        total = float(w * h)
        out = []
        for d in raw:
            x1, y1, x2, y2 = d["bbox"]
            # clip to image bounds
            x1, x2 = max(0.0, min(x1, w)), max(0.0, min(x2, w))
            y1, y2 = max(0.0, min(y1, h)), max(0.0, min(y2, h))
            area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            out.append({
                "label": d["label"],
                "confidence": round(float(d["confidence"]), 4),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "area_ratio": round(area / total, 4),
                **({"probs": d["probs"]} if d.get("probs") else {}),
            })
        return out

    # ---- main entry ----
    def run(self, source: ImageInput, request_id: Optional[str] = None) -> Dict[str, Any]:
        request_id = request_id or uuid.uuid4().hex[:12]
        t0 = time.perf_counter()
        logger.info("[%s] pipeline start", request_id)
        try:
            img = self._load_image(source)
            logger.info("[%s] image loaded %dx%d", request_id, img.width, img.height)

            raw = self.detector.detect(img)
            detections = self._with_area_ratio(raw, img.width, img.height)
            logger.info("[%s] detection done: %d objects", request_id, len(detections))

            items = [d for d in detections if d["confidence"] >= self._tau_det]
            extras: Dict[str, Any] = {}
            if items:
                inputs = aggregate_detections(items)
                sev = self._severity_fn(inputs["area_ratio"], inputs["waste_class"],
                                        inputs["item_count"])
                score = round(max(SEVERITY_MIN, min(SEVERITY_MAX, float(sev["severity_score"]))), 2)
                level = sev["severity_level"] if sev["severity_level"] in LEVELS else score_to_level(score)
                extras["scoring_inputs"] = inputs
            else:  # never auto-reject a citizen report: flag for a human instead
                score, level = 0.0, "LOW"
                extras["no_waste_detected"] = True
                extras["flag"] = "no waste detected - operator review"

            elapsed = round((time.perf_counter() - t0) * 1000, 1)
            logger.info("[%s] severity=%.2f level=%s (%.1f ms)", request_id, score, level, elapsed)
            return {
                **extras,
                "status": "success",
                "request_id": request_id,
                "severity_score": score,
                "severity_level": level,
                "detection_count": len(detections),
                "detections": detections,
                "image": {"width": img.width, "height": img.height},
                "processing_ms": elapsed,
            }
        except PipelineError as e:
            logger.warning("[%s] pipeline error %s: %s", request_id, e.code, e.message)
            return self._error(request_id, e.code, e.message, t0)
        except Exception as e:  # never crash the inference service
            logger.exception("[%s] unexpected failure", request_id)
            return self._error(request_id, "INTERNAL_ERROR", str(e), t0)

    @staticmethod
    def _error(request_id: str, code: str, message: str, t0: float) -> Dict[str, Any]:
        return {
            "status": "error",
            "request_id": request_id,
            "error": {"code": code, "message": message},
            "processing_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
