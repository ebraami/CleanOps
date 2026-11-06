"""
Unit tests for ai/inference/severity_calculator.py

Run from the repository root:
    pytest ai/tests/test_severity.py
"""

import sys
from pathlib import Path

import pytest

# Make the repository root importable so `ai.inference...` resolves no matter how pytest is launched.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ai.inference.severity_calculator import HAZARD_WEIGHTS, calculate_severity  # noqa: E402


# --------------------------------------------------------------------------------------
# Required scenarios from the task
# --------------------------------------------------------------------------------------
def test_battery_is_critical():
    result = calculate_severity(0.6, "battery", 5)
    assert result["severity_score"] == pytest.approx(8.0)
    assert result["severity_level"] == "CRITICAL"


def test_battery_single_large_item_is_critical():
    result = calculate_severity(1.0, "battery", 1)
    assert result["severity_score"] == pytest.approx(8.4)
    assert result["severity_level"] == "CRITICAL"


def test_paper_is_low():
    result = calculate_severity(0.05, "paper", 1)
    assert result["severity_score"] == pytest.approx(1.25)
    assert result["severity_level"] == "LOW"


# --------------------------------------------------------------------------------------
# Output shape
# --------------------------------------------------------------------------------------
def test_result_has_exactly_the_expected_keys_and_types():
    result = calculate_severity(0.3, "plastic", 2)
    assert set(result) == {"severity_score", "severity_level"}
    assert isinstance(result["severity_score"], float)
    assert result["severity_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_hazard_weights_match_specification():
    assert HAZARD_WEIGHTS == {
        "battery": 1.0, "glass": 0.8, "organic": 0.6,
        "metal": 0.5, "plastic": 0.4, "paper": 0.2,
    }


# --------------------------------------------------------------------------------------
# Formula values: (area ratio, class, item count, expected score, expected level)
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "ratio, waste_class, count, expected_score, expected_level",
    [
        (0.0, "paper", 1, 1.00, "LOW"),
        (0.1, "battery", 1, 3.90, "MEDIUM"),
        (0.2, "glass", 1, 3.80, "MEDIUM"),
        (0.5, "glass", 5, 6.90, "HIGH"),
        (0.6, "plastic", 1, 4.60, "MEDIUM"),
        (1.0, "battery", 5, 10.00, "CRITICAL"),
        (0.1, "organic", 1, 2.70, "MEDIUM"),
        (0.3, "metal", 3, 4.20, "MEDIUM"),
    ],
)
def test_formula_values(ratio, waste_class, count, expected_score, expected_level):
    result = calculate_severity(ratio, waste_class, count)
    assert result["severity_score"] == pytest.approx(expected_score)
    assert result["severity_level"] == expected_level


# --------------------------------------------------------------------------------------
# Level boundaries (>= is inclusive at each threshold)
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "ratio, waste_class, count, expected_score, expected_level",
    [
        (0.17, "plastic", 1, 2.45, "LOW"),       # just below 2.5
        (0.18, "plastic", 1, 2.50, "MEDIUM"),    # exactly 2.5
        (0.678, "plastic", 1, 4.99, "MEDIUM"),   # just below 5.0
        (0.68, "plastic", 1, 5.00, "HIGH"),      # exactly 5.0
        (0.498, "battery", 5, 7.49, "HIGH"),     # just below 7.5
        (0.5, "battery", 5, 7.50, "CRITICAL"),   # exactly 7.5
    ],
)
def test_level_boundaries(ratio, waste_class, count, expected_score, expected_level):
    result = calculate_severity(ratio, waste_class, count)
    assert result["severity_score"] == pytest.approx(expected_score)
    assert result["severity_level"] == expected_level


# --------------------------------------------------------------------------------------
# Hazard ordering
# --------------------------------------------------------------------------------------
def test_more_hazardous_classes_score_higher_for_same_inputs():
    order = ["battery", "glass", "organic", "metal", "plastic", "paper"]
    scores = [calculate_severity(0.2, c, 2)["severity_score"] for c in order]
    assert scores == sorted(scores, reverse=True)
    assert len(set(scores)) == len(scores)  # every class gives a distinct score


# --------------------------------------------------------------------------------------
# Class handling
# --------------------------------------------------------------------------------------
def test_waste_class_is_case_insensitive():
    assert calculate_severity(0.4, "BATTERY", 2) == calculate_severity(0.4, "battery", 2)
    assert calculate_severity(0.4, "Glass", 2) == calculate_severity(0.4, "glass", 2)


def test_unknown_class_uses_default_hazard_of_0_3():
    # 0.1*5 + 0.3*3 + 1*0.4 = 1.80
    result = calculate_severity(0.1, "something-else", 1)
    assert result["severity_score"] == pytest.approx(1.80)
    assert result["severity_level"] == "LOW"


# --------------------------------------------------------------------------------------
# Item count handling
# --------------------------------------------------------------------------------------
def test_item_count_defaults_to_one():
    assert calculate_severity(0.2, "metal") == calculate_severity(0.2, "metal", 1)


def test_item_count_is_capped_at_five():
    assert calculate_severity(0.2, "metal", 5) == calculate_severity(0.2, "metal", 50)


def test_more_items_increase_score_up_to_the_cap():
    s1 = calculate_severity(0.2, "metal", 1)["severity_score"]
    s3 = calculate_severity(0.2, "metal", 3)["severity_score"]
    s5 = calculate_severity(0.2, "metal", 5)["severity_score"]
    assert s1 < s3 < s5


# --------------------------------------------------------------------------------------
# Clamping and rounding
# --------------------------------------------------------------------------------------
def test_score_is_clamped_to_ten():
    result = calculate_severity(2.0, "battery", 99)
    assert result["severity_score"] == 10.0
    assert result["severity_level"] == "CRITICAL"


def test_score_is_clamped_to_zero():
    result = calculate_severity(-5.0, "paper", 0)
    assert result["severity_score"] == 0.0
    assert result["severity_level"] == "LOW"


def test_score_is_rounded_to_two_decimals():
    result = calculate_severity(0.123456, "plastic", 1)
    assert result["severity_score"] == round(result["severity_score"], 2)
