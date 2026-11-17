"""
VEDANTA — Statistical Store Data Access Layer
Queries PostgreSQL for structured placement statistics and approved fee records.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

async def get_placement_records(
    department: Optional[str] = None,
    academic_year: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve structured placement statistics.
    Joins placement_records with departments.
    """
    async with AsyncSessionLocal() as session:
        query = """
            SELECT 
                d.name as department,
                p.academic_year,
                p.total_students,
                p.students_placed,
                p.highest_package_lpa,
                p.average_package_lpa,
                p.source_url,
                p.record_type,
                p.package_distribution,
                p.companies_visited,
                p.offers_made
            FROM placement_records p
            LEFT JOIN departments d ON p.department_id = d.id
            WHERE 1=1
        """
        params = {}
        if department:
            query += " AND (d.name ILIKE :dept OR d.abbreviation ILIKE :dept OR d.short_name ILIKE :dept)"
            params["dept"] = f"%{department}%"
        if academic_year:
            query += " AND p.academic_year = :ay"
            params["ay"] = academic_year

        query += " ORDER BY p.highest_package_lpa DESC NULLS LAST"

        res = await session.execute(text(query), params)
        rows = res.fetchall()

        results = []
        for r in rows:
            results.append({
                "department": r[0] or "Institutional Aggregate",
                "academic_year": r[1],
                "total_students": r[2],
                "students_placed": r[3],
                "highest_package_lpa": r[4],
                "average_package_lpa": r[5],
                "source_url": r[6],
                "record_type": r[7],
                "package_distribution": r[8],
                "companies_visited": r[9],
                "offers_made": r[10],
            })
        return results

async def get_fee_records(
    department: Optional[str] = None,
    academic_year: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve structured fee schedule records.
    """
    async with AsyncSessionLocal() as session:
        query = """
            SELECT 
                d.name as department,
                f.academic_year,
                f.admission_category,
                f.fee_type,
                f.amount_inr,
                f.additional_charges,
                f.source_url
            FROM fee_records f
            LEFT JOIN departments d ON f.department_id = d.id
            WHERE 1=1
        """
        params = {}
        if department:
            query += " AND (d.name ILIKE :dept OR d.abbreviation ILIKE :dept)"
            params["dept"] = f"%{department}%"
        if academic_year:
            query += " AND f.academic_year = :ay"
            params["ay"] = academic_year
        if category:
            query += " AND f.admission_category ILIKE :cat"
            params["cat"] = f"%{category}%"

        query += " ORDER BY f.amount_inr DESC NULLS LAST"

        res = await session.execute(text(query), params)
        rows = res.fetchall()

        results = []
        for r in rows:
            results.append({
                "department": r[0] or "First Year B.Tech (All Branches)",
                "academic_year": r[1],
                "category": r[2],
                "fee_type": r[3],
                "total_amount_inr": r[4],
                "additional_charges": r[5],
                "source_url": r[6],
            })
        return results
