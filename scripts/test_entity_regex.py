import re

test_cases = [
    ("The Department of Computer Engineering at MIT Academy of Engineering (MITAOE) is headed by Dr. Sandip A. Gade. Dr. Sandip A. Gade is the Head of Department (HOD) for Computer Engineering.", "Computer Engineering", "Dr. Sandip A. Gade"),
    ("Dr. P D Ganjewar , Associate Professor & HOD Computer Engineering , Contact No.:020-30253661 Ext.: 1165 / 1052 Email – hod.comp@mitaoe.edu.in", "Computer Engineering", "Dr. P D Ganjewar"),
    ("Dr. Santosh Warpe , HOD , Information Technology Email – hodit@mitaoe.ac.in", "Information Technology", "Dr. Santosh Warpe"),
    ("Dr Manish Giri , HOD , Department of Computer Engineering (Software Engineering) Email – hodsoftengg@mitaoe.ac.in", "Software Engineering", "Dr Manish Giri"),
    ("Dr. Diptee Ghusse(Chikmurge), HOD , Computer Science & Engineering (Artificial Intelligence and Machine Learning) Email – hod.aiml@mitaoe.edu.in", "Artificial Intelligence and Machine Learning", "Dr. Diptee Ghusse(Chikmurge)"),
    ("Dr. V.C.Wangikar , HOD , Computer Science & Engineering (Data Science) Email – hod.datasci@mitaoe.edu.in", "Data Science", "Dr. V.C.Wangikar"),
    ("Dr. S. P. Shewale , Associate Professor & HOD, Department of Chemical Engineering", "Chemical Engineering", "Dr. S. P. Shewale"),
    ("Dr. D. Y.Sakhare , Professor and HOD (E&TC)", "Electronics and Telecommunication Engineering", "Dr. D. Y.Sakhare"),
    ("Dr. Nilesh. U. Mate, Professor & HOD, Department of Civil Engineering", "Civil Engineering", "Dr. Nilesh. U. Mate"),
    ("Dr. Maya Charde , Chairman , Associate Professor and HOD, Department of Mechanical Engineering", "Mechanical Engineering", "Dr. Maya Charde"),
    ("Dr. Yogesh. J. Bhalerao Chairman, Director, MIT Academy of Engineering (MITAOE)", "MITAOE", "Dr. Yogesh. J. Bhalerao"),
    ("Dr. Mahesh D. Goudar Member Secretary, Officiating Director & Professor, MIT Academy of Engineering", "MITAOE", "Dr. Mahesh D. Goudar"),
]

NAME_PREFIX = r"(?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?|Shri|Smt\.?)"
PERSON_NAME = r"(?:(?:" + NAME_PREFIX + r"\s+)?(?:[A-Z][A-Za-z0-9\.\(\)]*(?:\s+[A-Z0-9][A-Za-z0-9\.\(\)]*){1,4}))"

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
    "computer": "Computer Engineering",
    "comp": "Computer Engineering",
    "computer engineering": "Computer Engineering",
    "computer science": "Computer Science and Engineering",
    "cse": "Computer Science and Engineering",
    "information technology": "Information Technology",
    "it": "Information Technology",
    "entc": "Electronics and Telecommunication Engineering",
    "e&tc": "Electronics and Telecommunication Engineering",
    "electronics": "Electronics and Telecommunication Engineering",
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

patterns = [
    # Pattern 1: Name followed by HOD and department
    re.compile(
        r"(" + PERSON_NAME + r")\s*,\s*(?:[A-Za-z\.\s&]+)?(?:HOD|Head\s+of\s+(?:the\s+)?Department)\s*(?:of|,|–|-)?\s*([A-Za-z\s&–\(\)]+?)(?:Email|Contact|Phone|\.|\n|$)",
        re.I
    ),
    # Pattern 2: Name followed by Chairman/Member ... HOD, Department
    re.compile(
        r"(" + PERSON_NAME + r")\s+(?:Chairman|Member\s+Secretary|Member)?\s*,?\s*(?:Associate\s+Professor|Sr\.\s+Assistant\s+Professor|Professor|Assistant\s+Professor)?\s*(?:and|&)?\s*(?:HOD|HoD|Head)\s*(?:of\s+Department)?,?\s*([A-Za-z\s&–\(\)]+?)(?:Email|Contact|Phone|\.|\n|$)",
        re.I
    ),
    # Pattern 3: is headed by Name
    re.compile(
        r"([A-Za-z\s&–\(\)]+?)\s+(?:is\s+)?(?:headed\s+by|heads)\s+(" + PERSON_NAME + r")",
        re.I
    ),
    # Pattern 4: is the Head of Department for Department
    re.compile(
        r"(" + PERSON_NAME + r")\s+is\s+the\s+(?:Head\s+of\s+Department|HOD)\s*(?:\(HOD\))?\s+(?:for|of)\s+([A-Za-z\s&–\(\)]+?)(?:\.|\n|$)",
        re.I
    ),
    # Pattern 5: Director patterns
    re.compile(
        r"(" + PERSON_NAME + r")\s*(?:Chairman|Member\s+Secretary)?\s*,?\s*(Director|Officiating\s+Director|Deputy\s+Director)\s*,?\s*([A-Za-z\s&–\(\)]+?)(?:\.|\n|$)",
        re.I
    ),
]

for text, exp_dept, exp_person in test_cases:
    found = False
    for pat in patterns:
        m = pat.search(text)
        if m:
            g1, g2 = m.group(1).strip(), m.group(2).strip()
            print(f"MATCH: '{text[:60]}...' -> g1: '{g1}', g2: '{g2}'")
            found = True
            break
    if not found:
        print(f"FAILED on: '{text}'")
