"""
Scrape teacher data for TFJX (日文系) and TFOX (歐語系)
from teacher.tku.edu.tw + nscpeople.onrender.com
"""
import requests
from bs4 import BeautifulSoup
import json, time, re, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_TKU = "https://teacher.tku.edu.tw"
BASE_NSC = "https://nscpeople.onrender.com"
TKU_KEYWORDS = ["淡江", "tku", "tamkang"]
NSC_SUBS = "H04,H05,H06,H11"

sess_tku = requests.Session()
sess_tku.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})
sess_nsc = requests.Session()

RANK_PRIORITY = {"教授": 0, "約聘專案教授": 0, "副教授": 1, "約聘副教授": 1, "助理教授": 2, "講師": 3}


def fetch_html(url, retries=3, timeout=20):
    for i in range(retries):
        try:
            r = sess_tku.get(url, timeout=timeout)
            r.encoding = "utf-8"
            return r.text
        except Exception as e:
            print(f"  [err {i+1}] {e}")
            time.sleep(2)
    return None


def fetch_json_nsc(url, retries=4, timeout=40):
    for attempt in range(retries):
        try:
            r = sess_nsc.get(url, timeout=timeout)
            return r.json()
        except Exception as e:
            wait = 3 * (attempt + 1)
            print(f"  [nsc retry {attempt+1}/{retries}] wait {wait}s")
            time.sleep(wait)
    return {}


def parse_dept_teachers(dept_code):
    """Parse TchrSmy page and return list of {uid, name, nameEn, rank}.

    Page structure per row: TD[0]=Chinese name, TD[1]=English name,
    TD[2]=rank, TD[3]=link to StfTchrSmy (text = record count).
    """
    url = f"{BASE_TKU}/TchrSmy.aspx?cd={dept_code}"
    print(f"Fetching {url} ...")
    r = sess_tku.get(url, timeout=20)
    soup = BeautifulSoup(r.content.decode("utf-8"), "html.parser")
    teachers = []
    seen_uids = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.search(r'(?i)StfTchrSmy\.aspx\?tid=(t\d+)', href)
        if not m:
            continue
        uid = m.group(1)
        if uid in seen_uids:
            continue
        seen_uids.add(uid)

        tr = a.find_parent("tr")
        if not tr:
            continue
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        name    = tds[0].get_text(strip=True)
        name_en = tds[1].get_text(strip=True).replace(",", "").strip()
        rank    = tds[2].get_text(strip=True)
        if not name:
            continue

        teachers.append({"uid": uid, "name": name, "nameEn": name_en, "rank": rank})

    print(f"  Found {len(teachers)} teachers")
    return teachers


def get_profile(uid):
    """Get email + English name from PsnProfile page."""
    html_text = fetch_html(f"{BASE_TKU}/PsnProfile.aspx?u={uid}")
    if not html_text:
        return {"email": "", "nameEn": ""}

    soup = BeautifulSoup(html_text, "html.parser")
    email = ""
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("mailto:"):
            email = a["href"][7:]
            break
    if not email:
        m = re.search(r"[\w.\-]+@[\w.\-]+\.edu\.tw", html_text)
        email = m.group(0) if m else ""

    # English name: 2+ consecutive ALL-CAPS words
    text = soup.get_text(separator=" ")
    name_en = ""
    for c in re.findall(r'\b([A-Z][A-Z\-]{1,}(?:\s+[A-Z][A-Z\-]{1,})+)\b', text):
        c = c.strip()
        if 5 <= len(c) <= 60 and not any(x in c for x in ["HTTP", "TKU", "TAMKANG", "TAIWAN", "ASPX"]):
            name_en = c
            break

    return {"email": email, "nameEn": name_en}


def nsc_search(name):
    url = f"{BASE_NSC}/api/search?subs={NSC_SUBS}&name={requests.utils.quote(name)}&page=1&page_size=20"
    return fetch_json_nsc(url).get("results", [])


def nsc_detail(rs_no):
    return fetch_json_nsc(f"{BASE_NSC}/api/detail/{rs_no}")


def is_tku(org):
    return any(k in org.lower() for k in TKU_KEYWORDS)


def find_rs_no(name):
    results = nsc_search(name)
    tku = [r for r in results if is_tku(r.get("org", ""))]
    if not tku:
        return None
    if len(tku) == 1:
        return tku[0]["rs_no"]
    return tku[0]["rs_no"]


def scrape_dept(dept_code):
    """Full pipeline for one department."""
    partial_file = f"{dept_code.lower()}_partial.json"

    done_uids = set()
    results = []
    if os.path.exists(partial_file):
        try:
            saved = json.load(open(partial_file, encoding="utf-8"))
            results = saved
            done_uids = {r["uid"] for r in results}
            print(f"  Resuming {dept_code}: {len(done_uids)} already done")
        except Exception:
            pass

    raw = parse_dept_teachers(dept_code)
    if not raw:
        return []

    total = len(raw)

    for i, t in enumerate(raw, 1):
        uid = t["uid"]
        name = t["name"]
        rank = t.get("rank", "")

        if uid in done_uids:
            print(f"[{i:02d}/{total}] {name} (skip)")
            continue

        print(f"[{i:02d}/{total}] {name} ({uid})", end=" ... ", flush=True)

        # nameEn already parsed from list page; get email from profile
        name_en = t.get("nameEn", "")
        prof = get_profile(uid)
        email = prof.get("email", "")
        if not name_en:
            name_en = prof.get("nameEn", "")
        time.sleep(0.4)

        rs_no = find_rs_no(name)
        publications = []
        nsc_email = ""

        if rs_no:
            print(f"rs_no={rs_no}", end=" ", flush=True)
            time.sleep(0.3)
            detail = nsc_detail(rs_no)
            publications = detail.get("publications", [])
            nsc_email = detail.get("basic", {}).get("email", "")
            print(f"pubs={len(publications)}")
        else:
            print("NSC: not found")

        results.append({
            "name": name,
            "nameEn": name_en,
            "rank": rank,
            "uid": uid,
            "rs_no": rs_no,
            "email": nsc_email or email,
            "profileUrl": f"{BASE_TKU}/StfTchrSmy.aspx?tid={uid}",
            "courses": [],
            "publications": publications,
        })

        with open(partial_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        time.sleep(0.4)

    results.sort(key=lambda x: RANK_PRIORITY.get(x.get("rank", ""), 9))

    out = f"{dept_code.lower()}_teachers_final.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(results)} teachers to {out}")
    return results


if __name__ == "__main__":
    for code in ["TFJX", "TFOX"]:
        print(f"\n{'='*60}\nProcessing {code}\n{'='*60}")
        scrape_dept(code)
    print("\nAll done!")
