import httpx
from bs4 import BeautifulSoup

client = httpx.Client(verify=False, timeout=15.0, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

for page in ['mitaoe-academic-calendar.php', 'Examination-Time-Table.php', 'downloads.php']:
    url = f'https://mitaoe.ac.in/{page}'
    r = client.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    print(f"\n============================\nURL: {url}")
    print("Page Title:", soup.title.string.strip() if soup.title else "")
    # Find links to PDFs and calendar tables
    for a in soup.find_all('a', href=True):
        href = a['href']
        t = a.get_text(" ", strip=True)
        if any(w in href.lower() or w in t.lower() for w in ['calendar', 'timetable', 'time-table', 'exam', '202', 'ay', 'term']):
            print(f"  Link: '{t}' -> {href}")
    for el in soup.find_all(['h1', 'h2', 'h3', 'h4', 'table']):
        text = el.get_text(" ", strip=True)
        if any(w in text.lower() for w in ['academic year', '2026', '2025', '2024', 'term', 'semester']):
            print(f"  El [{el.name}]: {text[:150]}")
