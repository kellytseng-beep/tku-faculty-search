"""
Build tflx_teachers.html — static cards pre-rendered in Python,
search/filter via JS that adds/removes CSS class.
"""
import json, html as _html

# ── helpers ──────────────────────────────────────────────────────────────
def esc(s):
    return _html.escape(str(s or ""), quote=True)

def initials(name):
    zh = [c for c in name if ord(c) > 0x3000]
    if len(zh) >= 2:
        return zh[0] + zh[-1]
    return name[:2].upper()

AVATAR_PALETTES = [
    ("bg-blue-100","text-blue-700"),("bg-purple-100","text-purple-700"),
    ("bg-teal-100","text-teal-700"),("bg-rose-100","text-rose-700"),
    ("bg-amber-100","text-amber-700"),("bg-cyan-100","text-cyan-700"),
    ("bg-emerald-100","text-emerald-700"),("bg-fuchsia-100","text-fuchsia-700"),
]
def avatar_color(name):
    h = 0
    for c in name: h = (h * 31 + ord(c)) & 0xffff
    bg, fg = AVATAR_PALETTES[h % len(AVATAR_PALETTES)]
    return f"{bg} {fg}"

RANK_COLORS = {
    "教授":      "bg-blue-100 text-blue-800",
    "副教授":    "bg-indigo-100 text-indigo-800",
    "約聘副教授":"bg-violet-100 text-violet-800",
    "助理教授":  "bg-teal-100 text-teal-800",
}
AREA_COLORS = {
    "文學":    "bg-amber-50 text-amber-700 border border-amber-200",
    "語言學":  "bg-sky-50 text-sky-700 border border-sky-200",
    "英語教學":"bg-emerald-50 text-emerald-700 border border-emerald-200",
    "翻譯":    "bg-violet-50 text-violet-700 border border-violet-200",
    "其他":    "bg-slate-100 text-slate-600",
}
CAT_COLORS = {
    "期刊論文":"bg-blue-50 text-blue-700",
    "專書論文":"bg-purple-50 text-purple-700",
    "專書":"bg-green-50 text-green-700",
    "會議論文":"bg-orange-50 text-orange-700",
    "技術報告":"bg-slate-100 text-slate-600",
    "其他":"bg-slate-100 text-slate-600",
}
CAT_SHORT = {"期刊論文":"期刊","專書論文":"書章","專書":"專書","會議論文":"研討","技術報告":"報告","其他":"其他"}

# ── area inference ────────────────────────────────────────────────────────
LIT_KW   = ["文學","literary","literature","novel","poetry","poetics","fiction",
             "postcoloni","gothic","modernism","translation studies","比較文學",
             "film","cinema","電影","animal","ecology","ecocrit","環境","生態"]
LING_KW  = ["語言","linguist","syntax","phonology","pragmatics","corpus",
             "acquisition","syntactic","優選","形態","morpho","discourse",
             "grammar","semantics","applied linguist","句法"]
ELT_KW   = ["英語教學","language teaching","language learning","second language",
             "EFL","ESL","reading","writing","教學","learner","motivation",
             "vocabulary","pedagogy","curriculum","assessment","teacher training",
             "師資","strategy","strategies","learning strategies","閱讀","寫作"]
TRANS_KW = ["翻譯","translat","interpret","口譯","筆譯"]

def infer_areas(t):
    corpus = " ".join([t.get("nameEn","")]
                      + [p.get("title","") for p in t.get("publications",[])]
                      + t.get("courses",[])).lower()
    areas = []
    if any(k.lower() in corpus for k in TRANS_KW): areas.append("翻譯")
    if any(k.lower() in corpus for k in LIT_KW):   areas.append("文學")
    if any(k.lower() in corpus for k in LING_KW):  areas.append("語言學")
    if any(k.lower() in corpus for k in ELT_KW):   areas.append("英語教學")
    return areas or ["其他"]

