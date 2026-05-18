"""
Scrape 教學實踐研究計畫 (TPR) records for 淡江大學 from tpr.moe.edu.tw,
save by teacher name to tpr_data.json.
"""
import requests, json, time, re, sys
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://tpr.moe.edu.tw/plan/result"
PARAMS = {
    "startYear": "107", "endYear": "",
    "schoolType": "私立大學", "school": "淡江大學", "keyword": ""
}

sess = requests.Session()
sess.headers.update({"User-Agent": "Mozilla/5.0", "Accept-Language": "zh-TW,zh;q=0.9"})


def fetch_page(page):
    params = {**PARAMS, "page": str(page)}
    for attempt in range(3):
        try:
            r = sess.get(BASE, params=params, timeout=20)
            return r.text
        except Exception as e:
            print(f"  retry {attempt+1}: {e}")
            time.sleep(2)
    return None


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="customTable")
    if not table:
        return [], 1
    rows = []
    for tr in table.find_all("tr")[1:]:
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(tds) >= 8:
            rows.append({
                "year": tds[0],
                "field": tds[1],
                "period": tds[2],
                "school": tds[3],
                "department": tds[4],
                "name": tds[5],
                "rank": tds[6],
                "project": tds[7],
            })
    m = re.search(r"totalPages\s*=\s*(\d+)", html)
    total_pages = int(m.group(1)) if m else 1
    return rows, total_pages


def main():
    all_rows = []
    print("Fetching page 1...", flush=True)
    html = fetch_page(1)
    rows, total_pages = parse_page(html)
    all_rows.extend(rows)
    print(f"  page 1: {len(rows)} rows  (total pages: {total_pages})")

    for p in range(2, total_pages + 1):
        time.sleep(0.5)
        print(f"Fetching page {p}/{total_pages}...", flush=True)
        html = fetch_page(p)
        rows, _ = parse_page(html)
        all_rows.extend(rows)
        print(f"  page {p}: {len(rows)} rows")

    # group by teacher name
    by_name = {}
    for r in all_rows:
        by_name.setdefault(r["name"], []).append(r)

    out = {"projects_by_name": by_name, "total": len(all_rows)}
    with open("tpr_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_rows)} TPR records for {len(by_name)} teachers to tpr_data.json")


if __name__ == "__main__":
    main()
