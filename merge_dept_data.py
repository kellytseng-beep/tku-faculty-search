"""
Merge authoritative dept-site data into existing teacher JSON:
- Update all emails to o365 institutional addresses
- Update rank if changed (log changes)
- Add expertise/role from dept sites
- Add missing teachers (e.g. 曾秋桂 for TFJX)
- Skip 助教 (administrative, not researchers) and known extras

For weekly automation: reads from _v2.json (preferred) or _final.json (initial).
Always writes back to _v2.json.
"""
import json, requests, time, re, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_NSC = "https://nscpeople.onrender.com"
TKU_KEYWORDS = ["淡江", "tku", "tamkang"]
NSC_SUBS = "H04,H05,H06,H11"

sess = requests.Session()

def nsc_fetch(url, retries=4, timeout=40):
    for attempt in range(retries):
        try:
            return sess.get(url, timeout=timeout).json()
        except Exception as e:
            time.sleep(3 * (attempt + 1))
    return {}

def find_rs_no(name):
    url = f"{BASE_NSC}/api/search?subs={NSC_SUBS}&name={requests.utils.quote(name)}&page=1&page_size=20"
    results = nsc_fetch(url).get("results", [])
    tku = [r for r in results if any(k in r.get("org","").lower() for k in TKU_KEYWORDS)]
    if not tku: return None
    return tku[0]["rs_no"]

def nsc_detail(rs_no):
    return nsc_fetch(f"{BASE_NSC}/api/detail/{rs_no}")


def _load_excluded(dept_key):
    try:
        return set(json.load(open("excluded_teachers.json", encoding="utf-8")).get(dept_key, []))
    except Exception:
        return set()


def merge_dept(dept_key, current_file, out_file):
    print(f"\n=== {dept_key.upper()} ===")
    dept = json.load(open("dept_sites_data.json", encoding="utf-8"))[dept_key]
    current = json.load(open(current_file, encoding="utf-8"))
    excluded = _load_excluded(dept_key)

    # start from current data (preserve all existing teachers)
    cur_map = {t["name"].replace("　","").strip(): t for t in current}
    dept_names_set = set()

    # for each dept-site teacher: update email or add as new
    for d in dept:
        if d["rank"] in ("助教", "兼任", ""):
            print(f"  skip non-faculty: {d['name']} ({d['rank']})")
            continue
        name = d["name"].replace("　","").strip()
        if name in excluded:
            print(f"  ⛔ skip excluded: {name}")
            continue
        dept_names_set.add(name)

        if name in cur_map:
            # update existing
            t = cur_map[name]
            old_email = t.get("email","")
            old_rank  = t.get("rank","")
            if d["email"]:
                t["email"] = d["email"]
                if old_email and old_email != d["email"]:
                    print(f"  📧 email updated: {name}  {old_email} -> {d['email']}")
            if d["rank"] and d["rank"] != old_rank:
                print(f"  ⚡ RANK CHANGED: {name}  {old_rank or '(空)'} -> {d['rank']}")
                t["rank"] = d["rank"]
            t["expertise"] = d.get("expertise","")
            t["role"]      = d.get("role","")
            t["education"] = d.get("education","")
            if d.get("uid") and not t.get("uid"):
                t["uid"] = d["uid"]
                t["profileUrl"] = f"https://teacher.tku.edu.tw/StfTchrSmy.aspx?tid={d['uid']}"
        else:
            # new teacher — fetch NSC
            print(f"  NEW: {name} ({d['rank']}) — fetching NSC...")
            rs_no = find_rs_no(name)
            publications = []
            if rs_no:
                time.sleep(0.5)
                detail = nsc_detail(rs_no)
                publications = detail.get("publications", [])
                print(f"    rs_no={rs_no}  pubs={len(publications)}")
            else:
                print(f"    NSC: not found")
            cur_map[name] = {
                "name": name, "nameEn": "",
                "rank": d["rank"], "uid": d.get("uid",""),
                "rs_no": rs_no, "email": d.get("email",""),
                "profileUrl": f"https://teacher.tku.edu.tw/StfTchrSmy.aspx?tid={d.get('uid','')}" if d.get("uid") else "",
                "courses": [], "publications": publications,
                "expertise": d.get("expertise",""),
                "role": d.get("role",""),
                "education": d.get("education",""),
            }

    # report teachers in current but no longer on dept site (kept anyway)
    extras = [n for n in cur_map if n not in dept_names_set]
    if extras:
        print(f"  KEPT (not on current dept site): {extras}")

    merged = list(cur_map.values())
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"  saved {len(merged)} → {out_file}")


def _src(v2, initial):
    """Prefer the v2 file (cumulative) if it exists; else use the initial scrape."""
    return v2 if os.path.exists(v2) else initial


def main():
    merge_dept("tflx", _src("tflx_teachers_v2.json", "teachers_final.json"),       "tflx_teachers_v2.json")
    merge_dept("tfjx", _src("tfjx_teachers_v2.json", "tfjx_teachers_final.json"),  "tfjx_teachers_v2.json")
    merge_dept("tfox", _src("tfox_teachers_v2.json", "tfox_teachers_final.json"),  "tfox_teachers_v2.json")


if __name__ == "__main__":
    main()
