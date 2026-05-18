"""
Fetch Tamkang English Dept teacher publications from nscpeople.onrender.com
"""
import requests
import json
import time

BASE = "https://nscpeople.onrender.com"
TKU_KEYWORDS = ["淡江", "tku", "tamkang"]

TEACHERS = [
    {"name": "蔡振興", "nameEn": "TSAI CHEN-HSING",       "rank": "教授",       "uid": "t711706"},
    {"name": "林怡弟", "nameEn": "LIN YI-TI",               "rank": "教授",       "uid": "t991312"},
    {"name": "陳佩筠", "nameEn": "PEI-YUN CHEN",            "rank": "教授",       "uid": "t987227"},
    {"name": "曾郁景", "nameEn": "YU-CHING TSENG",          "rank": "教授",       "uid": "t986267"},
    {"name": "羅艾琳", "nameEn": "IRIS RALPH",               "rank": "教授",       "uid": "t985505"},
    {"name": "小澤自然","nameEn": "SHIZEN OZAWA",            "rank": "教授",       "uid": "t968359"},
    {"name": "吳怡芬", "nameEn": "I-FEN WU",                 "rank": "副教授",     "uid": "t992807"},
    {"name": "涂銘宏", "nameEn": "MING HUNG TU",             "rank": "副教授",     "uid": "t906169"},
    {"name": "張慈珊", "nameEn": "TZU-SHAN CHANG",           "rank": "副教授",     "uid": "t903772"},
    {"name": "張雅慧", "nameEn": "YEA HUEY CHANG",           "rank": "副教授",     "uid": "t905663"},
    {"name": "齊嵩齡", "nameEn": "CHYI SONG-LING",           "rank": "副教授",     "uid": "t901102"},
    {"name": "蔡瑞敏", "nameEn": "JUI-MIN TSAI",             "rank": "副教授",     "uid": "t980327"},
    {"name": "錢欽昭", "nameEn": "CHIN-JAU CHYAN",           "rank": "副教授",     "uid": "t986717"},
    {"name": "薛玉政", "nameEn": "SIEH YU-CHENG",            "rank": "副教授",     "uid": "t986722"},
    {"name": "鄧秋蓉", "nameEn": "DENG CHIOU-RUNG",          "rank": "副教授",     "uid": "t981147"},
    {"name": "郭家珍", "nameEn": "KUO CHIA-CHEN",            "rank": "副教授",     "uid": "t969421"},
    {"name": "李佳盈", "nameEn": "JIA-YING LEE",             "rank": "副教授",     "uid": "t960216"},
    {"name": "林銘輝", "nameEn": "LIN MING HUEI",            "rank": "副教授",     "uid": "t966407"},
    {"name": "張介英", "nameEn": "CHANG CHIEH-YING",         "rank": "副教授",     "uid": "t932481"},
    {"name": "劉佩勳", "nameEn": "LIU PEI-HSUN",             "rank": "副教授",     "uid": "t953096"},
    {"name": "王慧娟", "nameEn": "HUI-CHUAN WANG",           "rank": "約聘副教授", "uid": "t992887"},
    {"name": "吳瑜雲", "nameEn": "WU YU-YUN",                "rank": "助理教授",   "uid": "t741301"},
    {"name": "包俊傑", "nameEn": "BROWN IAIN KELSALL",       "rank": "助理教授",   "uid": "t988958"},
    {"name": "王蔚婷", "nameEn": "GUTIERREZ JANNETTE WANG",  "rank": "助理教授",   "uid": "t988809"},
    {"name": "莊晏甄", "nameEn": "YEN-CHEN CHUANG",          "rank": "助理教授",   "uid": "t981657"},
    {"name": "雷凱",   "nameEn": "GUY MATTHEW REDMER",       "rank": "助理教授",   "uid": "t969963"},
    {"name": "吳凱書", "nameEn": "WU KAI-SU",                "rank": "助理教授",   "uid": "t939455"},
    {"name": "熊婷惠", "nameEn": "HSIUNG TING-HUI",          "rank": "助理教授",   "uid": "t936737"},
    {"name": "陳家倩", "nameEn": "CHEN CHIA-CHIEN",          "rank": "助理教授",   "uid": "t931891"},
    {"name": "林嘉鴻", "nameEn": "CHIA-HUNG LIN",            "rank": "助理教授",   "uid": "t953007"},
]

