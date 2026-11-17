"""
VEDANTA — Knowledge Graph Engine
In-memory directed multi-graph of institutional entities, relationships, departments,
faculty, placements, fee structures, and governance using NetworkX.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx

from app.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeGraphEngine:
    """
    Institutional Knowledge Graph for MIT Academy of Engineering (MITAOE).
    Grounds all entity questions, faculty queries, department lookups,
    and statistical comparisons in an interconnected multi-relational graph.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._is_initialized = False
        self._entity_alias_index: Dict[str, str] = {}

    def initialize_graph(self):
        """Construct the core institutional topology and relationships."""
        self.graph.clear()
        self._entity_alias_index.clear()

        # 1. Institution Root Node
        self.add_entity_node(
            node_id="inst:mitaoe",
            canonical_name="MIT Academy of Engineering",
            node_type="institution",
            aliases=["MITAOE", "MIT Pune Alandi", "MIT Academy", "MIT Alandi"],
            metadata={
                "website": "https://mitaoe.ac.in/",
                "established": 1999,
                "affiliation": "Savitribai Phule Pune University (Autonomous)",
                "location": "Alandi, Pune, Maharashtra, India",
                "tagline": "Discover Knowledge. Trust Every Answer.",
                "current_academic_year": "2026-27",
            }
        )

        # 2. Academic Years
        academic_years = ["2026-27", "2025-26", "2024-25", "2023-24"]
        for ay in academic_years:
            self.add_entity_node(
                node_id=f"ay:{ay}",
                canonical_name=f"Academic Year {ay}",
                node_type="academic_year",
                aliases=[ay, f"AY {ay}", f"AY{ay}"],
                metadata={
                    "year_label": ay,
                    "is_current": (ay == "2026-27"),
                }
            )
            self.graph.add_edge("inst:mitaoe", f"ay:{ay}", rel_type="OFFERS_ACADEMIC_CYCLE", academic_year=ay)

        # 3. Academic Departments
        depts = [
            {
                "id": "dept:comp",
                "name": "Department of Computer Engineering",
                "code": "CE",
                "aliases": ["Computer Engineering", "CE", "Comp", "Computer Dept", "CSE (Core)"],
                "url": "https://mitaoe.ac.in/department-of-computer-engineering.php",
                "description": "Core computing algorithms, distributed systems, systems software, and computer engineering.",
            },
            {
                "id": "dept:it",
                "name": "Department of Information Technology",
                "code": "IT",
                "aliases": ["Information Technology", "IT", "IT Dept", "Information Tech"],
                "url": "https://mitaoe.ac.in/department-of-information-technology.php",
                "description": "Enterprise cloud computing, cybersecurity, network architectures, and information systems.",
            },
            {
                "id": "dept:se",
                "name": "Department of Computer Engineering (Software Engineering)",
                "code": "SE",
                "aliases": ["Software Engineering", "SE", "Software Engg", "Comp Software"],
                "url": "https://mitaoe.ac.in/department-of-software-engineering.php",
                "description": "Modern software architecture, devops, agile engineering, and cloud platforms.",
            },
            {
                "id": "dept:aiml",
                "name": "Department of Computer Science & Engineering (AI & ML)",
                "code": "AIML",
                "aliases": ["Artificial Intelligence and Machine Learning", "AI & ML", "AIML", "AI/ML", "AI", "ML"],
                "url": "https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php",
                "description": "Deep learning, neural architectures, computer vision, NLP, and cognitive computing.",
            },
            {
                "id": "dept:ds",
                "name": "Department of Computer Science & Engineering (Data Science)",
                "code": "DS",
                "aliases": ["Data Science", "DS", "CSE Data Science", "Big Data"],
                "url": "https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php",
                "description": "Statistical modeling, big data architectures, predictive analytics, and data engineering.",
            },
            {
                "id": "dept:entc",
                "name": "Department of Electronics & Telecommunication Engineering",
                "code": "ENTC",
                "aliases": ["Electronics and Telecommunication Engineering", "ENTC", "E&TC", "ETC", "Telecom"],
                "url": "https://mitaoe.ac.in/department-of-electronics-and-telecomminication-engineering.php",
                "description": "VLSI design, embedded systems, wireless communications, IoT, and signal processing.",
            },
            {
                "id": "dept:mech",
                "name": "Department of Mechanical Engineering",
                "code": "MECH",
                "aliases": ["Mechanical Engineering", "MECH", "ME", "Mechanical"],
                "url": "https://mitaoe.ac.in/department-of-mechanical-engineering.php",
                "description": "Robotics, thermal engineering, CAD/CAM, smart manufacturing, and mechatronics.",
            },
            {
                "id": "dept:civil",
                "name": "Department of Civil Engineering",
                "code": "CIVIL",
                "aliases": ["Civil Engineering", "CIVIL", "Civil"],
                "url": "https://mitaoe.ac.in/department-of-civil-engineering.php",
                "description": "Structural dynamics, environmental engineering, smart city infrastructure, and GIS.",
            },
            {
                "id": "dept:chem",
                "name": "Department of Chemical Engineering",
                "code": "CHEM",
                "aliases": ["Chemical Engineering", "CHEM", "Chemical"],
                "url": "https://mitaoe.ac.in/department-of-chemical-engineering.php",
                "description": "Process design, biochemical technology, reaction engineering, and separation processes.",
            },
            {
                "id": "dept:hes",
                "name": "School of Humanities and Engineering Sciences",
                "code": "HES",
                "aliases": ["Humanities and Engineering Sciences", "HES", "First Year Department", "Humanities", "Applied Sciences", "Mathematics Dept"],
                "url": "https://mitaoe.ac.in/mitaoe-school-of-humanities-and-engineering-sciences.php",
                "description": "Foundational engineering sciences, applied mathematics, engineering physics, chemistry, and professional communication.",
            },
            {
                "id": "dept:design",
                "name": "School of Design",
                "code": "DES",
                "aliases": ["School of Design", "Design", "B.Des", "Industrial Design", "Product Design"],
                "url": "https://mitaoe.ac.in/mitaoe-school-of-design.php",
                "description": "Product design, user experience design, communication design, and industrial innovation.",
            },
        ]

        for d in depts:
            self.add_entity_node(
                node_id=d["id"],
                canonical_name=d["name"],
                node_type="department",
                aliases=d["aliases"],
                metadata={
                    "code": d["code"],
                    "url": d["url"],
                    "description": d["description"],
                }
            )
            self.graph.add_edge(d["id"], "inst:mitaoe", rel_type="BELONGS_TO")

        # 4. Leadership & Faculty Entities
        people = [
            {
                "id": "person:pramod_ganjewar",
                "name": "Dr. Pramod D. Ganjewar",
                "type": "person",
                "aliases": ["Dr. Pramod Ganjewar", "Pramod Ganjewar", "Dr. P. D. Ganjewar", "HOD Computer", "HOD CE", "HOD Comp"],
                "designation": "Associate Professor & HOD",
                "dept_id": "dept:comp",
                "email": "hod.comp@mitaoe.edu.in",
                "url": "https://mitaoe.ac.in/department-of-computer-engineering.php",
                "is_current_hod": True,
                "qualification": "PhD in Computer Engineering",
                "notes": "Current Head of Department for Computer Engineering (AY 2026-27).",
            },
            {
                "id": "person:sandip_gade",
                "name": "Dr. Sandip A. Gade",
                "type": "person",
                "aliases": ["Dr. Sandip Gade", "Sandip Gade", "Dr. S. A. Gade", "Previous HOD Comp", "Former HOD CE"],
                "designation": "Professor (Former HOD)",
                "dept_id": "dept:comp",
                "email": "sagade@comp.mitaoe.ac.in",
                "url": "https://mitaoe.ac.in/department-of-computer-engineering.php",
                "is_current_hod": False,
                "is_former_hod": True,
                "qualification": "PhD in Computer Engineering",
                "notes": "Institutional records confirm Dr. Sandip A. Gade previously served as Head of Department of Computer Engineering.",
            },
            {
                "id": "person:bhagyashree_dhakulkar",
                "name": "Dr. Bhagyashree Dhakulkar",
                "type": "person",
                "aliases": ["Dr. Bhagyashree Dhakulkar", "Bhagyashree Dhakulkar", "HOD IT", "HOD Information Technology"],
                "designation": "Associate Professor & HOD",
                "dept_id": "dept:it",
                "email": "hod.it@mitaoe.edu.in",
                "url": "https://mitaoe.ac.in/department-of-information-technology.php",
                "is_current_hod": True,
                "notes": "Current Head of Department for Information Technology.",
            },
            {
                "id": "person:nitin_kulkarni",
                "name": "Dr. Nitin K. Kulkarni",
                "type": "person",
                "aliases": ["Dr. Nitin Kulkarni", "Nitin Kulkarni", "HOD Software Engineering", "HOD SE"],
                "designation": "Associate Professor & HOD",
                "dept_id": "dept:se",
                "email": "hod.se@mitaoe.edu.in",
                "url": "https://mitaoe.ac.in/department-of-software-engineering.php",
                "is_current_hod": True,
                "notes": "Current Head of Department for Software Engineering.",
            },
            {
                "id": "person:sunita_barve",
                "name": "Dr. Sunita S. Barve",
                "type": "person",
                "aliases": ["Dr. Sunita Barve", "Sunita Barve", "HOD AIML", "HOD AI & ML", "HOD AI/ML"],
                "designation": "Associate Professor & HOD",
                "dept_id": "dept:aiml",
                "email": "hod.aiml@mitaoe.edu.in",
                "url": "https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php",
                "is_current_hod": True,
                "notes": "Current Head of Department for CSE (AI & ML).",
            },
            {
                "id": "person:pratibha_kale",
                "name": "Dr. Pratibha D. Kale",
                "type": "person",
                "aliases": ["Dr. Pratibha Kale", "Pratibha Kale", "HOD Data Science", "HOD DS"],
                "designation": "Associate Professor & HOD",
                "dept_id": "dept:ds",
                "email": "hod.ds@mitaoe.edu.in",
                "url": "https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php",
                "is_current_hod": True,
                "notes": "Current Head of Department for CSE (Data Science).",
            },
            {
                "id": "person:yogesh_bhalerao",
                "name": "Dr. Yogesh. J. Bhalerao",
                "type": "person",
                "aliases": ["Dr. Yogesh Bhalerao", "Yogesh Bhalerao", "Dr. Y. J. Bhalerao", "Director MITAOE", "Director"],
                "designation": "Director",
                "dept_id": None,
                "email": "director@mitaoe.ac.in",
                "url": "https://mitaoe.ac.in/mitaoe-director-profile.php",
                "notes": "Institutional Director & Academic Council Chairman.",
            },
            {
                "id": "person:mahesh_goudar",
                "name": "Dr. Mahesh D. Goudar",
                "type": "person",
                "aliases": ["Dr. Mahesh Goudar", "Mahesh Goudar", "Officiating Director"],
                "designation": "Officiating Director / Academic Leader",
                "dept_id": None,
                "email": "mdgoudar@mitaoe.ac.in",
                "url": "https://mitaoe.ac.in/mitaoe-leadership.php",
                "notes": "Academic leadership and former officiating director.",
            },
        ]

        for p in people:
            self.add_entity_node(
                node_id=p["id"],
                canonical_name=p["name"],
                node_type="person",
                aliases=p["aliases"],
                metadata=p,
            )
            # Department relationship
            dept_id = p.get("dept_id")
            if dept_id and self.graph.has_node(dept_id):
                if p.get("is_current_hod"):
                    self.graph.add_edge(p["id"], dept_id, rel_type="HEADS", academic_year="2026-27", status="current")
                    self.graph.add_edge(dept_id, p["id"], rel_type="HEADED_BY", academic_year="2026-27", status="current")
                elif p.get("is_former_hod"):
                    self.graph.add_edge(p["id"], dept_id, rel_type="FORMERLY_HEADED", status="historical")
                    self.graph.add_edge(dept_id, p["id"], rel_type="FORMERLY_HEADED_BY", status="historical")
                else:
                    self.graph.add_edge(p["id"], dept_id, rel_type="WORKS_IN")
            elif p.get("designation") == "Director":
                self.graph.add_edge(p["id"], "inst:mitaoe", rel_type="DIRECTS")

        # 5. Institutional Placement Facts (2023-24 Ground Truth from placement.php)
        self.add_entity_node(
            node_id="fact:placement:aggregate",
            canonical_name="MITAOE Placement Statistics 2023-24 (Institutional Aggregate)",
            node_type="placement",
            aliases=["Overall Placement Statistics", "Aggregate Placement", "MITAOE Placement", "Placement Statistics"],
            metadata={
                "academic_year": "2023-24",
                "highest_package_lpa": 27.0,
                "average_package_lpa": 6.75,
                "median_package_lpa": 6.0,
                "placement_offers": "500+",
                "internship_offers": "800+",
                "recruiting_companies": "450+",
                "source_url": "https://mitaoe.ac.in/placement.php",
                "provenance": "Primary data extracted directly from dynamic data-target counters on MITAOE placement portal.",
            }
        )
        self.graph.add_edge("inst:mitaoe", "fact:placement:aggregate", rel_type="HAS_PLACEMENT_STATISTICS")

        # Department-specific placement records
        dept_placement_data = [
            ("dept:comp", 206, 182, 24.5, 6.8, 88.3),
            ("dept:aiml", 66, 58, 21.0, 6.9, 87.8),
            ("dept:it", 130, 110, 18.0, 6.2, 84.6),
            ("dept:entc", 180, 145, 16.5, 5.4, 80.5),
            ("dept:mech", 135, 98, 12.0, 4.8, 72.5),
            ("dept:civil", 65, 44, 9.5, 4.2, 67.7),
            ("dept:chem", 50, 36, 10.0, 4.5, 72.0),
        ]
        for dept_id, total, placed, highest, avg, pct in dept_placement_data:
            node_id = f"fact:placement:{dept_id.split(':')[-1]}"
            self.add_entity_node(
                node_id=node_id,
                canonical_name=f"Placement Statistics - {self.graph.nodes[dept_id]['canonical_name']}",
                node_type="placement",
                aliases=[f"{self.graph.nodes[dept_id]['metadata']['code']} Placement"],
                metadata={
                    "department_id": dept_id,
                    "academic_year": "2023-24",
                    "total_eligible": total,
                    "students_placed": placed,
                    "highest_package_lpa": highest,
                    "average_package_lpa": avg,
                    "placement_percentage": pct,
                    "source_url": "https://mitaoe.ac.in/placement.php",
                }
            )
            self.graph.add_edge(dept_id, node_id, rel_type="HAS_PLACEMENT_STATISTICS")

        # 6. Approved Fee Structure (AY 2026-27 Ground Truth from FY-BTech-Fee-Structure-26-27.PDF)
        self.add_entity_node(
            node_id="fact:fee:ay2026_27",
            canonical_name="Approved First Year B.Tech Fee Structure (AY 2026–27)",
            node_type="fee",
            aliases=["Fee Structure 2026-27", "First Year B.Tech Fees", "College Fees", "Admission Fees", "MITAOE Fee Structure"],
            metadata={
                "academic_year": "2026-27",
                "open_total_fee": 212737.0,
                "open_tuition": 184348.0,
                "open_development": 27652.0,
                "open_university": 737.0,
                "caution_deposit_refundable": 25000.0,
                "obc_ebc_fee": 120563.0,
                "sc_st_tfws_vjnt_fee": 28389.0,
                "jk_migrant_fee": 24797.0,
                "sppu_eligibility_mh": 650.0,
                "sppu_eligibility_oms": 1150.0,
                "source_url": "https://mitaoe.ac.in/assets/images/pdf/FY-BTech-Fee-Structure-26-27.PDF",
            }
        )
        self.graph.add_edge("inst:mitaoe", "fact:fee:ay2026_27", rel_type="HAS_FEE_STRUCTURE", academic_year="2026-27")

        self._is_initialized = True
        logger.info(
            "Knowledge graph built successfully",
            nodes=self.graph.number_of_nodes(),
            edges=self.graph.number_of_edges(),
        )

    def add_entity_node(
        self,
        node_id: str,
        canonical_name: str,
        node_type: str,
        aliases: List[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        """Add a typed node and register all its alias lookup variations."""
        aliases = aliases or []
        meta = metadata or {}
        self.graph.add_node(
            node_id,
            canonical_name=canonical_name,
            node_type=node_type,
            aliases=aliases,
            metadata=meta,
        )

        # Index canonical and aliases in lowercase
        self._entity_alias_index[canonical_name.lower().strip()] = node_id
        for alias in aliases:
            self._entity_alias_index[alias.lower().strip()] = node_id

    def find_entity(self, query: str, entity_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Resolve an entity query to a canonical node in the knowledge graph.
        Performs exact alias lookup, token subset matching, and type filtering.
        """
        if not self._is_initialized:
            self.initialize_graph()

        q = query.lower().strip()
        # Clean punctuation
        q_clean = re.sub(r"[^\w\s]", " ", q).strip()
        q_clean = re.sub(r"\s+", " ", q_clean)

        # 1. Exact alias match
        if q in self._entity_alias_index:
            node_id = self._entity_alias_index[q]
            node_data = self.graph.nodes[node_id]
            if not entity_type or node_data.get("node_type") == entity_type:
                return {"node_id": node_id, **node_data}

        if q_clean in self._entity_alias_index:
            node_id = self._entity_alias_index[q_clean]
            node_data = self.graph.nodes[node_id]
            if not entity_type or node_data.get("node_type") == entity_type:
                return {"node_id": node_id, **node_data}

        # 2. Substring matching in aliases
        for alias, node_id in self._entity_alias_index.items():
            if len(alias) >= 3 and (alias in q_clean or q_clean in alias):
                node_data = self.graph.nodes[node_id]
                if not entity_type or node_data.get("node_type") == entity_type:
                    return {"node_id": node_id, **node_data}

        return None

    def get_hod(
        self,
        department_name_or_code: str,
        include_predecessor: bool = False,
    ) -> Dict[str, Any]:
        """
        Retrieve current (and optionally historical) HOD for a department.
        Handles CE vs CSE distinctions gracefully.
        """
        if not self._is_initialized:
            self.initialize_graph()

        dept_entity = self.find_entity(department_name_or_code, entity_type="department")
        if not dept_entity:
            # Fallback check
            for nid, data in self.graph.nodes(data=True):
                if data.get("node_type") == "department":
                    code = data.get("metadata", {}).get("code", "")
                    if code.lower() == department_name_or_code.lower():
                        dept_entity = {"node_id": nid, **data}
                        break

        if not dept_entity:
            return {"found": False, "message": f"Department '{department_name_or_code}' not found."}

        dept_id = dept_entity["node_id"]
        canonical_name = dept_entity["canonical_name"]
        code = dept_entity.get("metadata", {}).get("code", "")

        current_hod = None
        historical_hod = None

        for src, dst, key, edge_data in self.graph.out_edges(dept_id, keys=True, data=True):
            if edge_data.get("rel_type") == "HEADED_BY":
                person = self.graph.nodes[dst]
                current_hod = {
                    "name": person["canonical_name"],
                    "designation": person["metadata"].get("designation", "Head of Department"),
                    "email": person["metadata"].get("email"),
                    "url": person["metadata"].get("url"),
                    "department": canonical_name,
                    "code": code,
                    "notes": person["metadata"].get("notes", ""),
                }
            elif edge_data.get("rel_type") == "FORMERLY_HEADED_BY":
                person = self.graph.nodes[dst]
                historical_hod = {
                    "name": person["canonical_name"],
                    "designation": person["metadata"].get("designation", "Former HOD"),
                    "email": person["metadata"].get("email"),
                    "url": person["metadata"].get("url"),
                    "department": canonical_name,
                    "code": code,
                    "notes": person["metadata"].get("notes", ""),
                }

        # CSE Disambiguation if queried as "CSE"
        is_cse_query = "cse" in department_name_or_code.lower() or "computer science and engineering" in department_name_or_code.lower()

        sub_branches = []
        if is_cse_query:
            # Gather sub-branches under the CSE umbrella
            for sub_code, sub_id in [("SE", "dept:se"), ("AIML", "dept:aiml"), ("DS", "dept:ds")]:
                sub_dept = self.graph.nodes[sub_id]
                for s, d, k, ed in self.graph.out_edges(sub_id, keys=True, data=True):
                    if ed.get("rel_type") == "HEADED_BY":
                        p = self.graph.nodes[d]
                        sub_branches.append({
                            "department": sub_dept["canonical_name"],
                            "code": sub_code,
                            "hod_name": p["canonical_name"],
                            "designation": p["metadata"].get("designation"),
                            "url": sub_dept["metadata"].get("url"),
                        })

        return {
            "found": True,
            "department": canonical_name,
            "code": code,
            "current_hod": current_hod,
            "historical_hod": historical_hod,
            "is_cse_umbrella": is_cse_query,
            "cse_sub_branches": sub_branches,
        }

    def add_faculty_profile(
        self,
        name: str,
        designation: str,
        department_name: str,
        email: str,
        url: str,
        qualification: str = "",
        research: str = "",
        aliases: Optional[List[str]] = None,
    ) -> str:
        """
        Dynamically register a discovered faculty member into the Knowledge Graph.
        """
        if not self._is_initialized:
            self.initialize_graph()

        node_id = f"person:faculty_{re.sub(r'[^a-z0-9]', '_', name.lower())}"
        aliases = aliases or []

        # Find affiliated department node
        dept_id = None
        for nid, data in self.graph.nodes(data=True):
            if data.get("node_type") == "department":
                dept_canon = data.get("canonical_name", "").lower()
                if department_name.lower() in dept_canon or dept_canon in department_name.lower():
                    dept_id = nid
                    break

        self.add_entity_node(
            node_id=node_id,
            node_type="person",
            canonical_name=name,
            aliases=[name] + aliases,
            metadata={
                "designation": designation,
                "email": email,
                "url": url,
                "qualification": qualification,
                "research": research,
                "department_name": department_name,
            },
        )

        if dept_id:
            self.graph.add_edge(node_id, dept_id, rel_type="WORKS_IN")

        return node_id

    def get_faculty_profile(self, name_query: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete faculty record, department, and contact info using strict identity matching."""
        if not self._is_initialized:
            self.initialize_graph()

        from app.intelligence.entity_engine.identity_resolver import matches_identity

        best_match = None
        best_score = 0.0

        for nid, data in self.graph.nodes(data=True):
            if data.get("node_type") == "person":
                c_name = data.get("canonical_name", "")
                aliases = data.get("aliases", [])

                is_m, score, _ = matches_identity(name_query, c_name)
                if is_m and score > best_score:
                    best_match = (nid, data)
                    best_score = score
                    continue

                for alias in aliases:
                    is_m, score, _ = matches_identity(name_query, alias)
                    if is_m and score > best_score:
                        best_match = (nid, data)
                        best_score = score

        if not best_match:
            return None

        node_id, node_data = best_match
        meta = node_data.get("metadata", {})
        canonical_name = node_data.get("canonical_name")

        # Find affiliated department
        dept_info = None
        for u, v, data in self.graph.edges(node_id, data=True):
            if data.get("rel_type") in ("WORKS_IN", "HEADS", "FORMERLY_HEADED"):
                dept = self.graph.nodes[v]
                dept_info = {
                    "name": dept["canonical_name"],
                    "url": dept["metadata"].get("url"),
                    "code": dept["metadata"].get("code"),
                }
                break

        if not dept_info and meta.get("department_name"):
            dept_info = {
                "name": meta.get("department_name"),
                "url": meta.get("url"),
            }

        return {
            "canonical_name": canonical_name,
            "designation": meta.get("designation", "Faculty Member"),
            "email": meta.get("email"),
            "qualification": meta.get("qualification"),
            "research": meta.get("research"),
            "url": meta.get("url"),
            "department": dept_info or {"name": "MIT Academy of Engineering"},
            "notes": meta.get("notes"),
        }

    def get_placement_summary(self, department: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve verified placement stats from graph."""
        if not self._is_initialized:
            self.initialize_graph()

        if not department:
            agg = self.graph.nodes.get("fact:placement:aggregate")
            return agg["metadata"] if agg else {}

        ent = self.find_entity(department, entity_type="department")
        if ent:
            dept_id = ent["node_id"]
            for u, v, data in self.graph.out_edges(dept_id, data=True):
                if data.get("rel_type") == "HAS_PLACEMENT_STATISTICS":
                    return self.graph.nodes[v]["metadata"]

        return {}

    def get_fee_summary(self) -> Dict[str, Any]:
        """Retrieve verified fee structure from graph."""
        if not self._is_initialized:
            self.initialize_graph()

        fee_node = self.graph.nodes.get("fact:fee:ay2026_27")
        return fee_node["metadata"] if fee_node else {}

    def compare_departments(self, dept1_query: str, dept2_query: str) -> Dict[str, Any]:
        """Compare placement statistics between two departments."""
        if not self._is_initialized:
            self.initialize_graph()

        d1 = self.find_entity(dept1_query, entity_type="department")
        d2 = self.find_entity(dept2_query, entity_type="department")

        if not d1 or not d2:
            return {"error": "One or both departments could not be resolved."}

        p1 = self.get_placement_summary(d1["canonical_name"])
        p2 = self.get_placement_summary(d2["canonical_name"])

        return {
            "dept1": {
                "name": d1["canonical_name"],
                "code": d1["metadata"].get("code"),
                "stats": p1,
            },
            "dept2": {
                "name": d2["canonical_name"],
                "code": d2["metadata"].get("code"),
                "stats": p2,
            },
        }


# Singleton instance
_graph_engine_instance: Optional[KnowledgeGraphEngine] = None


def get_knowledge_graph() -> KnowledgeGraphEngine:
    global _graph_engine_instance
    if _graph_engine_instance is None:
        _graph_engine_instance = KnowledgeGraphEngine()
        _graph_engine_instance.initialize_graph()
    return _graph_engine_instance
