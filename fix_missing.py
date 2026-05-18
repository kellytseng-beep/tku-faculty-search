"""
Fix specific data issues:
- Add 宋麗玲, 巫宛真 (TFOX 西文組) — missing from consolidated tfox page
- Re-fetch 葉夌's NSC pubs (failed before due to full-width space in name)
- Add sub-group info to all TFOX teachers from 4 sub-group sites
"""
import requests, json, time, re, sys
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sess = requests.Session()
sess.headers.update({"User-Agent": "Mozilla/5.0"})
BASE_NSC = "https://nscpeople.onrender.com"
NSC_SUBS = "H04,H05,H06,H11"


def nsc_search(name):
    url = f"{BASE_NSC}/api/search?subs={NSC_SUBS}&name={requests.utils.quote(name)}&page=1&page_size=20"
    return sess.get(url, timeout=40).json().get("results", [])


def nsc_detail(rs_no):
    return sess.get(f"{BASE_NSC}/api/detail/{rs_no}", timeout=40).json()


def find_rs_no(name):
    tku = [r for r in nsc_search(name) if "淡江" in r.get("org", "")]
    return tku[0]["rs_no"] if tku else None


def parse_subgroup_site(url):
    """Return list of {name, rank, email, uid} from a sub-group faculty page."""
    r = sess.get(url, timeout=20)
    text = r.content.decode("utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")
    out = []
    for div in soup.find_all("div", class_="dv_members"):
        h4 = div.find("h4")
        if not h4:
            continue
        name = h4.get_text(strip=True).replace("　", "").strip()
        rank = ""
        for cls in div.get("class", []):
            for rk in ["約聘專案教授", "專案教授", "約聘副教授", "副教授",
                       "助理教授", "助教", "教授", "講師"]:
                if cls.endswith("-" + rk):
                    rank = rk; break
            if rank: break
        email = ""
        uid = ""
        for a in div.find_all("a", href=True):
            if a["href"].startswith("mailto:") and not email:
                email = a["href"][7:].strip()
            m = re.search(r"(?:PsnSchoolTime|PsnProfile|StfTchrSmy)\.aspx\?(?:u|tid)=(t\d+)", a["href"])
            if m and not uid:
                uid = m.group(1)
        # expertise
        full = div.get_text(separator="\n", strip=True)
        exp_m = re.search(r"專業領域[:：]\s*([^\n]+)", full)
        expertise = exp_m.group(1).strip() if exp_m else ""
        edu_m = re.search(r"學歷[:：]\s*([^\n]+)", full)
        education = edu_m.group(1).strip() if edu_m else ""
        role_m = re.search(r"職稱[:：]\s*([^\n]+)", full)
        role = role_m.group(1).strip() if role_m else rank
        out.append({"name": name, "rank": rank, "email": email, "uid": uid,
                    "expertise": expertise, "education": education, "role": role})
    return out


SUBGROUPS = {
    "法文組": "https://www.tffx.tku.edu.tw/tffx/?page_id=16538",
    "德文組": "https://www.tfgx.tku.edu.tw/tfgx/?page_id=6774",
    "西文組": "https://www.tfsx.tku.edu.tw/tfsx/?page_id=9226&asc=專任師資",
    "俄文組": "https://www.tfux.tku.edu.tw/tfux/?page_id=24030",
}


def main():
    # 1) Scrape all 4 sub-group sites
    name_to_group = {}   # name -> 組別
    name_to_info = {}    # name -> full dict
    for group, url in SUBGROUPS.items():
        print(f"\nScraping {group}: {url}")
        teachers = parse_subgroup_site(url)
        print(f"  found {len(teachers)} teachers")
        for t in teachers:
            name_to_group[t["name"]] = group
            name_to_info[t["name"]] = t
        time.sleep(0.5)

    # 2) Load current TFOX data
    data = json.load(open("tfox_teachers_v2.json", encoding="utf-8"))
    cur_names = {t["name"].replace("　", "").strip() for t in data}
    print(f"\nCurrent TFOX: {len(data)} teachers")

    # 3) Add sub-group info to existing teachers
    for t in data:
        n = t["name"].replace("　", "").strip()
        if n in name_to_group:
            t["group"] = name_to_group[n]
            sub = name_to_info[n]
            # also fill in missing fields from sub-group site if present
            if not t.get("expertise") and sub.get("expertise"):
                t["expertise"] = sub["expertise"]
            if not t.get("education") and sub.get("education"):
                t["education"] = sub["education"]
            if not t.get("role") and sub.get("role"):
                t["role"] = sub["role"]
            if not t.get("uid") and sub.get("uid"):
                t["uid"] = sub["uid"]
                t["profileUrl"] = f"https://teacher.tku.edu.tw/StfTchrSmy.aspx?tid={sub['uid']}"

    # Load exclusion list
    try:
        excluded = set(json.load(open("excluded_teachers.json", encoding="utf-8")).get("tfox", []))
    except Exception:
        excluded = set()

    # 4) Add missing teachers
    for name, group in name_to_group.items():
        if name in cur_names or name in excluded:
            if name in excluded:
                print(f"  ⛔ skip excluded: {name}")
            continue
        sub = name_to_info[name]
        print(f"\nNEW: {name} ({group}, {sub['rank']}) — fetching NSC...")
        rs_no = find_rs_no(name)
        pubs = []
        if rs_no:
            time.sleep(0.5)
            detail = nsc_detail(rs_no)
            pubs = detail.get("publications", [])
            print(f"  rs_no={rs_no}  pubs={len(pubs)}")
        else:
            print(f"  NSC: not found")
        data.append({
            "name": name, "nameEn": "",
            "rank": sub["rank"], "uid": sub.get("uid", ""),
            "rs_no": rs_no, "email": sub.get("email", ""),
            "profileUrl": f"https://teacher.tku.edu.tw/StfTchrSmy.aspx?tid={sub['uid']}" if sub.get("uid") else "",
            "courses": [], "publications": pubs,
            "expertise": sub.get("expertise", ""),
            "role": sub.get("role", ""),
            "education": sub.get("education", ""),
            "group": group,
        })

    # 5) Re-sort by rank
    RANK_ORDER = {"教授": 0, "約聘專案教授": 0, "專案教授": 0,
                  "副教授": 1, "約聘副教授": 1, "助理教授": 2, "講師": 3}
    data.sort(key=lambda t: RANK_ORDER.get(t.get("rank", ""), 9))

    with open("tfox_teachers_v2.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(data)} teachers to tfox_teachers_v2.json")

    # 6) Fix 葉夌 (TFJX) — full-width space messed up NSC search
    print("\n--- fixing 葉夌 (TFJX) ---")
    jdata = json.load(open("tfjx_teachers_v2.json", encoding="utf-8"))
    for t in jdata:
        if "葉" in t["name"] and "夌" in t["name"]:
            t["name"] = "葉夌"  # normalize
            rs_no = find_rs_no("葉夌")
            if rs_no:
                time.sleep(0.3)
                detail = nsc_detail(rs_no)
                t["rs_no"] = rs_no
                t["publications"] = detail.get("publications", [])
                print(f"  葉夌: rs_no={rs_no}, pubs={len(t['publications'])}")
            else:
                print("  葉夌: NSC not found")
            break
    with open("tfjx_teachers_v2.json", "w", encoding="utf-8") as f:
        json.dump(jdata, f, ensure_ascii=False, indent=2)
    print("  saved tfjx_teachers_v2.json")


if __name__ == "__main__":
    main()
