"""CleanOps - FastAPI waste detection inference service (YOLOv8).

Run (from the repository root):
    pip install -r ai/inference/requirements.txt
    uvicorn app:app --app-dir ai/inference --host 0.0.0.0 --port 8000
    # interactive docs: http://localhost:8000/docs

Endpoints
    GET  /health           liveness + model status (200 when the model is loaded, 503 otherwise)
    POST /api/v1/detect    multipart/form-data, field "file" = JPEG / PNG / WebP image

Configuration (environment variables, all optional)
    MODEL_PATH            trained weights                       (default: ai/models/yolov8n_cleanops_best.pt)
    CONF_THRESHOLD        detection confidence cut-off          (default: 0.25)
    CONFIDENT_THRESHOLD   boxes below this get `low_det_conf`   (default: 0.50)
    IOU_THRESHOLD         NMS IoU threshold                     (default: 0.70)
    MAX_DET               maximum detections per image          (default: 100)
    IMGSZ                 inference image size                  (default: 640)
    MAX_UPLOAD_MB         maximum upload size in MB             (default: 10)
    MAX_IMAGE_PIXELS      maximum decoded image size in pixels  (default: 50000000)

The defaults follow docs/design/ai/yolov8-detection-spec.md (conf 0.25, NMS IoU 0.70, max_det 100, imgsz 640).
"""
from __future__ import annotations

import io
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Optional

import numpy as np
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("cleanops.inference")

API_VERSION = "1.0.0"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "yolov8n_cleanops_best.pt"


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Settings:
    model_path: Path = DEFAULT_MODEL_PATH
    conf_threshold: float = 0.25
    confident_threshold: float = 0.50
    iou_threshold: float = 0.70
    max_det: int = 100
    imgsz: int = 640
    max_upload_mb: float = 10.0
    max_image_pixels: int = 50_000_000

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        d = cls()
        return cls(
            model_path=Path(env.get("MODEL_PATH", str(d.model_path))),
            conf_threshold=float(env.get("CONF_THRESHOLD", d.conf_threshold)),
            confident_threshold=float(env.get("CONFIDENT_THRESHOLD", d.confident_threshold)),
            iou_threshold=float(env.get("IOU_THRESHOLD", d.iou_threshold)),
            max_det=int(env.get("MAX_DET", d.max_det)),
            imgsz=int(env.get("IMGSZ", d.imgsz)),
            max_upload_mb=float(env.get("MAX_UPLOAD_MB", d.max_upload_mb)),
            max_image_pixels=int(env.get("MAX_IMAGE_PIXELS", d.max_image_pixels)),
        )


# --------------------------------------------------------------------------- #
# Response schema
# --------------------------------------------------------------------------- #
class ImageInfo(BaseModel):
    width: int = Field(description="Width in pixels after EXIF orientation correction")
    height: int = Field(description="Height in pixels after EXIF orientation correction")


class BBox(BaseModel):
    """Corner coordinates in pixels of the (EXIF-corrected) uploaded image."""
    x1: float
    y1: float
    x2: float
    y2: float


class BBoxNormalized(BaseModel):
    """YOLO-style box, every value normalised to 0-1 by the image width / height."""
    x_center: float
    y_center: float
    width: float
    height: float


class Detection(BaseModel):
    id: int = Field(description="1-based rank, highest confidence first")
    class_id: int
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bbox: BBox
    bbox_normalized: BBoxNormalized
    area_px: float = Field(description="Box area in pixels")
    coverage_ratio: float = Field(ge=0, le=1, description="Box area / image area")
    flags: list[Literal["low_det_conf"]] = Field(
        default_factory=list, description="`low_det_conf`: confidence is below CONFIDENT_THRESHOLD")


class Summary(BaseModel):
    detection_count: int
    total_coverage_ratio: float = Field(
        ge=0, le=1, description="Share of the image covered by the UNION of all boxes (overlaps counted once)")
    class_counts: dict[str, int]


class ModelInfo(BaseModel):
    name: str
    conf_threshold: float
    iou_threshold: float
    max_det: int
    imgsz: int


class DetectResponse(BaseModel):
    image: ImageInfo
    model: ModelInfo
    detections: list[Detection]
    summary: Summary
    report_flags: list[Literal["no_waste_detected", "dense_scene"]] = Field(
        default_factory=list,
        description="`no_waste_detected`: no box reached the confidence cut-off. "
                    "`dense_scene`: the max_det cap was reached, so more objects may exist.")
    inference_ms: float


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_file: str
    classes: list[str] = Field(default_factory=list)
    api_version: str = API_VERSION
    detail: Optional[str] = None


