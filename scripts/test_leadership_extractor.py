import re

test_cases = [
    ("The Department of Computer Engineering at MIT Academy of Engineering (MITAOE) is headed by Dr. Sandip A. Gade. Dr. Sandip A. Gade is the Head of Department (HOD) for Computer Engineering.", "Computer Engineering", "Dr. Sandip A. Gade"),
    ("Dr. P D Ganjewar  , Associate Professor & HOD Computer Engineering , Contact No.:020-30253661 Ext.: 1165 / 1052 Email – hod.comp@mitaoe.edu.in", "Computer Engineering", "Dr. P D Ganjewar"),
    ("1 Dr. Pramod D. Ganjewar Chairman Associate Professor & HOD Computer Engineering", "Computer Engineering", "Dr. Pramod D. Ganjewar"),
    ("Dr. Santosh Warpe            , HOD , Information Technology Email – hodit@mitaoe.ac.in", "Information Technology", "Dr. Santosh Warpe"),
    ("Dr Manish Giri , HOD , Department of Computer Engineering (Software Engineering) Email – hodsoftengg@mitaoe.ac.in", "Software Engineering", "Dr Manish Giri"),
    ("Dr. Diptee Ghusse(Chikmurge), HOD , Computer Science & Engineering (Artificial Intelligence and Machine Learning) Email – hod.aiml@mitaoe.edu.in", "Artificial Intelligence and Machine Learning", "Dr. Diptee Ghusse(Chikmurge)"),
    ("Dr. V.C.Wangikar  , HOD , Computer Science & Engineering (Data Science) Email – hod.datasci@mitaoe.edu.in", "Data Science", "Dr. V.C.Wangikar"),
    ("1 Dr. Vaishali Wangikar Chairman Associate Professor & HOD, Computer Science and Engineering (Data Science)", "Data Science", "Dr. Vaishali Wangikar"),
    ("Dr. S. P. Shewale , Associate Professor & HOD, Department of Chemical Engineering Phone : 020-30253615/ 30253500 Ext. 1045 Email: hod.chem@mitaoe.edu.in", "Chemical Engineering", "Dr. S. P. Shewale"),
    ("Dr. D. Y.Sakhare , Professor and HOD (E&TC) Contact No: Tel:(020) 30253500 Ext: 1096 Email – hodentc@mitaoe.ac.in", "Electronics and Telecommunication Engineering", "Dr. D. Y.Sakhare"),
    ("Dr. Nilesh. U. Mate, Professor & HOD, Department of Civil Engineering Contact Number – 020-30253500 Ext. 1261 Email – hodcivil@mitaoe.ac.in", "Civil Engineering", "Dr. Nilesh. U. Mate"),
    ("1 Dr. Maya Charde Chairman Associate Professor and HOD, Department of Mechanical Engineering", "Mechanical Engineering", "Dr. Maya Charde"),
    ("Dr. Yogesh. J. Bhalerao Chairman, Director, MIT Academy of Engineering (MITAOE)", "Director", "Dr. Yogesh. J. Bhalerao"),
    ("Dr. Mahesh D. Goudar Member Secretary, Officiating Director & Professor, MIT Academy of Engineering", "Officiating Director", "Dr. Mahesh D. Goudar"),
]

DEPT_NORMALIZATION = {
    "software": "Software Engineering",
    "software engineering": "Software Engineering",
    "data science": "Data Science",
    "datasci": "Data Science",
    "artificial intelligence": "Artificial Intelligence and Machine Learning",
    "machine learning": "Artificial Intelligence and Machine Learning",
    "ai & ml": "Artificial Intelligence and Machine Learning",
    "ai and ml": "Artificial Intelligence and Machine Learning",
    "aiml": "Artificial Intelligence and Machine Learning",
    "computer engineering": "Computer Engineering",
    "computer": "Computer Engineering",
    "comp": "Computer Engineering",
    "computer science": "Computer Science and Engineering",
    "cse": "Computer Science and Engineering",
    "information technology": "Information Technology",
    "it": "Information Technology",
    "entc": "Electronics and Telecommunication Engineering",
    "e&tc": "Electronics and Telecommunication Engineering",
    "electronics & telecommunication": "Electronics and Telecommunication Engineering",
    "mechanical": "Mechanical Engineering",
    "mech": "Mechanical Engineering",
    "civil": "Civil Engineering",
    "chemical": "Chemical Engineering",
    "chem": "Chemical Engineering",
    "humanities": "Humanities and Engineering Sciences",
    "design": "School of Design",
}

