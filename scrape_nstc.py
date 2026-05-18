"""
Scrape NSTC (國家科學及技術委員會) 補助研究計畫 by PI name from
wsts.nstc.gov.tw/STSWeb/Award/AwardMultiQuery.aspx
Save to nstc_data.json indexed by teacher name.
"""
import urllib.request, urllib.parse, ssl, re, json, time, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "https://wsts.nstc.gov.tw/STSWeb/Award/AwardMultiQuery.aspx"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ctx.set_ciphers("DEFAULT@SECLEVEL=0")


def fetch(data=None, cookies=""):
    headers = {"User-Agent": "Mozilla/5.0", "Cookie": cookies}
    if data:
        body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        body = None
    req = urllib.request.Request(URL, data=body, headers=headers)
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(req, context=ctx, timeout=45)
            sc = r.headers.get_all("Set-Cookie") or []
            new_ck = "; ".join(s.split(";", 1)[0] for s in sc) if sc else cookies
            return r.read().decode("utf-8", "replace"), new_ck
        except Exception as e:
            print(f"  fetch err {attempt+1}: {e}")
            time.sleep(3)
    return "", cookies


def extract(name, text):
    m = re.search(r'<input[^>]+name="' + re.escape(name) + r'"[^>]+value="([^"]*)"', text)
    return m.group(1) if m else ""


def setup_search_form():
    """Steps 1+2: get initial page, then click 補助研究計畫 to reach search form."""
    html1, cookies = fetch()
    data = {
        "__EVENTTARGET": "dtlItem$ctl00$btnItem",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": extract("__VIEWSTATE", html1),
        "__VIEWSTATEGENERATOR": extract("__VIEWSTATEGENERATOR", html1),
        "__EVENTVALIDATION": extract("__EVENTVALIDATION", html1),
    }
    html2, cookies = fetch(data=data, cookies=cookies)
    return html2, cookies


def parse_results(html):
    """Parse the grdResult table. Returns list of dicts."""
    m = re.search(r'<table[^>]*grdResult[\s\S]+?</table>', html)
    if not m:
        return []
    table = m.group(0)
    trs = re.findall(r"<tr[^>]*>([\s\S]+?)</tr>", table)
    rows = []
    for tr in trs[1:]:  # skip header
        cells = re.findall(r"<t[dh][^>]*>([\s\S]+?)</t[dh]>", tr)
        if len(cells) < 4:
            continue
        year = re.sub(r"<[^>]+>", " ", cells[0]).strip()
        name = re.sub(r"<[^>]+>", " ", cells[1]).strip()
        org  = re.sub(r"<[^>]+>", " ", cells[2]).strip()
        content_raw = re.sub(r"<[^>]+>", " ", cells[3])
        content = re.sub(r"\s+", " ", content_raw).strip()
        # Parse content fields
        title_m = re.search(r"計畫名稱[:：]\s*([^成執總研]+?)(?=成果報告|執行起迄|總核定|研究領域|$)", content)
        dates_m = re.search(r"執行起迄[:：]\s*([\d/]+~[\d/]+)", content)
        amount_m = re.search(r"總核定金額[:：]\s*([\d,]+)", content)
        field_m = re.search(r"研究領域[:：]\s*([^成計總執]+)", content)
        rows.append({
            "year": year,
            "name": name,
            "org": org,
            "title": title_m.group(1).strip() if title_m else content[:80],
            "dates": dates_m.group(1) if dates_m else "",
            "amount": amount_m.group(1) if amount_m else "",
            "field": field_m.group(1).strip() if field_m else "",
        })
    # check total pages
    pages_m = re.search(r'第(\d+)頁.*?共.*?(\d+).*?頁|共\s*(\d+)\s*頁|(\d+)\s*筆', html)
    return rows


def parse_total(html):
    """Return total record count from result page."""
    m = re.search(r"共[^\d]*?(\d+)\s*筆", html)
    return int(m.group(1)) if m else 0


def get_pagination_options(html):
    """Return list of page option values from ddlPage."""
    m = re.search(r'<select[^>]+name="wUctlAwardQueryPage\$grdResult\$ctl13\$ddlPage"[\s\S]+?</select>', html)
    if not m:
        return []
    return re.findall(r'<option[^>]*value="(\d+)"', m.group(0))