# --------------------------------------------------------------------------- #
# Image decoding and geometry helpers
# --------------------------------------------------------------------------- #
class ImageDecodeError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def decode_image(data: bytes, max_pixels: int) -> Image.Image:
    """Decode uploaded bytes into an RGB image with the EXIF orientation applied.

    Raises ImageDecodeError (400 corrupt / not an image, 413 too many pixels)."""
    try:
        img = Image.open(io.BytesIO(data))
        if img.width * img.height > max_pixels:
            raise ImageDecodeError(413, f"Image is too large ({img.width}x{img.height}); limit is {max_pixels} pixels")
        img = ImageOps.exif_transpose(img)  # phone photos are often stored rotated + an EXIF flag
        return img.convert("RGB")
    except ImageDecodeError:
        raise
    except Exception as exc:  # unreadable, truncated, not an image, decompression bomb ...
        raise ImageDecodeError(400, "The uploaded file is not a valid image") from exc


def _to_numpy(x: Any) -> np.ndarray:
    return x.cpu().numpy() if hasattr(x, "cpu") else np.asarray(x)


def union_area(boxes_xyxy: np.ndarray) -> float:
    """Exact area of the union of axis-aligned boxes (overlaps counted once)."""
    boxes = np.asarray(boxes_xyxy, dtype=float).reshape(-1, 4)
    if boxes.shape[0] == 0:
        return 0.0
    xs = np.unique(boxes[:, [0, 2]])
    ys = np.unique(boxes[:, [1, 3]])
    if len(xs) < 2 or len(ys) < 2:
        return 0.0
    covered = np.zeros((len(ys) - 1, len(xs) - 1), dtype=bool)
    xi = np.searchsorted(xs, boxes[:, [0, 2]])
    yi = np.searchsorted(ys, boxes[:, [1, 3]])
    for (x0, x1), (y0, y1) in zip(xi, yi):
        covered[y0:y1, x0:x1] = True
    cell_area = np.outer(np.diff(ys), np.diff(xs))
    return float(cell_area[covered].sum())


def build_response(result: Any, image_size: tuple[int, int], settings: Settings, inference_ms: float) -> DetectResponse:
    """Turn one Ultralytics Results object into the API response."""
    width, height = image_size
    image_area = float(width * height)

    boxes = result.boxes
    xyxy = _to_numpy(boxes.xyxy).astype(float).reshape(-1, 4)
    conf = _to_numpy(boxes.conf).astype(float).reshape(-1)
    cls = _to_numpy(boxes.cls).astype(int).reshape(-1)
    names = result.names

    order = np.argsort(-conf, kind="stable")          # highest confidence first
    xyxy, conf, cls = xyxy[order], conf[order], cls[order]
    xyxy[:, [0, 2]] = np.clip(xyxy[:, [0, 2]], 0, width)
    xyxy[:, [1, 3]] = np.clip(xyxy[:, [1, 3]], 0, height)

    detections: list[Detection] = []
    class_counts: dict[str, int] = {}
    for i, ((x1, y1, x2, y2), c, k) in enumerate(zip(xyxy, conf, cls), start=1):
        bw, bh = x2 - x1, y2 - y1
        area = bw * bh
        name = str(names[int(k)])
        class_counts[name] = class_counts.get(name, 0) + 1
        detections.append(Detection(
            id=i,
            class_id=int(k),
            class_name=name,
            confidence=round(float(min(max(c, 0.0), 1.0)), 4),
            bbox=BBox(x1=round(float(x1), 2), y1=round(float(y1), 2), x2=round(float(x2), 2), y2=round(float(y2), 2)),
            bbox_normalized=BBoxNormalized(
                x_center=round(float((x1 + x2) / 2 / width), 6), y_center=round(float((y1 + y2) / 2 / height), 6),
                width=round(float(bw / width), 6), height=round(float(bh / height), 6)),
            area_px=round(float(area), 2),
            coverage_ratio=round(float(area / image_area), 6),
            flags=["low_det_conf"] if c < settings.confident_threshold else [],
        ))

    report_flags: list[str] = []
    if not detections:
        report_flags.append("no_waste_detected")
    if len(detections) >= settings.max_det:
        report_flags.append("dense_scene")

    return DetectResponse(
        image=ImageInfo(width=width, height=height),
        model=ModelInfo(name=settings.model_path.stem, conf_threshold=settings.conf_threshold,
                        iou_threshold=settings.iou_threshold, max_det=settings.max_det, imgsz=settings.imgsz),
        detections=detections,
        summary=Summary(detection_count=len(detections),
                        total_coverage_ratio=round(min(union_area(xyxy) / image_area, 1.0), 6),
                        class_counts=class_counts),
        report_flags=report_flags,
        inference_ms=round(inference_ms, 1),
    )