# ── card renderer ─────────────────────────────────────────────────────────
def render_card(t):
    rank     = t.get("rank","")
    name     = t.get("name","")
    name_en  = t.get("nameEn","")
    email    = t.get("email","")
    areas    = t.get("areas",[])
    pubs     = t.get("publications",[])
    uid      = t.get("uid","")
    rs_no    = t.get("rs_no","")
    profile_url = t.get("profileUrl","")

    rank_cls = RANK_COLORS.get(rank, "bg-slate-100 text-slate-700")
    av_cls   = avatar_color(name)
    ini      = initials(name)
    total    = len(pubs)

    # area tags
    area_tags = "".join(
        f'<span class="tag {AREA_COLORS.get(a,"bg-slate-100 text-slate-600")}">{esc(a)}</span>'
        for a in areas
    )

    # pub category stats
    cat_count = {}
    for p in pubs:
        c = p.get("category","其他")
        cat_count[c] = cat_count.get(c, 0) + 1
    stat_chips = " ".join(
        f'<span class="tag {CAT_COLORS.get(c,"bg-slate-100 text-slate-600")}">'
        f'{esc(CAT_SHORT.get(c,c))} {n}</span>'
        for c, n in sorted(cat_count.items(), key=lambda x: -x[1])
    )

    # recent 5 pubs
    pub_rows = []
    for p in pubs[:5]:
        yr    = (p.get("date","") or "")[:4]
        cat   = p.get("category","其他")
        title = " ".join((p.get("title","") or "").split())[:120]
        src   = " ".join((p.get("source","") or "").split())[:40]
        cat_cls = CAT_COLORS.get(cat,"bg-slate-100 text-slate-600")
        cat_s   = CAT_SHORT.get(cat,cat)
        src_html = f'<span class="text-slate-400"> · {esc(src)}</span>' if src else ""
        pub_rows.append(
            f'<div class="pub-row flex gap-2 text-xs py-1.5 border-b border-slate-100 last:border-0">'
            f'<span class="text-slate-400 w-10 shrink-0">{esc(yr)}</span>'
            f'<span class="tag {cat_cls} shrink-0">{esc(cat_s)}</span>'
            f'<span class="text-slate-700 leading-snug">{esc(title)}{src_html}</span>'
            f'</div>'
        )
    pub_block = "".join(pub_rows)

    # extra pubs beyond first 5 — shown via <details>
    more_link = ""
    if total > 5:
        extra_rows = []
        for p in pubs[5:]:
            yr    = (p.get("date","") or "")[:4]
            cat   = p.get("category","其他")
            title = " ".join((p.get("title","") or "").split())[:120]
            src   = " ".join((p.get("source","") or "").split())[:40]
            cat_cls = CAT_COLORS.get(cat,"bg-slate-100 text-slate-600")
            cat_s   = CAT_SHORT.get(cat,cat)
            src_html = f'<span class="text-slate-400"> · {esc(src)}</span>' if src else ""
            extra_rows.append(
                f'<div class="pub-row flex gap-2 text-xs py-1.5 border-b border-slate-100 last:border-0">'
                f'<span class="text-slate-400 w-10 shrink-0">{esc(yr)}</span>'
                f'<span class="tag {cat_cls} shrink-0">{esc(cat_s)}</span>'
                f'<span class="text-slate-700 leading-snug">{esc(title)}{src_html}</span>'
                f'</div>'
            )
        more_link = (
            f'<details class="mt-1">'
            f'<summary class="text-xs text-blue-500 cursor-pointer hover:underline list-none pt-1.5 text-right">'
            f'查看全部 {total} 筆 ▾</summary>'
            f'<div class="mt-1">{"".join(extra_rows)}</div>'
            f'</details>'
        )

    email_html = (
        f'<a href="mailto:{esc(email)}" class="text-xs text-slate-400 hover:text-blue-500 truncate">{esc(email)}</a>'
        if email else '<span class="text-xs text-slate-300">—</span>'
    )
    profile_html = (
        f'<a href="{esc(profile_url)}" target="_blank" rel="noopener" '
        f'class="text-xs text-blue-500 hover:underline shrink-0 flex items-center gap-0.5">'
        f'教師歷程'
        f'<svg class="w-3 h-3 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
        f'd="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>'
        f'</svg></a>'
    ) if profile_url else ""

    # data attributes for JS filter (safe because esc() is applied)
    search_corpus = " ".join([name, name_en] + [" ".join((p.get("title","") or "").split()) for p in pubs]).lower()

    # rank order for sorting
    rank_order = {"教授":0,"副教授":1,"約聘副教授":1,"助理教授":2}.get(rank, 9)

    return (
        f'<div class="card bg-white rounded-xl shadow-sm border border-slate-100 p-4 flex flex-col gap-3" '
        f'data-rank="{esc(rank)}" '
        f'data-areas="{esc(",".join(areas))}" '
        f'data-search="{esc(search_corpus[:500])}" '
        f'data-rankorder="{rank_order}" '
        f'data-pubs="{total}">'

        # top row
        f'<div class="flex items-start gap-3">'
        f'<div class="w-12 h-12 rounded-full {av_cls} flex items-center justify-center '
        f'text-base font-bold shrink-0">{esc(ini)}</div>'
        f'<div class="flex-1 min-w-0">'
        f'<div class="flex flex-wrap items-center gap-2">'
        f'<span class="font-semibold text-slate-800">{esc(name)}</span>'
        f'<span class="tag {rank_cls} font-medium">{esc(rank)}</span>'
        f'</div>'
        f'<div class="text-xs text-slate-400">{esc(name_en)}</div>'
        f'<div class="flex flex-wrap gap-1 mt-1">{area_tags}</div>'
        f'</div>'
        f'<div class="text-right shrink-0">'
        f'<div class="text-xl font-bold text-blue-600">{total}</div>'
        f'<div class="text-xs text-slate-400">篇著作</div>'
        f'</div>'
        f'</div>'

        # stat chips
        + (f'<div class="flex flex-wrap gap-1">{stat_chips}</div>' if stat_chips else "")

        # publications
        + (
            f'<div class="border border-slate-100 rounded-lg px-3 py-1">{pub_block}{more_link}</div>'
            if pub_block else
            '<div class="text-xs text-slate-400 italic">暫無論著資料</div>'
        )

        # footer
        + f'<div class="flex items-center justify-between gap-2 pt-1 border-t border-slate-50">'
        f'<div class="min-w-0 flex-1">{email_html}</div>'
        f'{profile_html}'
        f'</div>'

        f'</div>'
    )

