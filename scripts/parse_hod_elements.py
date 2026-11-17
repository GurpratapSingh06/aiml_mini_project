import httpx
from bs4 import BeautifulSoup
import re

client = httpx.Client(verify=False, timeout=15.0, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

urls = [
    ('Computer Engineering', 'https://mitaoe.ac.in/department-of-computer-engineering.php'),
    ('Information Technology', 'https://mitaoe.ac.in/department-of-information-technology.php'),
    ('Software Engineering', 'https://mitaoe.ac.in/department-of-software-engineering.php'),
    ('AI & ML', 'https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php'),
    ('Data Science', 'https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php'),
    ('Mechanical', 'https://mitaoe.ac.in/department-of-mechanical-engineering.php'),
    ('Civil', 'https://mitaoe.ac.in/department-of-civil-engineering.php'),
    ('Chemical', 'https://mitaoe.ac.in/department-of-chemical-engineering.php'),
    ('E&TC', 'https://mitaoe.ac.in/department-of-electronics-and-telecomminication-engineering.php'),
]

for dept, url in urls:
    r = client.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    print(f"\n====================\nDepartment: {dept}")
    # Search for any text containing HOD or Head
    for el in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'strong', 'td']):
        t = el.get_text(" ", strip=True)
        if re.search(r'\b(HOD|Head of Department)\b', t, re.I) and len(t) < 180:
            # check parent or surrounding text
            parent = el.parent.get_text(" | ", strip=True) if el.parent else ""
            print(f"  El [{el.name}]: {t}")
            if len(parent) < 300 and parent != t:
                print(f"    Parent: {parent}")
