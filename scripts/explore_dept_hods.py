import httpx
from bs4 import BeautifulSoup
import re

client = httpx.Client(verify=False, timeout=15.0, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

dept_urls = [
    'https://mitaoe.ac.in/department-of-computer-engineering.php',
    'https://mitaoe.ac.in/department-of-information-technology.php',
    'https://mitaoe.ac.in/department-of-software-engineering.php',
    'https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php',
    'https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php',
    'https://mitaoe.ac.in/department-of-chemical-engineering.php',
    'https://mitaoe.ac.in/department-of-civil-engineering.php',
    'https://mitaoe.ac.in/department-of-electronics-and-telecomminication-engineering.php',
    'https://mitaoe.ac.in/department-of-mechanical-engineering.php',
    'https://mitaoe.ac.in/Department-of-Electronics-and-Computer-Engineering.php',
    'https://mitaoe.ac.in/about-mitaoe.php',
    'https://mitaoe.ac.in/mitaoe-academic-calendar.php',
    'https://mitaoe.ac.in/mitaoe-academic-council.php',
]

for url in dept_urls:
    try:
        r = client.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else ""
        text = soup.get_text(separator=' ', strip=True)
        # Search for HOD, Head, Director, Principal
        hod_snippets = []
        for match in re.finditer(r'(?:head of (?:the )?department|hod|director|dean|principal)[^.\n]{1,120}', text, re.IGNORECASE):
            hod_snippets.append(match.group(0))
        print(f"\n============================\nURL: {url}\nTitle: {title}")
        print("HOD / Leadership mentions:")
        for s in hod_snippets[:5]:
            print("  - ", s)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
