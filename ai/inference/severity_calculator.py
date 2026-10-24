"""
severity_calculator.py - standalone severity calculation for CleanStreet AI.

Combines how much of the photo the waste covers, how hazardous the material is, and how
many items were detected into a single 0-10 severity score and a named level.

    score = (bbox_area_ratio * 5.0) + (hazard * 3.0) + (min(item_count, 5) * 0.4)

The score is rounded to 2 decimals and clamped to [0, 10].

Levels:  >= 7.5 CRITICAL | >= 5.0 HIGH | >= 2.5 MEDIUM | otherwise LOW

This module has no dependencies outside the Python standard library.
"""

HAZARD_WEIGHTS = {
    'battery': 1.0,
    'glass': 0.8,
    'organic': 0.6,
    'metal': 0.5,
    'plastic': 0.4,
    'paper': 0.2
}


def calculate_severity(bbox_area_ratio: float, waste_class: str, item_count: int = 1) -> dict:
    """Return {"severity_score": float, "severity_level": str}.

    bbox_area_ratio -- fraction of the image covered by the waste (expected 0.0 - 1.0)
    waste_class     -- material class name (case-insensitive); unknown classes use hazard 0.3
    item_count      -- number of detected items; counts above 5 are treated as 5
    """
    hazard = HAZARD_WEIGHTS.get(waste_class.lower(), 0.3)
    score = (bbox_area_ratio * 5.0) + (hazard * 3.0) + (min(item_count, 5) * 0.4)
    score = min(max(round(score, 2), 0.0), 10.0)

    if score >= 7.5:
        level = "CRITICAL"
    elif score >= 5.0:
        level = "HIGH"
    elif score >= 2.5:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"severity_score": score, "severity_level": level}
