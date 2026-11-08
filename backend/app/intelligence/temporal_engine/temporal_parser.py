"""
VEDANTA — Temporal Intelligence Engine
Determines the validity period, academic year, and currency of institutional records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class TemporalValidity(str, Enum):
    CURRENT = "current"
    HISTORICAL = "historical"
    UPCOMING = "upcoming"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


@dataclass
class TemporalAssessment:
    academic_year: Optional[str]
    validity_status: TemporalValidity
    publication_date: Optional[datetime]
    effective_date: Optional[datetime]
    confidence: float
    notes: str
    metadata: Dict[str, Any]


class TemporalParser:
    """
    Parses temporal indicators, academic years, and resolves validity periods
    to ensure answers reflect current facts and identify historical records.
    """

    AY_REGEX = re.compile(r"\b(?:AY|A\.Y\.|Academic\s+Year)?\s*(20[12]\d)\s*[-–/]\s*([12]\d|20[12]\d)\b", re.IGNORECASE)
    CALENDAR_YEAR_REGEX = re.compile(r"\b(20[12]\d)\b")
    DATE_PATTERNS = [
        re.compile(r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](20\d{2})\b"),  # DD/MM/YYYY
        re.compile(r"\b(?:dated|date|w\.e\.f\.?)\s*[:\-\u2013]?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+20\d{2})\b", re.IGNORECASE),
    ]

    SUPERSEDED_KEYWORDS = [
        "superseded", "cancelled", "archived", "old", "previous revision",
        "obsolete", "withdrawn", "rescinded"
    ]

    def __init__(self, reference_year: int = 2025):
        self.reference_year = reference_year

    def parse_academic_year(self, text: str) -> Optional[str]:
        """
        Normalize academic years into canonical '2024-25' format.
        """
        match = self.AY_REGEX.search(text)
        if match:
            start_yr, end_yr = match.groups()
            start = int(start_yr)
            # Normalize end year (e.g. '2025' -> '25' or '25' -> '25')
            if len(end_yr) == 4:
                end = int(end_yr) % 100
            else:
                end = int(end_yr)
            
            # Sanity check: end year should be start + 1
            if end == (start + 1) % 100:
                return f"{start}-{end:02d}"
            return f"{start}-{end:02d}"
        return None

    def assess_validity(
        self,
        text: str,
        source_url: str = "",
        document_metadata: Optional[Dict[str, Any]] = None,
    ) -> TemporalAssessment:
        """
        Determine if the content is current, historical, or superseded.
        """
        academic_year = self.parse_academic_year(text) or self.parse_academic_year(source_url)
        
        # Check explicit superseded indicators
        text_lower = text.lower()
        if any(kw in text_lower for kw in self.SUPERSEDED_KEYWORDS):
            return TemporalAssessment(
                academic_year=academic_year,
                validity_status=TemporalValidity.SUPERSEDED,
                publication_date=None,
                effective_date=None,
                confidence=0.88,
                notes="Text contains keywords indicating superseded status.",
                metadata={"source_url": source_url},
            )

        if academic_year:
            try:
                start_year = int(academic_year.split("-")[0])
                if start_year >= self.reference_year:
                    status = TemporalValidity.CURRENT
                    confidence = 0.90
                    notes = f"Academic year {academic_year} aligns with or succeeds current cycle."
                elif start_year == self.reference_year - 1:
                    status = TemporalValidity.CURRENT
                    confidence = 0.82
                    notes = f"Academic year {academic_year} is recent."
                else:
                    status = TemporalValidity.HISTORICAL
                    confidence = 0.88
                    notes = f"Academic year {academic_year} is prior to current active cycle."
            except Exception:
                status = TemporalValidity.UNKNOWN
                confidence = 0.50
                notes = "Could not parse numerical year boundary."
        else:
            # Check calendar years
            years = [int(y) for y in self.CALENDAR_YEAR_REGEX.findall(text)]
            if years:
                latest_year = max(years)
                if latest_year >= self.reference_year:
                    status = TemporalValidity.CURRENT
                    confidence = 0.75
                    notes = f"Contains reference to year {latest_year}."
                else:
                    status = TemporalValidity.HISTORICAL
                    confidence = 0.70
                    notes = f"Latest year mentioned is {latest_year}."
            else:
                status = TemporalValidity.UNKNOWN
                confidence = 0.40
                notes = "No explicit temporal expressions found."

        return TemporalAssessment(
            academic_year=academic_year,
            validity_status=status,
            publication_date=None,
            effective_date=None,
            confidence=confidence,
            notes=notes,
            metadata={"source_url": source_url},
        )
