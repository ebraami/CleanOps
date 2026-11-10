"""End-to-end tests: image -> detections -> severity score/level (run with: pytest ai/tests -v)."""
import io
import logging

import pytest
from PIL import Image

from ai.inference.pipeline import LEVELS, SeverityPipeline, map_label_to_class, score_to_level
from ai.inference.severity_calculator import calculate_severity

W, H = 640, 480


class FakeDetector:
    """Stands in for YOLO so tests run without model weights."""
    def __init__(self, boxes):
        self.boxes = boxes  # a bbox list, or a full detection dict

    def detect(self, image):
        return [b if isinstance(b, dict) else
                {"label": "plastic", "confidence": 0.9, "bbox": b} for b in self.boxes]


def street_image_bytes(fmt="JPEG"):
    img = Image.new("RGB", (W, H), (90, 90, 90))  # synthetic "street" image
    buf = io.BytesIO()
    img.save(buf, fmt)
    return buf.getvalue()


def make(boxes):
    return SeverityPipeline(detector=FakeDetector(boxes))


def test_clean_street_is_low():
    r = make([]).run(street_image_bytes())
    assert r["status"] == "success"
    assert r["severity_score"] == 0.0 and r["severity_level"] == "LOW"
    assert r["detection_count"] == 0


def test_small_waste_is_low_or_medium():
    r = make([[10, 10, 60, 60]]).run(street_image_bytes())
    assert r["severity_level"] in ("LOW", "MEDIUM")  # plastic, tiny area, 1 item -> ~2.0


def test_large_waste_is_high_or_critical():
    boxes = [[0, 0, 400, 300], [200, 100, 640, 480], [50, 50, 350, 400]]
    r = make(boxes).run(street_image_bytes())
    assert r["severity_level"] in ("MEDIUM", "HIGH", "CRITICAL")  # plastic: capped area+count


def test_more_waste_never_lowers_score():
    small = make([[0, 0, 100, 100]]).run(street_image_bytes())
    big = make([[0, 0, 100, 100], [0, 0, 300, 300]]).run(street_image_bytes())
    assert big["severity_score"] >= small["severity_score"]


def test_score_always_in_range_even_with_huge_boxes():
    boxes = [[-100, -100, 5000, 5000]] * 20  # out-of-bounds boxes are clipped
    r = make(boxes).run(street_image_bytes())
    assert 0.0 <= r["severity_score"] <= 10.0
    assert all(0.0 <= d["area_ratio"] <= 1.0 for d in r["detections"])
    assert r["severity_score"] <= 10.0


def test_area_ratio_is_correct():
    r = make([[0, 0, 320, 240]]).run(street_image_bytes())  # quarter of image
    assert r["detections"][0]["area_ratio"] == pytest.approx(0.25, abs=1e-3)


def test_response_format():
    r = make([[0, 0, 100, 100]]).run(street_image_bytes(), request_id="abc123")
    for key in ("status", "request_id", "severity_score", "severity_level",
                "detection_count", "detections", "image", "processing_ms"):
        assert key in r
    assert r["request_id"] == "abc123"
    assert r["severity_level"] in LEVELS
    assert r["image"] == {"width": W, "height": H}
    assert set(r["detections"][0]) == {"label", "confidence", "bbox", "area_ratio"}
    assert set(r["scoring_inputs"]) == {"area_ratio", "waste_class", "item_count"}


@pytest.mark.parametrize("fmt", ["JPEG", "PNG"])
def test_supported_formats(fmt):
    assert make([]).run(street_image_bytes(fmt))["status"] == "success"


def test_empty_bytes_error():
    r = make([]).run(b"")
    assert r["status"] == "error" and r["error"]["code"] == "EMPTY_IMAGE"


def test_none_error():
    assert make([]).run(None)["error"]["code"] == "EMPTY_IMAGE"


def test_corrupted_bytes_error():
    r = make([]).run(b"this is definitely not an image")
    assert r["status"] == "error" and r["error"]["code"] == "CORRUPTED_IMAGE"