# ── load & process data ───────────────────────────────────────────────────
data = json.load(open("teachers_final.json", encoding="utf-8"))

for t in data:
    t["areas"] = infer_areas(t)
    t["profileUrl"] = f"https://teacher.tku.edu.tw/StfTchrSmy.aspx?tid={t['uid']}"
    for p in t.get("publications", []):
        if p.get("title"):  p["title"]  = " ".join(p["title"].split())
        if p.get("source"): p["source"] = " ".join(p["source"].split())

RANK_ORDER = {"教授":0,"副教授":1,"約聘副教授":1,"助理教授":2}
data.sort(key=lambda t: RANK_ORDER.get(t.get("rank",""),9))

cards_html = "\n".join(render_card(t) for t in data)
total = len(data)

# ── page template ─────────────────────────────────────────────────────────
PAGE = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>淡江大學英文學系 — 專任師資查詢</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
body {{ font-family: 'Noto Sans TC', sans-serif; }}
.tag {{ display:inline-block; padding:1px 7px; border-radius:9999px; font-size:0.7rem; line-height:1.5; white-space:nowrap; }}
.card {{ transition:transform 0.15s,box-shadow 0.15s; }}
.card:hover {{ transform:translateY(-2px); box-shadow:0 8px 20px -4px rgba(0,0,0,.1); }}
.pub-row:hover {{ background:#f8fafc; }}
.hidden-card {{ display:none!important; }}
</style>
</head>
<body class="bg-slate-50 min-h-screen">

<header class="bg-gradient-to-r from-blue-900 to-blue-700 text-white shadow-lg">
  <div class="max-w-7xl mx-auto px-4 py-5 flex flex-col sm:flex-row items-start sm:items-center gap-3">
    <div>
      <div class="text-xs text-blue-300 mb-0.5">淡江大學 · 外國語文學院</div>
      <h1 class="text-2xl font-bold tracking-wide">英文學系 專任師資</h1>
      <div class="text-xs text-blue-300 mt-0.5">資料來源：國科會研究人才資料庫 · 教師歷程系統</div>
    </div>
    <div class="sm:ml-auto text-right">
      <div class="text-3xl font-bold" id="countDisplay">{total}</div>
      <div class="text-xs text-blue-300">位教師</div>
    </div>
  </div>
</header>

<div class="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-sm">
  <div class="max-w-7xl mx-auto px-4 py-3 flex flex-wrap gap-2 items-center">
    <div class="relative">
      <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
      </svg>
      <input type="search" id="searchInput" placeholder="搜尋姓名、論著關鍵字…"
        class="pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-400">
    </div>
    <div class="flex gap-1.5 flex-wrap">
      <button onclick="setRank('all',this)"   class="rank-btn active-rank px-3 py-1 rounded-lg text-xs font-medium bg-blue-600 text-white border border-blue-600">全部</button>
      <button onclick="setRank('教授',this)"  class="rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">教授</button>
      <button onclick="setRank('副教授',this)" class="rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">副教授</button>
      <button onclick="setRank('助理教授',this)" class="rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">助理教授</button>
    </div>
    <div class="flex gap-1.5 flex-wrap">
      <button onclick="setArea('all',this)"    class="area-btn active-area px-3 py-1 rounded-lg text-xs font-medium bg-teal-600 text-white border border-teal-600">所有領域</button>
      <button onclick="setArea('文學',this)"   class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">文學</button>
      <button onclick="setArea('語言學',this)" class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">語言學</button>
      <button onclick="setArea('英語教學',this)" class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">英語教學</button>
      <button onclick="setArea('翻譯',this)"   class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">翻譯</button>
    </div>
    <select id="sortSelect" onchange="applySort(this.value)"
      class="ml-auto px-2 py-1.5 border border-slate-300 rounded-lg text-xs text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
      <option value="rank">排列：依職稱</option>
      <option value="pubs">排列：依論著數</option>
      <option value="name">排列：依姓名</option>
    </select>
  </div>
</div>

<main class="max-w-7xl mx-auto px-4 py-5">
  <div id="noResult" class="hidden text-center py-24 text-slate-400">
    <p>找不到符合條件的教師</p>
  </div>
  <div id="teacherGrid" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
{cards_html}
  </div>
</main>

<footer class="text-center text-xs text-slate-400 py-6 border-t border-slate-200">
  資料來源：
  <a href="https://nscpeople.onrender.com/" target="_blank" class="text-blue-400 hover:underline">國科會研究人才資料庫</a> ·
  <a href="https://teacher.tku.edu.tw/TchrSmy.aspx?cd=TFLX" target="_blank" class="text-blue-400 hover:underline">淡江教師歷程</a> ·
  <a href="https://www.tflx.tku.edu.tw/tflx/?page_id=7936" target="_blank" class="text-blue-400 hover:underline">英文學系官網</a>
</footer>

<script>
var activeRank = 'all';
var activeArea = 'all';

function applyFilters() {{
  var q = document.getElementById('searchInput').value.trim().toLowerCase();
  var cards = document.getElementById('teacherGrid').querySelectorAll('.card');
  var visible = 0;
  cards.forEach(function(card) {{
    var rank   = card.dataset.rank;
    var areas  = card.dataset.areas;
    var search = card.dataset.search;
    var matchRank   = activeRank === 'all' || rank === activeRank || (activeRank === '副教授' && rank === '約聘副教授');
    var matchArea   = activeArea === 'all' || areas.split(',').indexOf(activeArea) >= 0;
    var matchSearch = !q || search.indexOf(q) >= 0;
    if (matchRank && matchArea && matchSearch) {{
      card.classList.remove('hidden-card');
      visible++;
    }} else {{
      card.classList.add('hidden-card');
    }}
  }});
  document.getElementById('countDisplay').textContent = visible;
  document.getElementById('noResult').classList.toggle('hidden', visible > 0);
}}

function setRank(rank, btn) {{
  activeRank = rank;
  document.querySelectorAll('.rank-btn').forEach(function(b) {{
    b.className = 'rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600';
  }});
  btn.className = 'rank-btn active-rank px-3 py-1 rounded-lg text-xs font-medium bg-blue-600 text-white border border-blue-600';
  applyFilters();
}}

function setArea(area, btn) {{
  activeArea = area;
  document.querySelectorAll('.area-btn').forEach(function(b) {{
    b.className = 'area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600';
  }});
  btn.className = 'area-btn active-area px-3 py-1 rounded-lg text-xs font-medium bg-teal-600 text-white border border-teal-600';
  applyFilters();
}}

function applySort(mode) {{
  var grid = document.getElementById('teacherGrid');
  var cards = Array.from(grid.querySelectorAll('.card'));
  if (mode === 'pubs') {{
    cards.sort(function(a,b) {{ return parseInt(b.dataset.pubs||0) - parseInt(a.dataset.pubs||0); }});
  }} else if (mode === 'name') {{
    cards.sort(function(a,b) {{ return a.dataset.search.localeCompare(b.dataset.search,'zh-TW'); }});
  }} else {{
    cards.sort(function(a,b) {{ return parseInt(a.dataset.rankorder||9) - parseInt(b.dataset.rankorder||9); }});
  }}
  cards.forEach(function(c) {{ grid.appendChild(c); }});
}}

document.getElementById('searchInput').addEventListener('input', applyFilters);
</script>
</body>
</html>"""

with open("tflx_teachers.html", "w", encoding="utf-8") as f:
    f.write(PAGE)

print(f"Built tflx_teachers.html with {total} static cards ({len(PAGE)//1024}KB)")
