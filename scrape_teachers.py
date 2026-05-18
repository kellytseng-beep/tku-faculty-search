"""
Scraper for Tamkang University English Department teacher profiles
from teacher.tku.edu.tw
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE = "https://teacher.tku.edu.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

TEACHERS = [
    {"name": "蔡振興", "nameEn": "TSAI CHEN-HSING",   "rank": "教授",       "uid": "t711706"},
    {"name": "林怡弟", "nameEn": "LIN YI-TI",           "rank": "教授",       "uid": "t991312"},
    {"name": "陳佩筠", "nameEn": "PEI-YUN CHEN",        "rank": "教授",       "uid": "t987227"},
    {"name": "曾郁景", "nameEn": "YU-CHING TSENG",      "rank": "教授",       "uid": "t986267"},
    {"name": "羅艾琳", "nameEn": "IRIS RALPH",           "rank": "教授",       "uid": "t985505"},
    {"name": "小澤自然","nameEn": "SHIZEN OZAWA",        "rank": "教授",       "uid": "t968359"},
    {"name": "吳怡芬", "nameEn": "I-FEN WU",             "rank": "副教授",     "uid": "t992807"},
    {"name": "涂銘宏", "nameEn": "MING HUNG TU",         "rank": "副教授",     "uid": "t906169"},
    {"name": "張慈珊", "nameEn": "TZU-SHAN CHANG",       "rank": "副教授",     "uid": "t903772"},
    {"name": "張雅慧", "nameEn": "YEA HUEY CHANG",       "rank": "副教授",     "uid": "t905663"},
    {"name": "齊嵩齡", "nameEn": "CHYI SONG-LING",       "rank": "副教授",     "uid": "t901102"},
    {"name": "蔡瑞敏", "nameEn": "JUI-MIN TSAI",         "rank": "副教授",     "uid": "t980327"},
    {"name": "錢欽昭", "nameEn": "CHIN-JAU CHYAN",       "rank": "副教授",     "uid": "t986717"},
    {"name": "薛玉政", "nameEn": "SIEH YU-CHENG",        "rank": "副教授",     "uid": "t986722"},
    {"name": "鄧秋蓉", "nameEn": "DENG CHIOU-RUNG",      "rank": "副教授",     "uid": "t981147"},
    {"name": "郭家珍", "nameEn": "KUO CHIA-CHEN",        "rank": "副教授",     "uid": "t969421"},
    {"name": "李佳盈", "nameEn": "JIA-YING LEE",         "rank": "副教授",     "uid": "t960216"},
    {"name": "林銘輝", "nameEn": "LIN MING HUEI",        "rank": "副教授",     "uid": "t966407"},
    {"name": "張介英", "nameEn": "CHANG CHIEH-YING",     "rank": "副教授",     "uid": "t932481"},
    {"name": "劉佩勳", "nameEn": "LIU PEI-HSUN",         "rank": "副教授",     "uid": "t953096"},
    {"name": "王慧娟", "nameEn": "HUI-CHUAN WANG",       "rank": "約聘副教授", "uid": "t992887"},
    {"name": "吳瑜雲", "nameEn": "WU YU-YUN",            "rank": "助理教授",   "uid": "t741301"},
    {"name": "包俊傑", "nameEn": "BROWN IAIN KELSALL",   "rank": "助理教授",   "uid": "t988958"},
    {"name": "王蔚婷", "nameEn": "GUTIERREZ JANNETTE WANG","rank": "助理教授", "uid": "t988809"},
    {"name": "莊晏甄", "nameEn": "YEN-CHEN CHUANG",      "rank": "助理教授",   "uid": "t981657"},
    {"name": "雷凱",   "nameEn": "GUY MATTHEW REDMER",   "rank": "助理教授",   "uid": "t969963"},
    {"name": "吳凱書", "nameEn": "WU KAI-SU",            "rank": "助理教授",   "uid": "t939455"},
    {"name": "熊婷惠", "nameEn": "HSIUNG TING-HUI",      "rank": "助理教授",   "uid": "t936737"},
    {"name": "陳家倩", "nameEn": "CHEN CHIA-CHIEN",      "rank": "助理教授",   "uid": "t931891"},
    {"name": "林嘉鴻", "nameEn": "CHIA-HUNG LIN",        "rank": "助理教授",   "uid": "t953007"},
]

sess = requests.Session()
sess.headers.update(HEADERS)


def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = sess.get(url, timeout=15)
            r.encoding = "utf-8"
            if "系統似乎無法正常運作" in r.text:
                print(f"  [server down] {url}")
                return None
            return r.text
        except Exception as e:
            print(f"  [err {i+1}] {url}: {e}")
            time.sleep(2)
    return None


def parse_table_rows(soup, table_id=None):
    """Extract rows from the first data table on the page."""
    tbl = soup.find("table", id=table_id) if table_id else soup.find("table")
    if not tbl:
        return []
    rows = []
    for tr in tbl.find_all("tr")[1:]:  # skip header
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if any(cells):
            rows.append(cells)
    return rows


def get_email(uid):
    html = fetch(f"{BASE}/PsnProfile.aspx?u={uid}")
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            return href[7:]
    # fallback: text pattern
    m = re.search(r"[\w.\-]+@mail\.tku\.edu\.tw", html)
    return m.group(0) if m else ""


def get_courses(uid):
    """Return list of current course names."""
    html = fetch(f"{BASE}/PsnCat.aspx?c=2&u={uid}")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    courses = []
    # current courses table usually has class or is first table
    for tbl in soup.find_all("table"):
        for tr in tbl.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) >= 2:
                name = tds[0].get_text(strip=True)
                if name and len(name) > 1:
                    courses.append(name)
    # deduplicate preserving order
    seen = set()
    result = []
    for c in courses:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result[:8]  # cap at 8


def get_publications(uid, limit=5):
    """Return most recent publications (titles)."""
    html = fetch(f"{BASE}/PsnCat.aspx?c=4&u={uid}")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    pubs = []
    for tbl in soup.find_all("table"):
        for tr in tbl.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) >= 2:
                year = tds[0].get_text(strip=True)
                title = tds[1].get_text(strip=True)
                if title and len(title) > 3:
                    pubs.append({"year": year, "title": title})
    # sort by year descending and take most recent
    pubs.sort(key=lambda x: x["year"], reverse=True)
    return pubs[:limit]


def get_research(uid, limit=5):
    """Return most recent research projects."""
    html = fetch(f"{BASE}/PsnCat.aspx?c=3&u={uid}")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    projects = []
    for tbl in soup.find_all("table"):
        for tr in tbl.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) >= 2:
                year = tds[0].get_text(strip=True)
                title = tds[1].get_text(strip=True)
                if title and len(title) > 3:
                    projects.append({"year": year, "title": title})
    projects.sort(key=lambda x: x["year"], reverse=True)
    return projects[:limit]


def scrape_all():
    results = []
    total = len(TEACHERS)
    for i, t in enumerate(TEACHERS, 1):
        uid = t["uid"]
        print(f"[{i:02d}/{total}] {t['name']} ({uid})")

        email = get_email(uid)
        print(f"  email: {email}")
        time.sleep(0.5)

        courses = get_courses(uid)
        print(f"  courses: {len(courses)}")
        time.sleep(0.5)

        pubs = get_publications(uid)
        print(f"  pubs: {len(pubs)}")
        time.sleep(0.5)

        research = get_research(uid)
        print(f"  research: {len(research)}")
        time.sleep(0.5)

        results.append({
            **t,
            "email": email,
            "profileUrl": f"{BASE}/PsnProfile.aspx?u={uid}",
            "courses": courses,
            "publications": pubs,
            "research": research,
        })

    return results


if __name__ == "__main__":
    print("Scraping Tamkang English Dept teachers from teacher.tku.edu.tw...\n")
    data = scrape_all()
    out = "teachers_data.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Saved {len(data)} teachers to {out}")