def search_by_name(html_form, cookies, pi_name):
    """Submit search with PI name. Return all rows (handle pagination)."""
    data = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": extract("__VIEWSTATE", html_form),
        "__VIEWSTATEGENERATOR": extract("__VIEWSTATEGENERATOR", html_form),
        "__EVENTVALIDATION": extract("__EVENTVALIDATION", html_form),
        "wUctlAwardQueryPage$repQuery$ctl01$ddlYRst": "100",
        "wUctlAwardQueryPage$repQuery$ctl01$ddlYRend": "115",
        "wUctlAwardQueryPage$repQuery$ctl02$ddlD": "",
        "wUctlAwardQueryPage$repQuery$ctl03$ddlO1": "",
        "wUctlAwardQueryPage$repQuery$ctl04$txtT": pi_name,
        "wUctlAwardQueryPage$repQuery$ctl05$txtT": "",
        "wUctlAwardQueryPage$repQuery$ctl07$txtT": "",
        "wUctlAwardQueryPage$repQuery$ctl08$rblR": "AWARD_YEAR",
        "wUctlAwardQueryPage$ddlPageSize": "100",
        "wUctlAwardQueryPage$btnQuery.x": "50",
        "wUctlAwardQueryPage$btnQuery.y": "10",
    }
    html, cookies = fetch(data=data, cookies=cookies)
    rows = parse_results(html)
    # Handle pagination — if more pages
    pages = get_pagination_options(html)
    if len(pages) > 1:
        for p in pages[1:]:
            page_data = {
                "__EVENTTARGET": "wUctlAwardQueryPage$grdResult$ctl13$ddlPage",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "__VIEWSTATE": extract("__VIEWSTATE", html),
                "__VIEWSTATEGENERATOR": extract("__VIEWSTATEGENERATOR", html),
                "__EVENTVALIDATION": extract("__EVENTVALIDATION", html),
                "wUctlAwardQueryPage$grdResult$ctl13$ddlPage": p,
                "wUctlAwardQueryPage$ddlPageSize": "100",
            }
            html, cookies = fetch(data=page_data, cookies=cookies)
            rows.extend(parse_results(html))
            time.sleep(0.3)
    return rows, html, cookies


def load_all_teachers():
    """Load all 88 teacher names + dept."""
    teachers = []
    for f, lbl in [("tflx_teachers_v2.json", "TFLX"),
                    ("tfjx_teachers_v2.json", "TFJX"),
                    ("tfox_teachers_v2.json", "TFOX")]:
        for t in json.load(open(f, encoding="utf-8")):
            teachers.append({"name": t["name"], "dept": lbl})
    return teachers


def main():
    partial_file = "nstc_partial.json"
    out = {}
    if False:  # for resume support
        try:
            out = json.load(open(partial_file, encoding="utf-8"))
        except Exception:
            out = {}

    teachers = load_all_teachers()
    print(f"Total teachers to scrape: {len(teachers)}")

    print("Setting up search form (steps 1+2)...")
    html_form, cookies = setup_search_form()
    print(f"  form HTML len: {len(html_form)}")

    for i, t in enumerate(teachers, 1):
        if t["name"] in out:
            print(f"[{i:02d}/{len(teachers)}] {t['name']} (skip)")
            continue
        print(f"[{i:02d}/{len(teachers)}] {t['name']} ({t['dept']})", end=" ... ", flush=True)
        try:
            rows, last_html, cookies = search_by_name(html_form, cookies, t["name"])
            # filter to 淡江 + 學會 projects only
            tku_rows = [r for r in rows if "淡江" in r["org"] or "中華民國" in r["org"]]
            print(f"total={len(rows)}, kept={len(tku_rows)}")
            out[t["name"]] = tku_rows
            # Update form html for next iteration to keep VIEWSTATE fresh
            html_form = last_html
            # save partial
            with open(partial_file, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ERR: {e}")
            # re-establish form
            html_form, cookies = setup_search_form()
        time.sleep(0.5)

    # Save final
    with open("nstc_data.json", "w", encoding="utf-8") as f:
        json.dump({"projects_by_name": out, "total": sum(len(v) for v in out.values())}, f,
                  ensure_ascii=False, indent=2)
    print(f"\nDone. Saved {sum(len(v) for v in out.values())} projects for {len(out)} teachers to nstc_data.json")


if __name__ == "__main__":
    main()