sess = requests.Session()

def fetch_json(url, retries=4, timeout=40):
    for attempt in range(retries):
        try:
            r = sess.get(url, timeout=timeout)
            return r.json()
        except Exception as e:
            wait = 3 * (attempt + 1)
            print(f"  [retry {attempt+1}/{retries} err={e}] waiting {wait}s...")
            time.sleep(wait)
    return {}

def search(name):
    url = f"{BASE}/api/search?subs=H04,H05,H11&name={requests.utils.quote(name)}&page=1&page_size=20"
    return fetch_json(url).get("results", [])

def get_detail(rs_no):
    url = f"{BASE}/api/detail/{rs_no}"
    return fetch_json(url)

def is_tku(org: str) -> bool:
    org_lower = org.lower()
    return any(k in org_lower for k in TKU_KEYWORDS)

def find_rs_no(teacher):
    results = search(teacher["name"])
    # filter to TKU
    tku_results = [r for r in results if is_tku(r.get("org", ""))]
    if len(tku_results) == 1:
        return tku_results[0]["rs_no"]
    if len(tku_results) > 1:
        # also filter by dept keyword if ambiguous
        eng_results = [r for r in tku_results if "英文" in r.get("org", "")]
        if eng_results:
            return eng_results[0]["rs_no"]
        return tku_results[0]["rs_no"]
    return None

def main():
    # resume from partial save
    partial_file = "teachers_nsc_partial.json"
    done_uids = set()
    results = []
    try:
        saved = json.load(open(partial_file, encoding="utf-8"))
        results = saved
        done_uids = {r["uid"] for r in results}
        print(f"Resuming: {len(done_uids)} already done.")
    except Exception:
        pass

    total = len(TEACHERS)

    for i, t in enumerate(TEACHERS, 1):
        if t["uid"] in done_uids:
            print(f"[{i:02d}/{total}] {t['name']} (skip)")
            continue
        print(f"[{i:02d}/{total}] {t['name']}...", end=" ", flush=True)

        rs_no = find_rs_no(t)
        if not rs_no:
            print("NOT FOUND in NSC DB")
            results.append({**t, "rs_no": None, "nsc_email": "", "publications": []})
            time.sleep(0.4)
            continue

        print(f"rs_no={rs_no}", end=" ", flush=True)
        time.sleep(0.3)

        detail = get_detail(rs_no)
        basic = detail.get("basic", {})
        pubs = detail.get("publications", [])
        print(f"pubs={len(pubs)}")

        results.append({
            **t,
            "rs_no": rs_no,
            "nsc_email": basic.get("email", ""),
            "publications": pubs,
        })
        # save partial progress after each teacher
        with open(partial_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        time.sleep(0.4)

    # merge with existing teachers_data.json for email / courses
    try:
        existing = {d["uid"]: d for d in json.load(open("teachers_data.json", encoding="utf-8"))}
        for r in results:
            uid = r["uid"]
            if uid in existing:
                r["email"] = r.get("nsc_email") or existing[uid].get("email", "")
                r["courses"] = existing[uid].get("courses", [])
            else:
                r["email"] = r.get("nsc_email", "")
                r["courses"] = []
    except Exception as e:
        print(f"Warning: could not merge teachers_data.json: {e}")
        for r in results:
            r["email"] = r.get("nsc_email", "")
            r["courses"] = []

    out = "teachers_nsc.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(results)} teachers to {out}")

if __name__ == "__main__":
    main()
