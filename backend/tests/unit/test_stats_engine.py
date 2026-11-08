"""
VEDANTA Unit Tests — Statistical Engine and Arithmetic Provenance
"""

import pytest
from app.intelligence.statistical_engine.stats_processor import (
    StatsProcessor,
    PlacementFact,
)


def test_placement_percentage_deterministic_calculation():
    processor = StatsProcessor()
    res = processor.calculate_metrics(students_placed=182, total_eligible=206)
    assert res["placement_percentage"] == 88.35
    assert res["formula"] == "(students_placed / total_eligible) * 100"


def test_zero_denominator_handled():
    processor = StatsProcessor()
    res = processor.calculate_metrics(students_placed=10, total_eligible=0)
    assert res["percentage"] is None
    assert "greater than zero" in res["error"]


def test_year_over_year_comparison():
    processor = StatsProcessor()
    y1 = PlacementFact(
        academic_year="2022-23",
        department="Computer Engineering",
        highest_package_lpa=21.0,
        average_package_lpa=6.2,
        students_placed=160,
    )
    y2 = PlacementFact(
        academic_year="2023-24",
        department="Computer Engineering",
        highest_package_lpa=24.5,
        average_package_lpa=6.8,
        students_placed=182,
    )
    comp = processor.compare_academic_years(y1, y2)
    assert comp["highest_package_change_lpa"] == 3.5
    assert comp["average_package_change_lpa"] == 0.6
    assert comp["students_placed_change"] == 22
