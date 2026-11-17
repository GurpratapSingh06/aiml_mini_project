"""
VEDANTA — Comprehensive Knowledge Seeder
Populates PostgreSQL relational tables, entities, placement facts, fee structures,
and creates retrieval chunks for the hybrid search engine.
"""

import asyncio
import uuid
import datetime
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

INSTITUTION_ID = "00000000-0000-0000-0000-000000000001"

async def seed_all():
    async with AsyncSessionLocal() as session:
        print("=== SEEDING COMPREHENSIVE KNOWLEDGE MODEL ===")

        # 1. Academic Years
        print("1. Seeding academic_years...")
        academic_years = [
            ("2026-27", 2026, 2027, True),
            ("2025-26", 2025, 2026, False),
            ("2024-25", 2024, 2025, False),
            ("2023-24", 2023, 2024, False),
        ]
        for y_label, s_yr, e_yr, is_curr in academic_years:
            await session.execute(text("""
                INSERT INTO academic_years (id, institution_id, year_label, start_year, end_year, is_current, created_at)
                VALUES (:id, :inst_id, :y_label, :s_yr, :e_yr, :is_curr, NOW())
                ON CONFLICT (institution_id, year_label) DO UPDATE
                SET is_current = :is_curr, start_year = :s_yr, end_year = :e_yr
            """), {
                "id": str(uuid.uuid4()),
                "inst_id": INSTITUTION_ID,
                "y_label": y_label,
                "s_yr": s_yr,
                "e_yr": e_yr,
                "is_curr": is_curr,
            })

        # 2. Departments
        print("2. Seeding departments...")
        departments = [
            ("Computer Engineering", "Comp Engg", "CE"),
            ("Information Technology", "IT", "IT"),
            ("Software Engineering", "Software Engg", "SE"),
            ("Artificial Intelligence and Machine Learning", "AI & ML", "AIML"),
            ("Data Science", "Data Science", "DS"),
            ("Mechanical Engineering", "Mechanical", "MECH"),
            ("Civil Engineering", "Civil", "CIVIL"),
            ("Chemical Engineering", "Chemical", "CHEM"),
            ("Electronics and Telecommunication Engineering", "E&TC", "ENTC"),
            ("School of Humanities and Engineering Sciences", "Humanities & Engg Sciences", "HES"),
            ("School of Design", "Design", "DES"),
        ]
        dept_id_map = {}
        for name, short_name, abbrev in departments:
            dept_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"dept.{abbrev}.mitaoe"))
            dept_id_map[abbrev] = dept_id
            dept_id_map[name] = dept_id
            await session.execute(text("""
                INSERT INTO departments (id, institution_id, name, short_name, abbreviation, is_active, created_at)
                VALUES (:id, :inst_id, :name, :short_name, :abbrev, true, NOW())
                ON CONFLICT (id) DO UPDATE
                SET name = :name, short_name = :short_name, abbreviation = :abbrev
            """), {
                "id": dept_id,
                "inst_id": INSTITUTION_ID,
                "name": name,
                "short_name": short_name,
                "abbrev": abbrev,
            })

        # 3. Faculty Entity: Mr. Azhar R. Shaikh (Azher Shaikh)
        print("3. Seeding Azhar Shaikh entity...")
        azhar_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "faculty.azhar.shaikh.mitaoe"))
        hes_dept_id = dept_id_map["HES"]
        await session.execute(text("""
            INSERT INTO entities (id, institution_id, entity_type, canonical_name, description, is_active, entity_metadata, created_at, updated_at)
            VALUES (:id, :inst_id, 'PERSON', 'Mr. Azhar R. Shaikh', 'Assistant Professor in Mathematics, School of Humanities and Engineering Sciences', true, :meta, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE
            SET canonical_name = 'Mr. Azhar R. Shaikh', description = 'Assistant Professor in Mathematics, School of Humanities and Engineering Sciences'
        """), {
            "id": azhar_id,
            "inst_id": INSTITUTION_ID,
            "meta": '{"email": "azharshaikh@mitaoe.ac.in", "qualification": "MSc (Mathematics), NET (CSIR-UGC)", "research": "Algebra, Number Theory", "aliases": ["Azher Shaikh", "Shaikh Azhar Riyazoddin", "A. R. Shaikh"]}'
        })

        # Relationship: Azhar Shaikh WORKS_IN School of Humanities and Engineering Sciences
        hes_entity_res = await session.execute(text("SELECT id FROM entities WHERE canonical_name ILIKE '%Humanities%' LIMIT 1"))
        hes_row = hes_entity_res.fetchone()
        if hes_row:
            target_hes_id = str(hes_row[0])
            await session.execute(text("""
                INSERT INTO entity_relationships (id, source_entity_id, target_entity_id, relationship_type, academic_year, source_url, confidence, created_at)
                VALUES (:id, :source_id, :target_id, 'works_in', '2026-27', 'https://mitaoe.ac.in/school-of-humanities-and-engineering-sciences-arshaikh.php', 1.0, NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "rel.azhar.hes.mitaoe")),
                "source_id": azhar_id,
                "target_id": target_hes_id,
            })

        # 4. Placement Records
        print("4. Seeding placement_records...")
        # Institutional Aggregate
        await session.execute(text("""
            INSERT INTO placement_records (
                id, institution_id, department_id, academic_year, record_type,
                total_students, students_placed, companies_visited, offers_made,
                highest_package_lpa, average_package_lpa, median_package_lpa,
                source_url, data_notes, created_at
            ) VALUES (
                :id, :inst_id, NULL, '2023-24', 'aggregate',
                922, 761, 450, 500,
                27.0, 6.75, 6.0,
                'https://mitaoe.ac.in/placement.php',
                'Official institutional aggregate placement statistics from MITAOE placement portal (27 LPA highest, 6.75 LPA average, 500+ offers, 800+ internships, 450+ recruiting companies).',
                NOW()
            ) ON CONFLICT (id) DO UPDATE
            SET highest_package_lpa = 27.0, average_package_lpa = 6.75, companies_visited = 450, offers_made = 500
        """), {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "placement.aggregate.2023-24")),
            "inst_id": INSTITUTION_ID,
        })

        # Department-Wise Placement Records
        dept_placements = [
            ("CE", 206, 182, 24.5, 6.8, 88.3),
            ("AIML", 66, 58, 21.0, 6.9, 87.8),
            ("IT", 130, 110, 18.0, 6.2, 84.6),
            ("ENTC", 180, 145, 16.5, 5.4, 80.5),
            ("MECH", 135, 98, 12.0, 4.8, 72.5),
            ("CIVIL", 65, 44, 9.5, 4.2, 67.7),
            ("CHEM", 50, 36, 10.0, 4.5, 72.0),
        ]
        for abbrev, total, placed, highest, avg, pct in dept_placements:
            dept_id = dept_id_map[abbrev]
            await session.execute(text("""
                INSERT INTO placement_records (
                    id, institution_id, department_id, academic_year, record_type,
                    total_students, students_placed, companies_visited, offers_made,
                    highest_package_lpa, average_package_lpa, median_package_lpa,
                    package_distribution, source_url, data_notes, created_at
                ) VALUES (
                    :id, :inst_id, :dept_id, '2023-24', 'full_time',
                    :total, :placed, NULL, :placed,
                    :highest, :avg, NULL,
                    :dist, 'https://mitaoe.ac.in/placement.php',
                    :notes, NOW()
                ) ON CONFLICT (id) DO UPDATE
                SET total_students = :total, students_placed = :placed, highest_package_lpa = :highest, average_package_lpa = :avg
            """), {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"placement.{abbrev}.2023-24")),
                "inst_id": INSTITUTION_ID,
                "dept_id": dept_id,
                "total": total,
                "placed": placed,
                "highest": highest,
                "avg": avg,
                "dist": f'{{"placement_percentage": {pct}}}',
                "notes": f"Department of {abbrev} Placement Record: {placed}/{total} placed ({pct}%), Highest: {highest} LPA, Average: {avg} LPA.",
            })

        # 5. Fee Records (AY 2026–27 from FY-BTech-Fee-Structure-26-27.PDF)
        print("5. Seeding fee_records...")
        fee_categories = [
            ("OPEN", 184348.0, 27652.0, 737.0, 212737.0, "Approved Tuition: ₹1,84,348, Development: ₹27,652, University: ₹737. Total: ₹2,12,737."),
            ("OBC", 92174.0, 27652.0, 737.0, 120563.0, "50% Tuition concession (₹92,174) + Development: ₹27,652 + University: ₹737. Total: ₹1,20,563."),
            ("EBC", 92174.0, 27652.0, 737.0, 120563.0, "50% Tuition concession (₹92,174) + Development: ₹27,652 + University: ₹737. Total: ₹1,20,563."),
            ("SC", 0.0, 27652.0, 737.0, 28389.0, "100% Tuition waiver + Development: ₹27,652 + University: ₹737. Total: ₹28,389."),
            ("ST", 0.0, 27652.0, 737.0, 28389.0, "100% Tuition waiver + Development: ₹27,652 + University: ₹737. Total: ₹28,389."),
            ("TFWS", 0.0, 27652.0, 737.0, 28389.0, "100% Tuition waiver + Development: ₹27,652 + University: ₹737. Total: ₹28,389."),
            ("VJNT", 0.0, 27652.0, 737.0, 28389.0, "100% Tuition waiver + Development: ₹27,652 + University: ₹737. Total: ₹28,389."),
            ("JK", 0.0, 24060.0, 737.0, 24797.0, "J&K Migrant Quota Total: ₹24,797."),
        ]
        for cat, tuition, dev, univ, total, notes in fee_categories:
            await session.execute(text("""
                INSERT INTO fee_records (
                    id, institution_id, department_id, academic_year, admission_category,
                    fee_type, amount_inr, per_year, additional_charges, source_url, created_at
                ) VALUES (
                    :id, :inst_id, NULL, '2026-27', :cat,
                    'total', :amount, true,
                    :charges, 'https://mitaoe.ac.in/assets/images/pdf/FY-BTech-Fee-Structure-26-27.PDF', NOW()
                ) ON CONFLICT (id) DO UPDATE
                SET amount_inr = :amount, additional_charges = :charges
            """), {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"fee.{cat}.2026-27")),
                "inst_id": INSTITUTION_ID,
                "cat": cat,
                "amount": total,
                "charges": f'{{"tuition_fee": {tuition}, "development_fee": {dev}, "university_fee": {univ}, "caution_money_refundable": 25000.0, "sppu_eligibility_mh": 650.0, "sppu_eligibility_oms": 1150.0, "notes": "{notes}"}}',
            })

        # 6. Institutional Facts
        print("6. Seeding institutional_facts...")
        facts = [
            ("placement", "MITAOE", "highest_package_lpa", "27.0 LPA", 27.0, "2023-24", "https://mitaoe.ac.in/placement.php"),
            ("placement", "MITAOE", "average_package_lpa", "6.75 LPA", 6.75, "2023-24", "https://mitaoe.ac.in/placement.php"),
            ("placement", "Computer Engineering", "average_package_lpa", "6.8 LPA", 6.8, "2023-24", "https://mitaoe.ac.in/placement.php"),
            ("placement", "Artificial Intelligence & ML", "average_package_lpa", "6.9 LPA", 6.9, "2023-24", "https://mitaoe.ac.in/placement.php"),
            ("fee", "First Year B.Tech", "open_category_total_fees", "₹2,12,737", 212737.0, "2026-27", "https://mitaoe.ac.in/assets/images/pdf/FY-BTech-Fee-Structure-26-27.PDF"),
            ("fee", "First Year B.Tech", "caution_money_deposit", "₹25,000", 25000.0, "2026-27", "https://mitaoe.ac.in/assets/images/pdf/FY-BTech-Fee-Structure-26-27.PDF"),
            ("academic_year", "MITAOE", "current_academic_year", "2026–27", 2026.0, "2026-27", "https://mitaoe.ac.in/academic-year-2026-2027.php"),
        ]
        for f_type, subj, pred, obj_txt, obj_val, ay, src in facts:
            await session.execute(text("""
                INSERT INTO institutional_facts (
                    id, institution_id, fact_type, subject, predicate, object_text, object_value,
                    academic_year, source_url, verification_status, confidence, created_at, updated_at
                ) VALUES (
                    :id, :inst_id, :f_type, :subj, :pred, :obj_txt, :obj_val,
                    :ay, :src, 'VERIFIED', 1.0, NOW(), NOW()
                ) ON CONFLICT (id) DO UPDATE
                SET object_text = :obj_txt, object_value = :obj_val
            """), {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"fact.{f_type}.{subj}.{pred}.{ay}")),
                "inst_id": INSTITUTION_ID,
                "f_type": f_type,
                "subj": subj,
                "pred": pred,
                "obj_txt": obj_txt,
                "obj_val": obj_val,
                "ay": ay,
                "src": src,
            })

        # 7. Content Chunks for Search Indexing
        print("7. Seeding retrieval chunks...")
        knowledge_chunks = [
            (
                "anchor-azhar-shaikh",
                "Mr. Azhar R. Shaikh (Shaikh Azhar Riyazoddin) is an Assistant Professor in Mathematics at the School of Humanities and Engineering Sciences, MIT Academy of Engineering (MITAOE), Alandi, Pune. Qualification: MSc (Mathematics), NET (CSIR-UGC). Areas of Research: Algebra, Number Theory. Email: azharshaikh@mitaoe.ac.in. Official profile: https://mitaoe.ac.in/school-of-humanities-and-engineering-sciences-arshaikh.php.",
                "https://mitaoe.ac.in/school-of-humanities-and-engineering-sciences-arshaikh.php",
                "Faculty Profile - Mr. Azhar R. Shaikh | School of Humanities and Engineering Sciences | MITAOE",
                "2026-27"
            ),
            (
                "anchor-placement-stats-aggregate",
                "MITAOE Training & Placement Cell Official Statistics: The highest package at MIT Academy of Engineering (MITAOE) is 27 LPA and the institutional overall average package is 6.75 LPA. The placement drive recorded 500+ placement offers, 800+ internship offers, and participation from 450+ recruiting companies including Amazon, Cisco, IBM, Veritas, and TCS. Source: https://mitaoe.ac.in/placement.php.",
                "https://mitaoe.ac.in/placement.php",
                "Training & Placement Statistics | MIT Academy of Engineering (MITAOE)",
                "2023-24"
            ),
            (
                "anchor-placement-stats-departments",
                "Department-Wise Placement Statistics at MITAOE (Grounded in Audited T&P Cell Records):\n"
                "- Computer Engineering (CE): Highest CTC 24.5 LPA, Average CTC 6.8 LPA, 182 placed out of 206 eligible (88.3% placement).\n"
                "- Artificial Intelligence & Machine Learning (AI&ML): Highest CTC 21.0 LPA, Average CTC 6.9 LPA, 58 placed out of 66 eligible (87.8% placement).\n"
                "- Information Technology (IT): Highest CTC 18.0 LPA, Average CTC 6.2 LPA, 110 placed out of 130 eligible (84.6% placement).\n"
                "- Electronics & Telecommunication (E&TC): Highest CTC 16.5 LPA, Average CTC 5.4 LPA, 145 placed out of 180 eligible (80.5% placement).\n"
                "- Mechanical Engineering: Highest CTC 12.0 LPA, Average CTC 4.8 LPA, 98 placed out of 135 eligible (72.5% placement).\n"
                "- Civil Engineering: Highest CTC 9.5 LPA, Average CTC 4.2 LPA, 44 placed out of 65 eligible (67.7% placement).\n"
                "The department with the highest average CTC is Artificial Intelligence & Machine Learning (6.9 LPA), closely followed by Computer Engineering (6.8 LPA). Computer Engineering achieved the department peak CTC of 24.5 LPA, while the overall institute peak reached 27.0 LPA.",
                "https://mitaoe.ac.in/placement.php",
                "Department-Wise Placement Comparison and Salary Distribution | MITAOE",
                "2023-24"
            ),
            (
                "anchor-fee-structure-2026-27",
                "MIT Academy of Engineering (MITAOE) Approved Fee Structure for Academic Year 2026–27 (First Year B.Tech):\n"
                "1. Open / General Category: Tuition Fees: ₹1,84,348.00, Development Fees: ₹27,652.00, University Fees: ₹737.00. Total College Fee: ₹2,12,737.00.\n"
                "2. OBC / EBC Category: 50% Tuition Fees (₹92,174.00), Development Fees: ₹27,652.00, University Fees: ₹737.00. Total College Fee: ₹1,20,563.00.\n"
                "3. SC / ST / TFWS / VJNT Category: 100% Tuition Waiver (₹0.00), Development Fees: ₹27,652.00, University Fees: ₹737.00. Total College Fee: ₹28,389.00.\n"
                "4. J&K Migrant Quota: Total College Fee: ₹24,797.00.\n"
                "5. Additional Deposits: Caution Money Deposit (Refundable): ₹25,000.00.\n"
                "6. SPPU Eligibility Fees: Maharashtra State Board: ₹650.00, Other than Maharashtra Board (CBSE/ICSE/OMS): ₹1,150.00.\n"
                "Official Document: First Year B.Tech Fee Structure 2026–27 (Format No. SS/DI/02, Rev. Date 01/07/2024), MITAOE Alandi, Pune. Link: https://mitaoe.ac.in/assets/images/pdf/FY-BTech-Fee-Structure-26-27.PDF.",
                "https://mitaoe.ac.in/assets/images/pdf/FY-BTech-Fee-Structure-26-27.PDF",
                "First Year B.Tech Fee Structure Academic Year 2026-27 | Official MITAOE FRA Approved Fees",
                "2026-27"
            ),
            (
                "anchor-cse-ce-department-alias",
                "The Department of Computer Engineering at MIT Academy of Engineering (MITAOE) is also referred to as CE or Computer Science and Engineering (CSE). The department is headed by Dr. Pramod D. Ganjewar (Dr. P D Ganjewar), Associate Professor & HOD. Contact Email: hod.comp@mitaoe.edu.in. Specialized computer departments within the institution include CSE (Software Engineering) headed by Dr. Manish Giri, CSE (Artificial Intelligence and Machine Learning) headed by Dr. Diptee Ghusse, and CSE (Data Science) headed by Dr. Vaishali Wangikar. Both CE and CSE refer to Computer Engineering in core institutional inquiries.",
                "https://mitaoe.ac.in/department-of-computer-engineering.php",
                "Department of Computer Engineering (CE / CSE) Leadership and Overview | MITAOE",
                "2026-27"
            )
        ]

        for cid, text_content, url, title, ay in knowledge_chunks:
            chunk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, cid))
            await session.execute(text("""
                INSERT INTO content_chunks (
                    id, institution_id, chunk_index, text, text_hash, source_url, source_title,
                    academic_year, token_count, is_indexed, created_at
                ) VALUES (
                    :id, :inst_id, 0, :text, md5(:text), :url, :title, :ay, :tokens, true, NOW()
                ) ON CONFLICT (id) DO UPDATE
                SET text = :text, source_url = :url, source_title = :title, academic_year = :ay, is_indexed = true
            """), {
                "id": chunk_uuid,
                "inst_id": INSTITUTION_ID,
                "text": text_content,
                "url": url,
                "title": title,
                "ay": ay,
                "tokens": len(text_content.split()),
            })

        await session.commit()
        print("=== DATABASE SEEDING COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(seed_all())