# --------------------------------------------------------------------------- #
# Application factory
# --------------------------------------------------------------------------- #
ModelLoader = Callable[[Path], Any]


def default_model_loader(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"Model weights not found: {path}")
    from ultralytics import YOLO  # imported lazily: heavy import, and not needed by the unit tests
    return YOLO(str(path))


def _class_names(model: Any) -> list[str]:
    names = getattr(model, "names", None) or {}
    return [str(v) for v in (names.values() if isinstance(names, dict) else names)]


def create_app(settings: Optional[Settings] = None, model_loader: ModelLoader = default_model_loader) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.model = None
        app.state.model_error = None
        app.state.lock = threading.Lock()  # one inference at a time: Ultralytics models are not thread-safe
        try:
            app.state.model = model_loader(settings.model_path)
            try:  # warm-up so the first real request is not slow (best effort)
                app.state.model.predict(source=Image.new("RGB", (64, 64)), imgsz=settings.imgsz, verbose=False)
            except Exception:
                logger.warning("Model warm-up failed (continuing)", exc_info=True)
            logger.info("Model loaded: %s", settings.model_path.name)
        except Exception as exc:
            app.state.model_error = f"{type(exc).__name__}: {exc}"
            logger.error("Could not load the model: %s", app.state.model_error)
        yield
        app.state.model = None

    app = FastAPI(
        title="CleanOps Waste Detection Inference Service",
        description="YOLOv8 waste detection for CleanStreet AI. Upload a street photo, get bounding boxes, "
                    "classes, confidences and image-coverage ratios as JSON.",
        version=API_VERSION,
        lifespan=lifespan,
    )

    @app.get("/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}}, tags=["health"])
    def health(request: Request):
        state = request.app.state
        if state.model is None:
            body = HealthResponse(status="degraded", model_loaded=False, model_file=settings.model_path.name,
                                  detail=state.model_error or "Model not loaded")
            return JSONResponse(status_code=503, content=body.model_dump())
        return HealthResponse(status="ok", model_loaded=True, model_file=settings.model_path.name,
                              classes=_class_names(state.model))

    @app.post(
        "/api/v1/detect",
        response_model=DetectResponse,
        tags=["detection"],
        summary="Detect waste in an uploaded image",
        responses={
            400: {"description": "Empty file, or not a valid / readable image"},
            413: {"description": "File or image too large"},
            415: {"description": "Content type is not an image"},
            422: {"description": "Missing `file` form field"},
            500: {"description": "Inference failed"},
            503: {"description": "Model is not loaded"},
        },
    )
    def detect(request: Request, file: UploadFile = File(..., description="JPEG / PNG / WebP street photo")):
        state = request.app.state
        if state.model is None:
            raise HTTPException(status_code=503, detail="Model is not loaded")

        content_type = (file.content_type or "").lower()
        if not (content_type.startswith("image/") or content_type == "application/octet-stream"):
            raise HTTPException(status_code=415, detail=f"Unsupported content type '{content_type}'; upload an image")

        limit = int(settings.max_upload_mb * 1024 * 1024)
        data = file.file.read(limit + 1)              # never read more than limit + 1 bytes
        if len(data) > limit:
            raise HTTPException(status_code=413, detail=f"File is larger than {settings.max_upload_mb:g} MB")
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")

        try:
            image = decode_image(data, settings.max_image_pixels)
        except ImageDecodeError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail)

        try:
            with state.lock:
                started = time.perf_counter()
                results = state.model.predict(
                    source=image, conf=settings.conf_threshold, iou=settings.iou_threshold,
                    imgsz=settings.imgsz, max_det=settings.max_det, verbose=False)
                inference_ms = (time.perf_counter() - started) * 1000
            response = build_response(results[0], image.size, settings, inference_ms)
        except Exception:
            logger.exception("Inference failed")
            raise HTTPException(status_code=500, detail="Inference failed")

        logger.info("detect: %dx%d -> %d detections in %.0f ms", image.width, image.height,
                    response.summary.detection_count, inference_ms)
        return response

    return app


app = create_app()
