import httpx
from bs4 import BeautifulSoup
import re

client = httpx.Client(verify=False, timeout=15.0, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

for name, url in [
    ('AI & ML', 'https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php'),
    ('Data Science', 'https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php'),
    ('Director', 'https://mitaoe.ac.in/mitaoe-academic-council.php')
]:
    r = client.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    print(f"\n============================\n{name}: {url}")
    for el in soup.find_all(['div', 'p', 'h3', 'h4', 'td']):
        t = el.get_text(" ", strip=True)
        if any(w in t.lower() for w in ['hod', 'head of department', 'director']) and len(t) < 180:
            print(f"[{el.name}] {t}")
