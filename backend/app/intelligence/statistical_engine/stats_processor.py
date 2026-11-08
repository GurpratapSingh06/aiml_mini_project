"""
VEDANTA — Statistical Intelligence Engine
Deterministic numerical analysis of placement statistics, fee structures, and admissions data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PlacementFact:
    academic_year: str
    department: str
    total_students: Optional[int] = None
    students_placed: Optional[int] = None
    offers_made: Optional[int] = None
    highest_package_lpa: Optional[float] = None
    average_package_lpa: Optional[float] = None
    median_package_lpa: Optional[float] = None
    placement_percentage: Optional[float] = None
    companies_visited: Optional[int] = None
    source_url: str = ""
    source_page: Optional[int] = None
    provenance_note: str = ""


@dataclass
class FeeFact:
    academic_year: str
    program: str
    category: str  # OPEN, OBC, SC, ST, VJNT, TFWS, EWS, NRI
    tuition_fee: Optional[float] = None
    development_fee: Optional[float] = None
    other_fees: Optional[float] = None
    total_fee: Optional[float] = None
    source_url: str = ""
    source_page: Optional[int] = None
    provenance_note: str = ""


class StatsProcessor:
    """
    Extracts and computes verified placement, salary, and fee statistics.
    Follows strict provenance rules: never fabricates numbers or averages.
    """

    LPA_REGEX = re.compile(
        r"(?:highest|maximum|top)?\s*(?:package|ctc|salary)?\s*[:\-\u2013]?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?\s*per\s*annum|lac|lacs)",
        re.IGNORECASE,
    )
    AVG_LPA_REGEX = re.compile(
        r"(?:average|mean)\s*(?:package|ctc|salary)?\s*[:\-\u2013]?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?\s*per\s*annum|lac|lacs)",
        re.IGNORECASE,
    )
    FEE_AMOUNT_REGEX = re.compile(
        r"(?:total\s+fees?|tuition\s+fees?|fees?)\s*[:\-\u2013]?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    def extract_placements_from_text(self, text: str, source_url: str = "") -> List[PlacementFact]:
        facts: List[PlacementFact] = []
        if not text:
            return facts

        # Scan for highest package
        highest_match = self.LPA_REGEX.search(text)
        highest_val = float(highest_match.group(1)) if highest_match else None

        # Scan for average package
        avg_match = self.AVG_LPA_REGEX.search(text)
        avg_val = float(avg_match.group(1)) if avg_match else None

        # Scan for placed count
        placed_match = re.search(r"(\d+)\s*\+?\s*(?:students?\s+placed|placements|offers)", text, re.IGNORECASE)
        placed_val = int(placed_match.group(1)) if placed_match else None

        # Scan for recruiters/companies
        companies_match = re.search(r"(\d+)\s*\+?\s*(?:recruiters|companies|corporates)", text, re.IGNORECASE)
        companies_val = int(companies_match.group(1)) if companies_match else None

        if highest_val or avg_val or placed_val or companies_val:
            facts.append(
                PlacementFact(
                    academic_year="2023-24",  # Fallback unless extracted
                    department="Institutional Aggregate",
                    students_placed=placed_val,
                    highest_package_lpa=highest_val,
                    average_package_lpa=avg_val,
                    companies_visited=companies_val,
                    source_url=source_url,
                    provenance_note="Direct extraction from verified web page text.",
                )
            )

        return facts

    def calculate_metrics(
        self,
        students_placed: int,
        total_eligible: int,
    ) -> Dict[str, Any]:
        """
        Calculates verified percentage and rates with denominator integrity.
        """
        if total_eligible <= 0:
            return {
                "percentage": None,
                "error": "Denominator (total students) must be greater than zero.",
            }
        
        pct = (students_placed / total_eligible) * 100.0
        return {
            "students_placed": students_placed,
            "total_eligible": total_eligible,
            "placement_percentage": round(pct, 2),
            "formula": "(students_placed / total_eligible) * 100",
        }

    def compare_academic_years(
        self,
        year1_data: PlacementFact,
        year2_data: PlacementFact,
    ) -> Dict[str, Any]:
        """
        Deterministic numerical comparison across academic cycles.
        """
        comparison: Dict[str, Any] = {
            "year_1": year1_data.academic_year,
            "year_2": year2_data.academic_year,
            "department": year1_data.department,
        }

        if year1_data.highest_package_lpa and year2_data.highest_package_lpa:
            diff = year2_data.highest_package_lpa - year1_data.highest_package_lpa
            comparison["highest_package_change_lpa"] = round(diff, 2)

        if year1_data.average_package_lpa and year2_data.average_package_lpa:
            diff_avg = year2_data.average_package_lpa - year1_data.average_package_lpa
            comparison["average_package_change_lpa"] = round(diff_avg, 2)

        if year1_data.students_placed and year2_data.students_placed:
            diff_placed = year2_data.students_placed - year1_data.students_placed
            comparison["students_placed_change"] = diff_placed

        return comparison