def normalize_dept(raw):
    cleaned = raw.strip().lower()
    cleaned = re.sub(r"\b(department\s+of|dept\s+of|department|dept|school\s+of)\b", "", cleaned).strip()
    for k, v in DEPT_NORMALIZATION.items():
        if k in cleaned:
            return v
    return raw.strip().title()

def extract_leadership(text):
    results = []
    # Clean text
    clean = re.sub(r"\s+", " ", text).strip()
    # Remove leading numbering like "1 "
    clean = re.sub(r"^\d+\s+", "", clean)

    # 1. Check for Director / Officiating Director
    dir_match = re.search(
        r"((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z\.\s]+?)\s+(?:Chairman|Member\s+Secretary)?\s*,?\s*(Director|Officiating\s+Director|Deputy\s+Director)\s*,?\s*(?:MITAOE|MIT\s+Academy\s+of\s+Engineering)?",
        clean,
        re.I
    )
    if dir_match:
        name = dir_match.group(1).strip()
        role = dir_match.group(2).strip()
        results.append((name, role, "MITAOE"))

    # 2. Check for HOD with Name prefix
    # e.g., "Dr. P D Ganjewar , Associate Professor & HOD Computer Engineering"
    # or "1 Dr. Maya Charde Chairman Associate Professor and HOD, Department of Mechanical Engineering"
    hod_name_first = re.search(
        r"((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z\.\(\)\s]+?)\s*(?:,|\s+Chairman|\s+Member)?\s*(?:(?:Associate|Sr\.\s+Assistant|Assistant)?\s*Professor)?\s*(?:and|&)?\s*(?:HOD|HoD|Head\s+of\s+(?:the\s+)?Department)\s*(?:of|,)?\s*([A-Za-z\s&–\(\)]+?)(?:Contact|Email|Phone|\.|\n|$)",
        clean,
        re.I
    )
    if hod_name_first:
        name = hod_name_first.group(1).strip()
        raw_dept = hod_name_first.group(2).strip()
        dept = normalize_dept(raw_dept)
        results.append((name, "Head of Department", dept))

    # 3. Check for "headed by <Name>"
    headed_by = re.search(
        r"(?:department\s+of\s+)?([A-Za-z\s&–\(\)]+?)(?:\s+at\s+MITAOE|\s+at\s+MIT\s+Academy\s+of\s+Engineering)?\s+is\s+headed\s+by\s+((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z\.\(\)\s]+?)(?:\.|\n|$)",
        clean,
        re.I
    )
    if headed_by:
        raw_dept = headed_by.group(1).strip()
        name = headed_by.group(2).strip()
        dept = normalize_dept(raw_dept)
        results.append((name, "Head of Department", dept))

    # 4. Check for "<Name> is the Head of Department (HOD) for <Dept>"
    hod_for = re.search(
        r"((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z\.\(\)\s]+?)\s+is\s+the\s+Head\s+of\s+Department\s*(?:\(HOD\))?\s+(?:for|of)\s+([A-Za-z\s&–\(\)]+?)(?:\.|\n|$)",
        clean,
        re.I
    )
    if hod_for:
        name = hod_for.group(1).strip()
        raw_dept = hod_for.group(2).strip()
        dept = normalize_dept(raw_dept)
        results.append((name, "Head of Department", dept))

    return results

for text, exp_dept, exp_person in test_cases:
    res = extract_leadership(text)
    if res:
        print(f"SUCCESS: {res[0][0]} | Role: {res[0][1]} | Dept/Org: {res[0][2]}")
    else:
        print(f"FAILED on: {text}")
