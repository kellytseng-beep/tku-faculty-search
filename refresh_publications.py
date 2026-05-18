"""
Weekly refresh of NSC publications for all existing teachers.
Re-fetches /api/detail/{rs_no} so new publications appear automatically.
"""
import json, requests, time, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://nscpeople.onrender.com"
sess = requests.Session()


def fetch_detail(rs_no, retries=3):
    for i in range(retries):
        try:
            return sess.get(f"{BASE}/api/detail/{rs_no}", timeout=40).json()
        except Exception as e:
            print(f"  err {i+1}: {e}")
            time.sleep(3 * (i + 1))
    return {}


def refresh(path):
    if not os.path.exists(path):
        print(f"  SKIP: {path} not found")
        return
    print(f"\n=== {path} ===")
    data = json.load(open(path, encoding="utf-8"))
    total_old = sum(len(t.get("publications", [])) for t in data)
    updated, unchanged, no_rs = 0, 0, 0
    for i, t in enumerate(data, 1):
        rs_no = t.get("rs_no")
        if not rs_no:
            no_rs += 1
            continue
        old_n = len(t.get("publications", []))
        print(f"  [{i:02d}/{len(data)}] {t['name']:8} ", end="", flush=True)
        detail = fetch_detail(rs_no)
        new_pubs = detail.get("publications", [])
        if new_pubs:
            t["publications"] = new_pubs
            if len(new_pubs) != old_n:
                diff = len(new_pubs) - old_n
                print(f"{old_n} -> {len(new_pubs)} ({'+' if diff > 0 else ''}{diff})")
                updated += 1
            else:
                print(f"{old_n} (no change)")
                unchanged += 1
        else:
            print(f"(no data, keeping {old_n})")
        time.sleep(0.4)
    total_new = sum(len(t.get("publications", [])) for t in data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Summary: updated={updated}, unchanged={unchanged}, no_rs={no_rs}")
    print(f"  Total pubs: {total_old} -> {total_new}")


if __name__ == "__main__":
    for f in ("tflx_teachers_v2.json", "tfjx_teachers_v2.json", "tfox_teachers_v2.json"):
        refresh(f)
