import httpx
from bs4 import BeautifulSoup
import re

client = httpx.Client(verify=False, timeout=15.0, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

def check_depts():
    r = client.get('https://mitaoe.ac.in/mitaoe-academic-departments.php')
    soup = BeautifulSoup(r.text, 'html.parser')
    print("--- Departments Page Title:", soup.title.string if soup.title else "")
    # Find all department links
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        if any(w in href.lower() or w in text.lower() for w in ['department', 'engineering', 'school', 'computer', 'it', 'chemical', 'mechanical', 'civil', 'electronics', 'design']):
            links.add((text, href))
    for t, h in sorted(links):
        print(f"Dept link: {t} -> {h}")

if __name__ == '__main__':
    check_depts()
