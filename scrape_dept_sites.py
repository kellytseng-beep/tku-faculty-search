"""
Scrape authoritative faculty lists from the 3 dept websites
(tflx/tfjx/tfox.tku.edu.tw), which have richer info than teacher.tku.edu.tw:
- Real institutional o365 emails
- Rank, expertise, photo URL
- Sometimes teacher UID from PsnSchoolTime link
"""
import requests, json, re, sys, time
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sess = requests.Session()
sess.headers.update({"User-Agent": "Mozilla/5.0", "Accept-Language": "zh-TW,zh;q=0.9"})

DEPTS = {
    "tflx": "https://www.tflx.tku.edu.tw/tflx/?page_id=7936",
    "tfjx": "https://www.tfjx.tku.edu.tw/tfjx/?page_id=14896",
    "tfox": "https://www.tfox.tku.edu.tw/tfox/?page_id=213",
}

RANK_KEYWORDS = ["教授", "副教授", "助理教授", "助教", "講師", "專案教授", "兼任"]


def parse_dept(html):
    soup = BeautifulSoup(html, "html.parser")
    teachers = []
    for div in soup.find_all("div", class_="dv_members"):
        # determine rank from class names
        rank = ""
        for cls in div.get("class", []):
            for rk in ["約聘專案教授", "專案教授", "約聘副教授", "副教授", "助理教授",
                       "助教", "教授", "講師"]:
                if cls.endswith("-" + rk):
                    rank = rk
                    break
            if rank: break

        h4 = div.find("h4")
        name = h4.get_text(strip=True) if h4 else ""
        if not name:
            continue

        # full text for parsing role/edu/expertise
        full = div.get_text(separator="\n", strip=True)

        # role (職稱) — can be more specific than rank
        role_m = re.search(r"職稱[:：]\s*([^\n]+)", full)
        role = role_m.group(1).strip() if role_m else rank
        # if role text contains a known rank, prefer that
        if not rank:
            for rk in ["約聘專案教授", "專案教授", "約聘副教授", "副教授",
                       "助理教授", "助教", "教授", "講師"]:
                if rk in role:
                    rank = rk
                    break

        # education
        edu_m = re.search(r"學歷[:：]\s*([^\n]+)", full)
        education = edu_m.group(1).strip() if edu_m else ""

        # expertise
        exp_m = re.search(r"專業領域[:：]\s*([^\n]+)", full)
        expertise = exp_m.group(1).strip() if exp_m else ""

        # email
        email = ""
        for a in div.find_all("a", href=True):
            if a["href"].startswith("mailto:"):
                email = a["href"].replace("mailto:", "").strip()
                break

        # uid (from PsnSchoolTime / PsnProfile / StfTchrSmy)
        uid = ""
        for a in div.find_all("a", href=True):
            m = re.search(r"(?:PsnSchoolTime|PsnProfile|StfTchrSmy)\.aspx\?(?:u|tid)=(t\d+)",
                          a["href"])
            if m:
                uid = m.group(1)
                break

        # photo
        photo = ""
        img = div.find("img")
        if img and img.get("src"):
            photo = img["src"]
            if photo.startswith("/"):
                photo = ""  # store relative path only if dept URL known

        teachers.append({
            "name": name, "rank": rank, "role": role,
            "education": education, "expertise": expertise,
            "email": email, "uid": uid, "photo": photo,
        })
    return teachers


def main():
    out = {}
    for key, url in DEPTS.items():
        print(f"\n=== {key.upper()}: {url} ===")
        r = sess.get(url, timeout=20)
        text = r.content.decode("utf-8", errors="replace")
        teachers = parse_dept(text)
        print(f"  Found {len(teachers)} teachers")
        for t in teachers:
            print(f"    {t['rank']:15} {t['name']:6} | {t['email']:35} | uid={t['uid']} | {t['expertise'][:40]}")
        out[key] = teachers
        time.sleep(0.5)

    with open("dept_sites_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to dept_sites_data.json")


if __name__ == "__main__":
    main()
