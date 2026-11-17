"""
VEDANTA — Intelligent Question-Driven Live Page & Entity Fetcher
Autonomous discovery of official MITAOE pages, faculty profiles, and institutional notices.
Zero hardcoding: dynamically discovers any faculty member from official department portals.
"""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.ingestion.parsers.chunker import TextChunker
from app.intelligence.entity_engine.identity_resolver import (
    extract_person_name_from_query,
    matches_identity,
    normalize_name_tokens,
)

logger = get_logger(__name__)

# Official Institutional Landing Portals
DEPARTMENT_PORTALS = [
    ("Computer Engineering", "https://mitaoe.ac.in/department-of-computer-engineering.php"),
    ("Information Technology", "https://mitaoe.ac.in/department-of-information-technology.php"),
    ("Software Engineering", "https://mitaoe.ac.in/department-of-software-engineering.php"),
    ("Artificial Intelligence and Machine Learning", "https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php"),
    ("Data Science", "https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php"),
    ("Mechanical Engineering", "https://mitaoe.ac.in/department-of-mechanical-engineering.php"),
    ("Civil Engineering", "https://mitaoe.ac.in/department-of-civil-engineering.php"),
    ("Chemical Engineering", "https://mitaoe.ac.in/department-of-chemical-engineering.php"),
    ("Electronics and Telecommunication Engineering", "https://mitaoe.ac.in/department-of-electronics-and-telecomminication-engineering.php"),
    ("Electronics and Computer Engineering", "https://mitaoe.ac.in/Department-of-Electronics-and-Computer-Engineering.php"),
    ("Humanities and Engineering Sciences", "https://mitaoe.ac.in/school-of-humanities-and-engineering-sciences-Faculty.php"),
    ("School of Design", "https://mitaoe.ac.in/mitaoe-school-of-design.php"),
    ("Leadership", "https://mitaoe.ac.in/mitaoe-leadership.php"),
]

OFFICIAL_PAGES = {
    "Computer Engineering": "https://mitaoe.ac.in/department-of-computer-engineering.php",
    "Information Technology": "https://mitaoe.ac.in/department-of-information-technology.php",
    "Software Engineering": "https://mitaoe.ac.in/department-of-software-engineering.php",
    "Artificial Intelligence and Machine Learning": "https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php",
    "Data Science": "https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php",
    "Mechanical Engineering": "https://mitaoe.ac.in/department-of-mechanical-engineering.php",
    "Civil Engineering": "https://mitaoe.ac.in/department-of-civil-engineering.php",
    "Chemical Engineering": "https://mitaoe.ac.in/department-of-chemical-engineering.php",
    "Electronics and Telecommunication Engineering": "https://mitaoe.ac.in/department-of-electronics-and-telecomminication-engineering.php",
    "Electronics and Computer Engineering": "https://mitaoe.ac.in/Department-of-Electronics-and-Computer-Engineering.php",
    "Humanities and Engineering Sciences": "https://mitaoe.ac.in/mitaoe-school-of-humanities-and-engineering-sciences.php",
    "School of Design": "https://mitaoe.ac.in/mitaoe-school-of-design.php",
    "Leadership": "https://mitaoe.ac.in/mitaoe-leadership.php",
    "Director Profile": "https://mitaoe.ac.in/mitaoe-director-profile.php",
    "Academic Council": "https://mitaoe.ac.in/mitaoe-academic-council.php",
    "Placement Portal": "https://mitaoe.ac.in/placement.php",
    "Academic Calendar 2026-27": "https://mitaoe.ac.in/2026-2027-Term-I-UG-Calendar.html",
    "Academic Calendar Portal": "https://mitaoe.ac.in/mitaoe-academic-calendar.php",
    "Examination Time Table": "https://mitaoe.ac.in/academic-year-2026-2027.php",
    "Downloads & Circulars": "https://mitaoe.ac.in/downloads.php",
}