def test_truncated_image_error():
    data = street_image_bytes("PNG")
    r = make([]).run(data[: len(data) // 2])
    assert r["error"]["code"] == "CORRUPTED_IMAGE"


def test_missing_file_error():
    assert make([]).run("/no/such/file.jpg")["error"]["code"] == "FILE_NOT_FOUND"


def test_empty_file_error(tmp_path):
    p = tmp_path / "empty.jpg"
    p.write_bytes(b"")
    assert make([]).run(str(p))["error"]["code"] == "EMPTY_IMAGE"


def test_reads_from_file_path(tmp_path):
    p = tmp_path / "street.jpg"
    p.write_bytes(street_image_bytes())
    assert make([[0, 0, 100, 100]]).run(p)["status"] == "success"


def test_detector_crash_returns_error_not_exception():
    class Boom:
        def detect(self, image):
            raise RuntimeError("model exploded")
    r = SeverityPipeline(detector=Boom()).run(street_image_bytes())
    assert r["status"] == "error" and r["error"]["code"] == "INTERNAL_ERROR"


def test_execution_logging(caplog):
    with caplog.at_level(logging.INFO, logger="cleanstreet.pipeline"):
        make([[0, 0, 100, 100]]).run(street_image_bytes(), request_id="log1")
    text = caplog.text
    assert "[log1] pipeline start" in text
    assert "detection done" in text and "severity=" in text


def test_error_is_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="cleanstreet.pipeline"):
        make([]).run(b"", request_id="log2")
    assert "[log2]" in caplog.text and "EMPTY_IMAGE" in caplog.text


@pytest.mark.parametrize("score,level", [(0, "LOW"), (2.4, "LOW"), (2.5, "MEDIUM"),
                                         (4.9, "MEDIUM"), (5.0, "HIGH"),
                                         (7.4, "HIGH"), (7.5, "CRITICAL"), (10, "CRITICAL")])
def test_level_boundaries(score, level):
    assert score_to_level(score) == level


def test_pipeline_matches_calculator_for_aggregated_inputs():
    """3 plastic boxes of 0.25 image-area each -> area 0.75, class plastic, count 3."""
    boxes = [[0, 0, 320, 240]] * 3
    r = make(boxes).run(street_image_bytes())
    assert r["scoring_inputs"] == {"area_ratio": 0.75, "waste_class": "plastic", "item_count": 3}
    expected = calculate_severity(0.75, "plastic", 3)
    assert r["severity_score"] == expected["severity_score"]
    assert r["severity_level"] == expected["severity_level"]


def test_most_hazardous_class_drives_score():
    dets = [{"label": "Bottle", "confidence": 0.9, "bbox": [0, 0, 100, 100]},
            {"label": "Battery", "confidence": 0.8, "bbox": [0, 0, 50, 50]}]
    assert make(dets).run(street_image_bytes())["scoring_inputs"]["waste_class"] == "battery"


@pytest.mark.parametrize("label,cls", [("Bottle", "plastic"), ("Broken glass", "glass"),
                                       ("Can", "metal"), ("Carton", "paper"),
                                       ("Cigarette", "other"), ("Food waste", "organic")])
def test_label_mapping(label, cls):
    assert map_label_to_class(label) == cls


def test_low_confidence_detections_ignored():
    r = make([{"label": "plastic", "confidence": 0.3, "bbox": [0, 0, 600, 400]}]).run(street_image_bytes())
    assert r["severity_score"] == 0.0 and r["no_waste_detected"] is True


def test_no_detection_flagged_for_operator_review():
    r = make([]).run(street_image_bytes())
    assert r["no_waste_detected"] is True and "operator review" in r["flag"]


def test_battery_raises_severity():
    base = make([[0, 0, 100, 100]]).run(street_image_bytes())
    bat = make([{"label": "battery", "confidence": 0.9, "bbox": [0, 0, 100, 100]}]).run(street_image_bytes())
    assert bat["severity_score"] > base["severity_score"]