# In-memory dynamically discovered faculty catalog with TTL
_faculty_catalog: List[Dict[str, Any]] = []
_faculty_catalog_timestamp: float = 0.0
_CATALOG_TTL = 3600.0  # 1 hour


async def get_or_build_faculty_catalog(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Concurrently discover all faculty profile URLs and cards from official MITAOE department pages.
    Cached in-memory to deliver sub-millisecond lookups while remaining 100% dynamic.
    """
    global _faculty_catalog, _faculty_catalog_timestamp
    now = time.monotonic()

    if _faculty_catalog and not force_refresh and (now - _faculty_catalog_timestamp) < _CATALOG_TTL:
        return _faculty_catalog

    logger.info("Building dynamic faculty profile catalog from department portals...")
    catalog: List[Dict[str, Any]] = []
    seen_urls = set()

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        tasks = [client.get(url, headers={"User-Agent": "VEDANTA-Bot/1.0 (+https://mitaoe.ac.in)"}) for _, url in DEPARTMENT_PORTALS]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for (dept_name, d_url), resp in zip(DEPARTMENT_PORTALS, responses):
            if isinstance(resp, Exception) or not hasattr(resp, "status_code") or resp.status_code != 200:
                continue

            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    full_url = urljoin(d_url, href)

                    if full_url in seen_urls:
                        continue

                    # Filter for faculty profile patterns
                    is_profile = any(
                        p in full_url.lower()
                        for p in [
                            "btech-",
                            "school-of-humanities-and-engineering",
                            "department-of-humanities",
                            "director-profile",
                        ]
                    ) and not any(
                        skip in full_url.lower()
                        for skip in ["btech-programs", "mtech-", "bdes-", "admission", "curriculum", "syllabus"]
                    )

                    if is_profile:
                        seen_urls.add(full_url)
                        parent = a.find_parent("div") or a.parent
                        card_text = parent.get_text(separator=" ", strip=True) if parent else ""
                        html_str = str(parent) if parent else ""
                        slug = full_url.split("/")[-1].replace(".php", "")

                        catalog.append({
                            "url": full_url,
                            "dept": dept_name,
                            "slug": slug,
                            "card_text": card_text,
                            "html_snippet": html_str,
                            "source_page": d_url,
                        })
            except Exception as e:
                logger.debug("Error parsing department links", dept=dept_name, error=str(e))

    if catalog:
        _faculty_catalog = catalog
        _faculty_catalog_timestamp = now
        logger.info("Dynamic faculty catalog built successfully", total_profiles=len(catalog))

    return _faculty_catalog


async def discover_and_fetch_person(person_query: str) -> List[dict]:
    """
    Autonomous, generic discovery of ANY faculty member at MITAOE without hardcoding.
    Searches the official institutional portal dynamically, fetches their official profile,
    extracts structured credentials, and validates identity strictly.
    """
    person_name = extract_person_name_from_query(person_query)
    if not person_name:
        # Fallback to token extraction
        cleaned = re.sub(r"\b(who|is|tell|me|about|the|dr|prof|mr|ms|mrs)\b", "", person_query, flags=re.I).strip()
        tokens = [t.lower() for t in cleaned.split() if len(t) >= 3]
        if not tokens:
            return []
        person_name = " ".join(tokens)

    logger.info("Autonomous generic faculty discovery initiated", requested_person=person_name)
    tokens = [t.lower() for t in normalize_name_tokens(person_name) if len(t) >= 3]
    if not tokens:
        return []

    catalog = await get_or_build_faculty_catalog()

    # 1. Match requested person against catalog
    target_entry = None
    for entry in catalog:
        slug_match = all(t in entry["slug"].lower() for t in tokens)
        card_match = all(t in entry["card_text"].lower() for t in tokens)
        html_match = all(t in entry["html_snippet"].lower() for t in tokens)

        if slug_match or card_match or html_match:
            target_entry = entry
            break

    # If still not found, check if last name / first name match with initials
    if not target_entry and len(tokens) >= 2:
        for entry in catalog:
            if tokens[-1] in entry["slug"].lower() or tokens[-1] in entry["card_text"].lower():
                target_entry = entry
                break

    if not target_entry:
        logger.info("Person not found in official portal catalog", person=person_name)
        return []

    target_url = target_entry["url"]
    target_dept = target_entry["dept"]
    logger.info("Official profile page located", person=person_name, url=target_url)

    # 2. Fetch the authoritative profile page
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(target_url, headers={"User-Agent": "VEDANTA-Bot/1.0 (+https://mitaoe.ac.in)"})
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            page_text = soup.get_text(separator=" ", strip=True)

            # Extract Full Name
            h = soup.find(["h2", "h1"])
            extracted_name = h.get_text(strip=True) if h else ""
            if not extracted_name:
                name_m = re.search(r"\bNAME\s*:\s*([A-Za-z\s\.\(\)]+?)(?:DESIGNATION|QUALIFICATION|FORE\s+FRONT|EMAIL|\.|\n|$)", page_text, re.I)
                extracted_name = name_m.group(1).strip() if name_m else person_name

            # Clean name of any trailing keywords
            extracted_name = re.sub(r"\b(Assistant|Associate|Professor|Lecturer|QUALIFICATION|NAME)\b.*$", "", extracted_name, flags=re.I).strip()
            extracted_name = re.sub(r"[\s,]+$", "", extracted_name)

            # Strict Identity Isolation: Ensure extracted name actually matches requested name!
            is_match, conf, rationale = matches_identity(person_name, extracted_name)
            if not is_match:
                logger.warning(
                    "Identity mismatch rejected during autonomous discovery",
                    requested=person_name,
                    extracted=extracted_name,
                    rationale=rationale,
                )
                return []

            # Extract Designation
            desig_m = re.search(
                r"\b(Senior\s+Assistant\s+Professor|Assistant\s+Professor|Associate\s+Professor|Professor\s+of\s+Practice|Professor|Lecturer|Head\s+of\s+Department|Dean)\b",
                page_text,
                re.I,
            )
            designation = desig_m.group(0).strip() if desig_m else "Faculty Member"

            # Extract Department
            dept_m = re.search(r"(?:Department|School)\s+of\s+([A-Za-z\s&–]+?)(?:,|\.|\sat\sMITAOE|\sat\sMIT)", page_text, re.I)
            department = dept_m.group(0).strip() if dept_m else target_dept

            # Extract Official Email
            email_m = re.search(r"\b[A-Za-z0-9._%+-]+@mitaoe\.(?:ac\.in|edu\.in)\b", page_text, re.I)
            email = email_m.group(0) if email_m else ""

            # Extract Academic Qualification
            qual_m = re.search(r"QUALIFICATION\s*:\s*([A-Za-z0-9\s\.\(\),\-_]+?)(?:EXPERIENCE|FORE\s+FRONT|EMAIL|CONTACT|OVERVIEW|\.|\n|$)", page_text, re.I)
            qualification = qual_m.group(1).strip() if qual_m else ""

            # Extract Forefront Research
            research_m = re.search(r"FORE\s+FRONT\s+AREA\s+OF\s+RESEARCH\s*:\s*([A-Za-z0-9\s\.\(\),\-_]+?)(?:EMAIL|CONTACT|EXPERIENCE|OVERVIEW|\.|\n|$)", page_text, re.I)
            research = research_m.group(1).strip() if research_m else ""

            # 3. Register into Knowledge Graph dynamically
            try:
                from app.intelligence.knowledge_graph import get_knowledge_graph
                kg = get_knowledge_graph()
                kg.add_faculty_profile(
                    name=extracted_name,
                    designation=designation,
                    department_name=department,
                    email=email,
                    url=target_url,
                    qualification=qualification,
                    research=research,
                )
            except Exception as e:
                logger.debug("Failed to dynamically register KG profile", error=str(e))

            # 4. Compose authoritative evidence chunk
            qual_line = f"- Academic Qualification: {qualification}\n" if qualification else ""
            res_line = f"- Forefront Research: {research}\n" if research else ""
            email_line = f"- Official Email: {email}\n" if email else ""

            chunk_text = (
                f"Official Faculty Profile: **{extracted_name}** is an **{designation}** in the **{department}** "
                f"at MIT Academy of Engineering (MITAOE), Alandi, Pune.\n"
                f"- Full Name: {extracted_name}\n"
                f"- Designation: {designation}\n"
                f"- Department / School: {department}\n"
                f"{qual_line}"
                f"{res_line}"
                f"{email_line}"
                f"- Official Profile Link: {target_url}\n"
                f"Verified from official institutional portal at {target_url}."
            )

            cid = str(uuid.uuid4())
            discovered_chunk = {
                "chunk_id": cid,
                "text": chunk_text,
                "source_url": target_url,
                "source_title": f"{extracted_name} | {department} | MITAOE",
                "page_number": None,
                "academic_year": "2026-27",
            }

            logger.info("Faculty discovered, verified, and indexed dynamically", person=extracted_name, url=target_url)
            return [discovered_chunk]

    except Exception as e:
        logger.error("Error fetching faculty profile", url=target_url, error=str(e))
        return []


async def fetch_and_index_topic(query: str, query_context) -> List[dict]:
    """
    Question-driven targeted fetch for missing pages and entities.
    """
    # 1. Check if query is looking for a specific person
    q_lower = query.lower()
    is_person_inquiry = False

    if query_context and query_context.entities:
        for ent in query_context.entities:
            if ent.entity_type == "person":
                is_person_inquiry = True
                break

    if not is_person_inquiry:
        is_person_inquiry = any(k in q_lower for k in ["who is", "who was", "faculty", "professor", "dr.", "prof.", "mr.", "mrs.", "ms."])

    if is_person_inquiry:
        person_chunks = await discover_and_fetch_person(query)
        if person_chunks:
            return person_chunks

    # 2. Check departmental and topical URLs
    target_url = None
    target_dept = None

    if query_context and query_context.departments:
        dept = query_context.departments[0]
        for name, url in OFFICIAL_PAGES.items():
            if dept.lower() in name.lower() or name.lower() in dept.lower():
                target_url = url
                target_dept = dept
                break

    if not target_url:
        if "calendar" in q_lower:
            target_url = OFFICIAL_PAGES["Academic Calendar 2026-27"]
        elif "timetable" in q_lower or "time table" in q_lower or "examination" in q_lower:
            target_url = OFFICIAL_PAGES["Examination Time Table"]
        elif "director" in q_lower:
            target_url = OFFICIAL_PAGES["Director Profile"]
        elif "placement" in q_lower or "salary" in q_lower or "package" in q_lower:
            target_url = OFFICIAL_PAGES["Placement Portal"]
        elif "download" in q_lower or "circular" in q_lower:
            target_url = OFFICIAL_PAGES["Downloads & Circulars"]

    if not target_url:
        return []

    logger.info("Question-driven fetch initiated", url=target_url, dept=target_dept)
    chunks_out = []

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(target_url, headers={"User-Agent": "VEDANTA-Bot/1.0 (+https://mitaoe.ac.in)"})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for s in soup(["script", "style", "nav", "footer", "noscript"]):
                    s.decompose()
                title = soup.title.string.strip() if soup.title else target_dept or "MITAOE"
                main = soup.find("main") or soup.find("article") or soup.body
                text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

                chunker = TextChunker(max_tokens=512, overlap_tokens=64)
                parsed_chunks = chunker.chunk(text, source_url=target_url, source_title=title)

                for c in parsed_chunks:
                    cid = str(uuid.uuid4())
                    chunks_out.append({
                        "chunk_id": cid,
                        "text": c.text,
                        "source_url": target_url,
                        "source_title": title,
                        "page_number": None,
                        "academic_year": "2026-27",
                    })

                logger.info("Question-driven fetch succeeded", url=target_url, chunks=len(chunks_out))
    except Exception as e:
        logger.warning("Question-driven fetch failed", url=target_url, error=str(e))

    return chunks_out
