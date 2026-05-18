"""
Build teacher HTML pages for TFLX, TFJX, TFOX + faculty hub index page.
"""
import json, html as _html, os

# load TPR data once (optional)
TPR_BY_NAME = {}
if os.path.exists("tpr_data.json"):
    try:
        TPR_BY_NAME = json.load(open("tpr_data.json", encoding="utf-8")).get("projects_by_name", {})
    except Exception:
        pass

# load NSTC data once (optional)
NSTC_BY_NAME = {}
if os.path.exists("nstc_data.json"):
    try:
        NSTC_BY_NAME = json.load(open("nstc_data.json", encoding="utf-8")).get("projects_by_name", {})
    except Exception:
        pass

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
    "教授":          "bg-blue-100 text-blue-800",
    "約聘專案教授":  "bg-sky-100 text-sky-800",
    "副教授":        "bg-indigo-100 text-indigo-800",
    "約聘副教授":    "bg-violet-100 text-violet-800",
    "助理教授":      "bg-teal-100 text-teal-800",
    "講師":          "bg-slate-100 text-slate-700",
}
AREA_COLORS = {
    "文學":    "bg-amber-50 text-amber-700 border border-amber-200",
    "語言學":  "bg-sky-50 text-sky-700 border border-sky-200",
    "英語教學":"bg-emerald-50 text-emerald-700 border border-emerald-200",
    "日語教學":"bg-emerald-50 text-emerald-700 border border-emerald-200",
    "語言教學":"bg-emerald-50 text-emerald-700 border border-emerald-200",
    "翻譯":    "bg-violet-50 text-violet-700 border border-violet-200",
    "其他":    "bg-slate-100 text-slate-600",
}
CAT_COLORS = {
    "期刊論文": "bg-blue-50 text-blue-700",
    "專書論文": "bg-purple-50 text-purple-700",
    "專書":     "bg-green-50 text-green-700",
    "會議論文": "bg-orange-50 text-orange-700",
    "研討會論文":"bg-orange-50 text-orange-700",
    "技術報告": "bg-slate-100 text-slate-600",
    "其他":     "bg-slate-100 text-slate-600",
}
CAT_SHORT = {
    "期刊論文":"期刊","專書論文":"書章","專書":"專書",
    "會議論文":"研討","研討會論文":"研討","技術報告":"報告","其他":"其他",
}

# ── per-department area inference ──────────────────────────────────────────
AREA_KW = {
    "tflx": {
        "teaching_label": "英語教學",
        "LIT":  ["文學","literary","literature","novel","poetry","poetics","fiction",
                 "postcoloni","gothic","modernism","比較文學","film","cinema","電影",
                 "animal","ecology","ecocrit","環境","生態"],
        "LING": ["語言","linguist","syntax","phonology","pragmatics","corpus",
                 "acquisition","syntactic","優選","形態","morpho","discourse",
                 "grammar","semantics","applied linguist","句法"],
        "TEACH":["英語教學","language teaching","language learning","second language",
                 "EFL","ESL","reading","writing","教學","learner","motivation",
                 "vocabulary","pedagogy","curriculum","assessment","teacher training",
                 "師資","strategy","strategies","learning strategies","閱讀","寫作"],
        "TRANS":["翻譯","translat","interpret","口譯","筆譯"],
    },
    "tfjx": {
        "teaching_label": "日語教學",
        "LIT":  ["文学","文學","literary","literature","文芸","小説","詩","俳句",
                 "和歌","物語","日本文","fiction","poetry","日本近代","日本現代",
                 "日本古典","日本語文学","文豪"],
        "LING": ["語言學","linguist","語学","文法","語彙","日語","日本語","phonology",
                 "morphology","syntax","語用","意味","語法","音韻","形態"],
        "TEACH":["日語教育","教育","教学","teaching","learning","教授法","習得",
                 "second language","language learning","EJL","日本語教育","日語教學",
                 "pedagogy","learner","curriculum","motivation","策略"],
        "TRANS":["翻訳","翻譯","translation","interpret","口譯","筆譯"],
    },
    "tfox": {
        "teaching_label": "語言教學",
        "LIT":  ["文學","文学","literature","literary","fiction","poetry","poetics",
                 "littérature","Literatur","literatura","romanzo","poesia","roman",
                 "nouvelle","theatre","théâtre","novel","比較文學"],
        "LING": ["語言學","linguist","grammar","syntax","phonology","morphology",
                 "pragmatics","sémantique","Semantik","semántica","corpus","discourse",
                 "grammaire","Grammatik","gramática","applied linguist"],
        "TEACH":["教學","teaching","language learning","didactique","Didaktik",
                 "enseñanza","language teaching","second language","EFL","pedagogy",
                 "learner","curriculum","assessment","外語","語言教育","師資"],
        "TRANS":["翻譯","translation","interpret","口譯","traduction","Übersetzung",
                 "traducción","筆譯"],
    },
}

RANK_ORDER = {"教授":0,"約聘專案教授":0,"副教授":1,"約聘副教授":1,"助理教授":2,"講師":3}

def infer_areas(t, dept_key):
    kw = AREA_KW[dept_key]
    corpus = " ".join([t.get("nameEn","")]
                      + [p.get("title","") for p in t.get("publications",[])]
                      + t.get("courses",[])).lower()
    areas = []
    if any(k.lower() in corpus for k in kw["TRANS"]): areas.append("翻譯")
    if any(k.lower() in corpus for k in kw["LIT"]):   areas.append("文學")
    if any(k.lower() in corpus for k in kw["LING"]):  areas.append("語言學")
    tl = kw["teaching_label"]
    if any(k.lower() in corpus for k in kw["TEACH"]): areas.append(tl)
    return areas or ["其他"]

# ── card renderer ──────────────────────────────────────────────────────────
def render_card(t):
    rank     = t.get("rank","")
    name     = t.get("name","")
    name_en  = t.get("nameEn","")
    email    = t.get("email","")
    areas    = t.get("areas",[])
    pubs     = t.get("publications",[])
    profile_url = t.get("profileUrl","")
    expertise = t.get("expertise","")
    group    = t.get("group","")  # 法文組/德文組/西文組/俄文組 (TFOX only)
    uid      = t.get("uid","")
    schedule_url = f"https://teacher.tku.edu.tw/PsnSchoolTime.aspx?u={uid}" if uid else ""

    rank_cls = RANK_COLORS.get(rank, "bg-slate-100 text-slate-700")
    av_cls   = avatar_color(name)
    ini      = initials(name)
    total    = len(pubs)

    GROUP_COLORS = {
        "法文組": "bg-rose-50 text-rose-700 border border-rose-200",
        "德文組": "bg-amber-50 text-amber-700 border border-amber-200",
        "西文組": "bg-orange-50 text-orange-700 border border-orange-200",
        "俄文組": "bg-sky-50 text-sky-700 border border-sky-200",
    }
    group_tag = (
        f'<span class="tag {GROUP_COLORS.get(group, "bg-slate-100 text-slate-600")}">{esc(group)}</span>'
        if group else ""
    )

    area_tags = "".join(
        f'<span class="tag {AREA_COLORS.get(a,"bg-slate-100 text-slate-600")}">{esc(a)}</span>'
        for a in areas
    )

    cat_count = {}
    for p in pubs:
        c = p.get("category","其他")
        cat_count[c] = cat_count.get(c, 0) + 1
    stat_chips = " ".join(
        f'<span class="tag {CAT_COLORS.get(c,"bg-slate-100 text-slate-600")}">'
        f'{esc(CAT_SHORT.get(c,c))} {n}</span>'
        for c, n in sorted(cat_count.items(), key=lambda x: -x[1])
    )

    def pub_row_html(p):
        yr  = (p.get("date","") or "")[:4]
        cat = p.get("category","其他")
        ttl = " ".join((p.get("title","") or "").split())[:120]
        src = " ".join((p.get("source","") or "").split())[:40]
        cls = CAT_COLORS.get(cat,"bg-slate-100 text-slate-600")
        sh  = CAT_SHORT.get(cat,cat)
        src_html = f'<span class="text-slate-400"> · {esc(src)}</span>' if src else ""
        return (
            f'<div class="pub-row flex gap-2 text-xs py-1.5 border-b border-slate-100 last:border-0">'
            f'<span class="text-slate-400 w-10 shrink-0">{esc(yr)}</span>'
            f'<span class="tag {cls} shrink-0">{esc(sh)}</span>'
            f'<span class="text-slate-700 leading-snug">{esc(ttl)}{src_html}</span>'
            f'</div>'
        )

    pub_block = "".join(pub_row_html(p) for p in pubs[:5])

    more_link = ""
    if total > 5:
        extra = "".join(pub_row_html(p) for p in pubs[5:])
        more_link = (
            f'<details class="mt-1"><summary class="text-xs text-blue-500 cursor-pointer '
            f'hover:underline list-none pt-1.5 text-right">查看全部 {total} 筆 ▾</summary>'
            f'<div class="mt-1">{extra}</div></details>'
        )

    # NSTC projects (國科會補助研究計畫)
    nstc_projects = NSTC_BY_NAME.get(name, [])
    nstc_html = ""
    if nstc_projects:
        rows = []
        for p in nstc_projects:
            yr  = esc(p.get("year",""))
            ttl = esc(p.get("title",""))[:120]
            dates = esc(p.get("dates",""))
            org   = esc(p.get("org",""))
            amount = p.get("amount","")
            amt_html = f'<span class="text-amber-700 font-medium">${esc(amount)}</span>' if amount else ""
            rows.append(
                f'<div class="pub-row flex gap-2 text-xs py-1.5 border-b border-amber-100 last:border-0">'
                f'<span class="text-slate-400 w-10 shrink-0">{yr}</span>'
                f'<span class="tag bg-amber-50 text-amber-700 shrink-0">國科</span>'
                f'<span class="text-slate-700 leading-snug">{ttl}'
                f'<span class="text-slate-400"> · {dates} {amt_html}</span></span>'
                f'</div>'
            )
        nstc_html = (
            f'<details class="rounded-lg border border-amber-100 bg-amber-50/30 px-3 py-1">'
            f'<summary class="text-xs font-medium text-amber-700 cursor-pointer py-1 list-none flex items-center gap-1.5">'
            f'<svg class="w-3.5 h-3.5 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            f'd="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>'
            f'</svg>'
            f'國科會研究計畫 ({len(nstc_projects)}) ▾</summary>'
            f'<div class="mt-1">{"".join(rows)}</div></details>'
        )

    # TPR projects (教學實踐研究計畫)
    tpr_projects = TPR_BY_NAME.get(name, [])
    tpr_html = ""
    if tpr_projects:
        rows = []
        for proj in tpr_projects:
            yr   = esc(proj.get("year",""))
            fld  = esc(proj.get("field",""))
            ttl  = esc(proj.get("project",""))[:120]
            dept = esc(proj.get("department",""))
            rows.append(
                f'<div class="pub-row flex gap-2 text-xs py-1.5 border-b border-emerald-100 last:border-0">'
                f'<span class="text-slate-400 w-10 shrink-0">{yr}</span>'
                f'<span class="tag bg-emerald-50 text-emerald-700 shrink-0">教學</span>'
                f'<span class="text-slate-700 leading-snug">{ttl}'
                f'<span class="text-slate-400"> · {fld}{(" · " + dept) if dept else ""}</span></span>'
                f'</div>'
            )
        tpr_html = (
            f'<details class="rounded-lg border border-emerald-100 bg-emerald-50/30 px-3 py-1">'
            f'<summary class="text-xs font-medium text-emerald-700 cursor-pointer py-1 list-none">'
            f'🎓 教學實踐研究計畫 ({len(tpr_projects)}) ▾</summary>'
            f'<div class="mt-1">{"".join(rows)}</div></details>'
        )

    email_html = (
        f'<a href="mailto:{esc(email)}" class="text-xs text-slate-400 hover:text-blue-500 truncate">{esc(email)}</a>'
        if email else '<span class="text-xs text-slate-300">—</span>'
    )
    profile_html = (
        f'<a href="{esc(profile_url)}" target="_blank" rel="noopener" '
        f'class="text-xs text-blue-500 hover:underline shrink-0 flex items-center gap-0.5">'
        f'教師歷程<svg class="w-3 h-3 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
        f'd="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>'
        f'</svg></a>'
    ) if profile_url else ""

    search_corpus = " ".join([name, name_en, expertise]
                             + [" ".join((p.get("title","") or "").split()) for p in pubs]).lower()
    rank_order = RANK_ORDER.get(rank, 9)

    # email selection checkbox — placed next to email at bottom of card
    has_email = bool(email)
    checkbox_html = (
        f'<input type="checkbox" class="mail-select w-4 h-4 accent-blue-600 cursor-pointer shrink-0" '
        f'data-email="{esc(email)}" data-name="{esc(name)}" '
        f'onclick="event.stopPropagation(); toggleSel(this)" title="勾選以寄信">'
    ) if has_email else ''

    return (
        f'<div class="card relative bg-white rounded-xl shadow-sm border border-slate-100 p-4 flex flex-col gap-3" '
        f'data-rank="{esc(rank)}" data-areas="{esc(",".join(areas))}" '
        f'data-search="{esc(search_corpus[:500])}" data-rankorder="{rank_order}" data-pubs="{total}" '
        f'data-email="{esc(email)}" data-name="{esc(name)}" '
        f'data-tpr="{len(tpr_projects)}" '
        f'data-nstc="{len(nstc_projects)}" '
        f'data-group="{esc(group)}">'

        + f'<div class="flex items-start gap-3">'
        f'<div class="w-12 h-12 rounded-full {av_cls} flex items-center justify-center '
        f'text-base font-bold shrink-0">{esc(ini)}</div>'
        f'<div class="flex-1 min-w-0">'
        f'<div class="flex flex-wrap items-center gap-2">'
        f'<span class="font-semibold text-slate-800">{esc(name)}</span>'
        f'<span class="tag {rank_cls} font-medium">{esc(rank)}</span>'
        f'{group_tag}'
        f'</div>'
        f'<div class="text-xs text-slate-400">{esc(name_en)}</div>'
        f'<div class="flex flex-wrap gap-1 mt-1">{area_tags}</div>'
        + (f'<div class="text-xs text-slate-500 mt-1 leading-snug"><span class="text-slate-400">專長：</span>{esc(expertise)}</div>' if expertise else "")
        + f'</div>'
        f'<div class="text-right shrink-0 flex flex-col items-end gap-1">'
        f'<div>'
        f'<div class="text-xl font-bold text-blue-600 leading-none">{total}</div>'
        f'<div class="text-xs text-slate-400">篇著作</div>'
        f'</div>'
        + (
            f'<a href="{esc(schedule_url)}" target="_blank" rel="noopener" '
            f'class="text-xs text-emerald-600 hover:text-emerald-700 hover:underline inline-flex items-center gap-0.5 mt-1" '
            f'title="本學期課表">'
            f'<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            f'd="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>'
            f'</svg>本學期課表'
            f'</a>'
            if schedule_url else ""
        )
        + f'</div>'
        f'</div>'

        + (f'<div class="flex flex-wrap gap-1">{stat_chips}</div>' if stat_chips else "")

        + (
            f'<div class="border border-slate-100 rounded-lg px-3 py-1">{pub_block}{more_link}</div>'
            if pub_block else
            '<div class="text-xs text-slate-400 italic">暫無論著資料</div>'
        )

        + nstc_html
        + tpr_html

        + f'<div class="flex items-center justify-between gap-2 pt-1 border-t border-slate-50">'
        f'<div class="flex items-center gap-2 min-w-0 flex-1">{checkbox_html}{email_html}</div>'
        f'{profile_html}'
        f'</div>'

        f'</div>'
    )

# ── page template builder ─────────────────────────────────────────────────
JS_BLOCK = """
<script>
var activeRank = 'all';
var activeArea = 'all';
var activeGroup = 'all';
// Persist selections across dept pages via localStorage
var STORAGE_KEY = 'tku_faculty_mailsel_v1';
var selectedEmails = {};
try { selectedEmails = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch(e) { selectedEmails = {}; }

function saveSel() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedEmails)); } catch(e) {}
}

function updateMailBar() {
  var keys = Object.keys(selectedEmails);
  var n = keys.length;
  document.getElementById('selCount').textContent = n;
  var c2 = document.getElementById('selCount2');
  if (c2) c2.textContent = n > 0 ? '(' + n + ')' : '';
  // Count by dept (each entry stored as {name, dept})
  var deptCounts = {};
  keys.forEach(function(e) {
    var d = (selectedEmails[e] && selectedEmails[e].dept) || '其他';
    deptCounts[d] = (deptCounts[d] || 0) + 1;
  });
  var breakdown = Object.keys(deptCounts).map(function(d) { return d + ' ' + deptCounts[d]; }).join(' · ');
  var b = document.getElementById('selBreakdown');
  if (b) b.textContent = breakdown || '尚未選取';
  // Toggle disabled state for "send selected" button based on n
  var btnSel = document.getElementById('btnSendSelected');
  if (btnSel) {
    btnSel.disabled = n === 0;
    btnSel.classList.toggle('opacity-50', n === 0);
    btnSel.classList.toggle('cursor-not-allowed', n === 0);
  }
}

// Sync any checkboxes on the current page with stored selections
function syncCheckboxesFromStorage() {
  document.querySelectorAll('.mail-select').forEach(function(cb) {
    var em = cb.dataset.email;
    cb.checked = !!selectedEmails[em];
  });
}

var CURRENT_DEPT = window.CURRENT_DEPT || '';

function toggleSel(cb) {
  var email = cb.dataset.email;
  var name  = cb.dataset.name;
  if (!email) return;
  if (cb.checked) selectedEmails[email] = {name: name, dept: CURRENT_DEPT};
  else delete selectedEmails[email];
  saveSel();
  updateMailBar();
}

function selectAllVisible() {
  document.querySelectorAll('.card:not(.hidden-card) .mail-select').forEach(function(cb) {
    if (cb.dataset.email && !cb.checked) {
      cb.checked = true;
      selectedEmails[cb.dataset.email] = {name: cb.dataset.name, dept: CURRENT_DEPT};
    }
  });
  saveSel();
  updateMailBar();
}

function clearSel() {
  if (Object.keys(selectedEmails).length === 0) return;
  if (!confirm('將清除全部 ' + Object.keys(selectedEmails).length + ' 位選取（含其他系所頁面選取的）。是否繼續？')) return;
  selectedEmails = {};
  saveSel();
  document.querySelectorAll('.mail-select').forEach(function(cb) { cb.checked = false; });
  updateMailBar();
}

function sendMail() {
  var emails = Object.keys(selectedEmails);
  if (emails.length === 0) return;
  window.location.href = 'mailto:' + emails.join(',');
}

function showSelList() {
  var keys = Object.keys(selectedEmails);
  if (keys.length === 0) { alert('目前沒有選取任何教師'); return; }
  var byDept = {};
  keys.forEach(function(e) {
    var v = selectedEmails[e];
    var d = (v && v.dept) || '其他';
    byDept[d] = byDept[d] || [];
    byDept[d].push((v && v.name) + ' <' + e + '>');
  });
  var lines = [];
  Object.keys(byDept).sort().forEach(function(d) {
    lines.push('— ' + d + ' (' + byDept[d].length + ') —');
    byDept[d].forEach(function(s) { lines.push('  ' + s); });
  });
  alert('已選取 ' + keys.length + ' 位教師：\\n\\n' + lines.join('\\n'));
}

function applyFilters() {
  var q = document.getElementById('searchInput').value.trim().toLowerCase();
  var cards = document.getElementById('teacherGrid').querySelectorAll('.card');
  var visible = 0;
  cards.forEach(function(card) {
    var rank   = card.dataset.rank;
    var areas  = card.dataset.areas;
    var search = card.dataset.search;
    var matchRank   = activeRank === 'all' || rank === activeRank ||
                      (activeRank === '副教授' && (rank === '副教授' || rank === '約聘副教授')) ||
                      (activeRank === '教授' && (rank === '教授' || rank === '約聘專案教授' || rank === '專案教授'));
    var matchArea   = activeArea === 'all' || areas.split(',').indexOf(activeArea) >= 0;
    var matchGroup  = activeGroup === 'all' || card.dataset.group === activeGroup;
    var matchSearch = !q || search.indexOf(q) >= 0;
    if (matchRank && matchArea && matchGroup && matchSearch) {
      card.classList.remove('hidden-card'); visible++;
    } else {
      card.classList.add('hidden-card');
    }
  });
  document.getElementById('countDisplay').textContent = visible;
  document.getElementById('noResult').classList.toggle('hidden', visible > 0);
}

function setRank(rank, btn) {
  activeRank = rank;
  document.querySelectorAll('.rank-btn').forEach(function(b) {
    b.className = 'rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600';
  });
  btn.className = 'rank-btn active-rank px-3 py-1 rounded-lg text-xs font-medium bg-blue-600 text-white border border-blue-600';
  applyFilters();
}

function setArea(area, btn) {
  activeArea = area;
  document.querySelectorAll('.area-btn').forEach(function(b) {
    b.className = 'area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600';
  });
  btn.className = 'area-btn active-area px-3 py-1 rounded-lg text-xs font-medium bg-teal-600 text-white border border-teal-600';
  applyFilters();
}

function setGroup(g, btn) {
  activeGroup = g;
  document.querySelectorAll('.group-tab').forEach(function(b) {
    b.classList.remove('active-group');
    b.classList.add('text-slate-500');
  });
  btn.classList.add('active-group');
  btn.classList.remove('text-slate-500');
  applyFilters();
}

function applySort(mode) {
  var grid = document.getElementById('teacherGrid');
  var cards = Array.from(grid.querySelectorAll('.card'));
  if (mode === 'pubs') {
    cards.sort(function(a,b) { return parseInt(b.dataset.pubs||0) - parseInt(a.dataset.pubs||0); });
  } else if (mode === 'name') {
    cards.sort(function(a,b) { return a.dataset.search.localeCompare(b.dataset.search,'zh-TW'); });
  } else {
    cards.sort(function(a,b) { return parseInt(a.dataset.rankorder||9) - parseInt(b.dataset.rankorder||9); });
  }
  cards.forEach(function(c) { grid.appendChild(c); });
}

document.getElementById('searchInput').addEventListener('input', applyFilters);
// Sync stored selections + initialize counts on load
syncCheckboxesFromStorage();
updateMailBar();
applyFilters();  // initialize visible count
</script>
"""

def build_dept_page(cfg, data, dept_key):
    teaching_label = AREA_KW[dept_key]["teaching_label"]
    cards_html = "\n".join(render_card(t) for t in data)
    total = len(data)
    hdr = cfg["header_gradient"]

    # Cross-dept nav (always present at very top)
    NAV_LINKS = [
        ("faculty_hub.html", "🏠 總覽", "tflx"),  # hub
        ("tflx_teachers.html", "英文系", "tflx"),
        ("tfjx_teachers.html", "日文系", "tfjx"),
        ("tfox_teachers.html", "歐語系", "tfox"),
    ]
    nav_btns = []
    for href, label, key in NAV_LINKS:
        is_current = (key == dept_key and "hub" not in href)
        cls = "bg-white/20 text-white font-semibold" if is_current else "text-blue-100 hover:bg-white/10 hover:text-white"
        nav_btns.append(f'<a href="{href}" class="px-3 py-1 rounded-md text-sm {cls} transition-colors">{label}</a>')
    nav_html = (
        f'<nav class="bg-slate-900 text-white">'
        f'<div class="max-w-7xl mx-auto px-3 sm:px-4 py-2 flex flex-wrap gap-1 sm:gap-2 items-center">'
        + "".join(nav_btns)
        + '</div></nav>'
    )

    # Group tabs for TFOX (歐語系 has 4 sub-groups)
    group_tabs_html = ""
    if dept_key == "tfox":
        group_counts = {}
        for t in data:
            g = t.get("group", "")
            if g:
                group_counts[g] = group_counts.get(g, 0) + 1
        tabs = [("all", "全部", total)]
        for code, label in [("法文組", "法語"), ("德文組", "德文"),
                             ("西文組", "西語"), ("俄文組", "俄文")]:
            tabs.append((code, label, group_counts.get(code, 0)))
        btns = []
        for i, (code, label, n) in enumerate(tabs):
            active = "active-group" if i == 0 else "text-slate-500"
            btns.append(
                f'<button onclick="setGroup(\'{code}\',this)" '
                f'class="group-tab {active} relative px-5 py-2.5 text-sm font-medium border-b-2 border-transparent '
                f'hover:text-emerald-600 transition-colors">'
                f'{label}<span class="ml-1 text-xs text-slate-400">({n})</span>'
                f'</button>'
            )
        group_tabs_html = f"""
<div class="bg-white border-b border-slate-200">
  <div class="max-w-7xl mx-auto px-4 flex flex-wrap gap-1 items-center">
    {''.join(btns)}
  </div>
</div>
<style>
  .group-tab.active-group {{ color: #047857; border-bottom-color: #10b981; }}
</style>"""

    page = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>淡江大學{cfg['title']} — 專任師資查詢</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
body {{ font-family: 'Noto Sans TC', sans-serif; }}
.tag {{ display:inline-block; padding:1px 7px; border-radius:9999px; font-size:0.7rem; line-height:1.5; white-space:nowrap; }}
.card {{ transition:transform 0.15s,box-shadow 0.15s; }}
.card:hover {{ transform:translateY(-2px); box-shadow:0 8px 20px -4px rgba(0,0,0,.1); }}
.pub-row:hover {{ background:#f8fafc; }}
.pub-row {{ overflow-wrap:anywhere; word-break:break-word; }}
.hidden-card {{ display:none!important; }}
.card {{ min-width: 0; }}
</style>
</head>
<body class="bg-slate-50 min-h-screen">

<script>window.CURRENT_DEPT = "{cfg['title']}";</script>

{nav_html}

<header class="bg-gradient-to-r {hdr} text-white shadow-lg">
  <div class="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-5 flex flex-row items-center gap-3">
    <div class="flex-1 min-w-0">
      <div class="text-xs text-blue-300 mb-0.5">
        淡江大學 · 外國語文學院
      </div>
      <h1 class="text-xl sm:text-2xl font-bold tracking-wide">{cfg['title']} 專任師資</h1>
      <div class="text-xs text-blue-300 mt-0.5 hidden sm:block">資料來源：國科會研究人才資料庫 · 教師歷程系統</div>
    </div>
    <div class="text-right shrink-0">
      <div class="text-2xl sm:text-3xl font-bold" id="countDisplay">{total}</div>
      <div class="text-xs text-blue-300">位教師</div>
    </div>
  </div>
</header>

{group_tabs_html}

<div class="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-sm">
  <div class="max-w-7xl mx-auto px-3 sm:px-4 py-2.5 sm:py-3 flex flex-wrap gap-1.5 sm:gap-2 items-center">
    <div class="relative w-full sm:w-auto">
      <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
      </svg>
      <input type="search" id="searchInput" placeholder="搜尋姓名、論著關鍵字…"
        class="pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-blue-400">
    </div>
    <div class="flex gap-1.5 flex-wrap">
      <button onclick="setRank('all',this)"     class="rank-btn active-rank px-3 py-1 rounded-lg text-xs font-medium bg-blue-600 text-white border border-blue-600">全部</button>
      <button onclick="setRank('教授',this)"    class="rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">教授</button>
      <button onclick="setRank('副教授',this)"  class="rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">副教授</button>
      <button onclick="setRank('助理教授',this)" class="rank-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">助理教授</button>
    </div>
    <div class="flex gap-1.5 flex-wrap">
      <button onclick="setArea('all',this)"              class="area-btn active-area px-3 py-1 rounded-lg text-xs font-medium bg-teal-600 text-white border border-teal-600">所有領域</button>
      <button onclick="setArea('文學',this)"             class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">文學</button>
      <button onclick="setArea('語言學',this)"           class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">語言學</button>
      <button onclick="setArea('{teaching_label}',this)" class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">{teaching_label}</button>
      <button onclick="setArea('翻譯',this)"             class="area-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-300 text-slate-600">翻譯</button>
    </div>
    <select id="sortSelect" onchange="applySort(this.value)"
      class="ml-auto px-2 py-1.5 border border-slate-300 rounded-lg text-xs text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
      <option value="rank">排列：依職稱</option>
      <option value="pubs">排列：依論著數</option>
      <option value="name">排列：依姓名</option>
    </select>
  </div>
</div>

<main class="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-5 pb-32 sm:pb-24">
  <div id="noResult" class="hidden text-center py-24 text-slate-400"><p>找不到符合條件的教師</p></div>
  <div id="teacherGrid" class="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
{cards_html}
  </div>
</main>

<div id="mailBar" class="fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-slate-200 shadow-lg">
  <div class="max-w-7xl mx-auto px-3 py-2.5 sm:py-3 flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 sm:gap-3">
    <div class="text-sm text-slate-700 flex-1 min-w-0">
      <div>已勾選 <span id="selCount" class="font-bold text-blue-600 text-lg mx-1">0</span>位教師
        <span class="text-xs text-slate-400">（跨系所累計）</span>
      </div>
      <div id="selBreakdown" class="text-xs text-slate-500 mt-0.5 truncate">尚未選取</div>
    </div>
    <div class="flex flex-wrap items-center gap-1.5 sm:gap-2">
      <button onclick="showSelList()" class="px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50 whitespace-nowrap">
        檢視名單
      </button>
      <button onclick="selectAllVisible()" class="px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50 whitespace-nowrap">
        勾選本頁顯示中
      </button>
      <button onclick="clearSel()" class="px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50 whitespace-nowrap">
        清除全部
      </button>
      <button id="btnSendSelected" onclick="sendMail()" class="flex-1 sm:flex-none sm:ml-auto px-4 py-1.5 text-xs bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 whitespace-nowrap">
        ✉️ 寄給已勾選 <span id="selCount2" class="font-bold"></span>
      </button>
    </div>
  </div>
</div>

<footer class="text-center text-xs text-slate-400 py-6 border-t border-slate-200 mb-20">
  資料更新：每次重新爬蟲後生成 · 資料來源：
  <a href="https://nscpeople.onrender.com/" target="_blank" class="text-blue-400 hover:underline">國科會研究人才資料庫</a> ·
  <a href="{cfg['dept_list_url']}" target="_blank" class="text-blue-400 hover:underline">淡江教師歷程</a>
  {(' · <a href="' + cfg['dept_web'] + '" target="_blank" class="text-blue-400 hover:underline">' + cfg['title'] + '官網</a>') if cfg.get('dept_web') else ''}
</footer>

{JS_BLOCK}
</body>
</html>"""

    with open(cfg["out_file"], "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Built {cfg['out_file']} with {total} cards ({len(page)//1024}KB)")


# ── hub index page ─────────────────────────────────────────────────────────
def build_hub(depts_info):
    cards = []
    for d in depts_info:
        total = d["total"]
        has_pub = d["has_pub"]
        icon = d["icon"]
        title = d["title"]
        fname = d["out_file"]
        grad  = d["grad_light"]
        color = d["color"]
        avg   = f"{has_pub/total*100:.0f}%" if total else "0%"
        cards.append(f"""
    <a href="{fname}" class="group bg-white rounded-2xl shadow-md border border-slate-100 p-6
       hover:shadow-xl hover:-translate-y-1 transition-all duration-200 flex flex-col gap-4">
      <div class="w-14 h-14 rounded-xl {grad} flex items-center justify-center text-2xl">{icon}</div>
      <div>
        <div class="text-xs text-slate-400 mb-0.5">淡江大學 · 外國語文學院</div>
        <h2 class="text-xl font-bold text-slate-800 group-hover:{color}">{title}</h2>
      </div>
      <div class="flex gap-4 mt-auto">
        <div class="text-center">
          <div class="text-2xl font-bold {color}">{total}</div>
          <div class="text-xs text-slate-400">位教師</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold {color}">{has_pub}</div>
          <div class="text-xs text-slate-400">有著作紀錄</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold {color}">{avg}</div>
          <div class="text-xs text-slate-400">著作覆蓋率</div>
        </div>
      </div>
      <div class="text-sm text-blue-500 font-medium group-hover:underline">查看師資 →</div>
    </a>""")

    cards_html = "\n".join(cards)
    total_all = sum(d["total"] for d in depts_info)

    hub = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>淡江大學外國語文學院 — 師資查詢總覽</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
body {{ font-family: 'Noto Sans TC', sans-serif; }}
</style>
</head>
<body class="bg-slate-50 min-h-screen">

<header class="bg-gradient-to-r from-slate-900 to-slate-700 text-white shadow-lg">
  <div class="max-w-5xl mx-auto px-4 py-6 sm:py-8">
    <div class="text-sm text-slate-400 mb-1">淡江大學</div>
    <h1 class="text-2xl sm:text-3xl font-bold tracking-wide mb-1">外國語文學院 師資查詢</h1>
    <p class="text-slate-400 text-xs sm:text-sm">整合各系所專任師資資料：發表著作 · 國科會計畫 · 教學實踐計畫 · 教師歷程</p>
    <div class="mt-4 text-3xl sm:text-4xl font-bold text-white">{total_all}
      <span class="text-base sm:text-lg font-normal text-slate-400 ml-1">位專任教師</span>
    </div>
  </div>
</header>

<main class="max-w-5xl mx-auto px-4 py-6 sm:py-8">
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
{cards_html}
  </div>

  <div id="hubMailBox" class="hidden mt-8 bg-blue-50 border border-blue-200 rounded-2xl p-5 flex flex-wrap items-center gap-3">
    <div class="text-sm text-slate-700">
      <div class="font-medium">📧 跨系所選取的教師：<span id="hubMailCount" class="font-bold text-blue-700 text-lg">0</span> 位</div>
      <div id="hubMailBreakdown" class="text-xs text-slate-500 mt-1"></div>
    </div>
    <div class="ml-auto flex gap-2">
      <button onclick="hubShowList()" class="px-3 py-1.5 text-xs border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-100">檢視名單</button>
      <button onclick="hubClear()" class="px-3 py-1.5 text-xs border border-slate-300 text-slate-600 rounded-lg hover:bg-slate-50">清除</button>
      <button onclick="hubSend()" class="px-4 py-1.5 text-xs bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">✉️ 一次寄信給全部</button>
    </div>
  </div>

  <div class="mt-10 bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
    <h2 class="text-base font-semibold text-slate-700 mb-3">關於本系統</h2>
    <p class="text-sm text-slate-500 leading-relaxed mb-3">
      本查詢系統整合三個系所的專任師資資料，每週一凌晨自動更新。支援依姓名、論著關鍵字、專長搜尋，以及依職稱、研究領域、語組篩選。
    </p>
    <div class="text-sm text-slate-600">
      <div class="font-medium text-slate-700 mb-1.5">資料來源：</div>
      <ul class="space-y-1 text-xs text-slate-500 list-disc ml-5">
        <li>師資名單、Email、職等、專長：
          <a href="https://www.tflx.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">英文系</a>、
          <a href="https://www.tfjx.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">日文系</a>、
          <a href="https://www.tfox.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">歐語系</a>各系官網
          （含<a href="https://www.tffx.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">法文</a>／<a href="https://www.tfgx.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">德文</a>／<a href="https://www.tfsx.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">西文</a>／<a href="https://www.tfux.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">俄文</a> 4 組獨立站）</li>
        <li>發表著作：<a href="https://nscpeople.onrender.com/" target="_blank" class="text-blue-500 hover:underline">國科會研究人才資料庫</a></li>
        <li>國科會計畫：<a href="https://wsts.nstc.gov.tw/STSWeb/Award/AwardMultiQuery.aspx" target="_blank" class="text-blue-500 hover:underline">國家科學及技術委員會 學術補助獎勵查詢</a></li>
        <li>教學實踐計畫：<a href="https://tpr.moe.edu.tw/plan/result" target="_blank" class="text-blue-500 hover:underline">教育部教學實踐研究計畫專案計畫</a></li>
        <li>教師歷程、當學期課表：<a href="https://teacher.tku.edu.tw/" target="_blank" class="text-blue-500 hover:underline">淡江大學教師歷程系統</a></li>
      </ul>
    </div>
  </div>
</main>

<footer class="text-center text-xs text-slate-400 py-6 border-t border-slate-200 mt-8">
  淡江大學外國語文學院師資查詢系統
</footer>

<script>
var HUB_KEY = 'tku_faculty_mailsel_v1';
function hubLoad() {{
  try {{ return JSON.parse(localStorage.getItem(HUB_KEY) || '{{}}'); }} catch(e) {{ return {{}}; }}
}}
function hubSave(o) {{ try {{ localStorage.setItem(HUB_KEY, JSON.stringify(o)); }} catch(e) {{}} }}
function hubRender() {{
  var sel = hubLoad();
  var keys = Object.keys(sel);
  var box = document.getElementById('hubMailBox');
  if (keys.length === 0) {{ box.classList.add('hidden'); return; }}
  box.classList.remove('hidden');
  document.getElementById('hubMailCount').textContent = keys.length;
  var byDept = {{}};
  keys.forEach(function(e) {{
    var d = (sel[e] && sel[e].dept) || '其他';
    byDept[d] = (byDept[d] || 0) + 1;
  }});
  document.getElementById('hubMailBreakdown').textContent =
    Object.keys(byDept).map(function(d) {{ return d + ' ' + byDept[d]; }}).join(' · ');
}}
function hubSend() {{
  var sel = hubLoad();
  var keys = Object.keys(sel);
  if (keys.length === 0) return;
  window.location.href = 'mailto:' + keys.join(',');
}}
function hubClear() {{
  if (!confirm('清除全部選取？')) return;
  hubSave({{}}); hubRender();
}}
function hubShowList() {{
  var sel = hubLoad();
  var keys = Object.keys(sel);
  if (keys.length === 0) return;
  var byDept = {{}};
  keys.forEach(function(e) {{
    var v = sel[e]; var d = (v && v.dept) || '其他';
    byDept[d] = byDept[d] || [];
    byDept[d].push((v && v.name) + ' <' + e + '>');
  }});
  var lines = [];
  Object.keys(byDept).sort().forEach(function(d) {{
    lines.push('— ' + d + ' (' + byDept[d].length + ') —');
    byDept[d].forEach(function(s) {{ lines.push('  ' + s); }});
  }});
  alert('已選取 ' + keys.length + ' 位教師：\\n\\n' + lines.join('\\n'));
}}
hubRender();
</script>

</body>
</html>"""

    with open("faculty_hub.html", "w", encoding="utf-8") as f:
        f.write(hub)
    print(f"Built faculty_hub.html ({len(hub)//1024}KB)")


# ── department configs ─────────────────────────────────────────────────────
DEPTS = [
    {
        "key": "tflx",
        "data_file": "tflx_teachers_v2.json" if os.path.exists("tflx_teachers_v2.json") else "teachers_final.json",
        "out_file": "tflx_teachers.html",
        "title": "英文學系",
        "header_gradient": "from-blue-900 to-blue-700",
        "dept_list_url": "https://teacher.tku.edu.tw/TchrSmy.aspx?cd=TFLX",
        "dept_web": "https://www.tflx.tku.edu.tw/",
        # hub card display
        "icon": "英",
        "grad_light": "bg-blue-100 text-blue-700",
        "color": "text-blue-600",
    },
    {
        "key": "tfjx",
        "data_file": "tfjx_teachers_v2.json" if os.path.exists("tfjx_teachers_v2.json") else "tfjx_teachers_final.json",
        "out_file": "tfjx_teachers.html",
        "title": "日文學系",
        "header_gradient": "from-red-900 to-red-700",
        "dept_list_url": "https://teacher.tku.edu.tw/TchrSmy.aspx?cd=TFJX",
        "dept_web": "",
        "icon": "日",
        "grad_light": "bg-red-100 text-red-700",
        "color": "text-red-600",
    },
    {
        "key": "tfox",
        "data_file": "tfox_teachers_v2.json" if os.path.exists("tfox_teachers_v2.json") else "tfox_teachers_final.json",
        "out_file": "tfox_teachers.html",
        "title": "歐語學系",
        "header_gradient": "from-emerald-900 to-emerald-700",
        "dept_list_url": "https://teacher.tku.edu.tw/TchrSmy.aspx?cd=TFOX",
        "dept_web": "",
        "icon": "歐",
        "grad_light": "bg-emerald-100 text-emerald-700",
        "color": "text-emerald-600",
    },
]


def main():
    hub_info = []
    for cfg in DEPTS:
        if not os.path.exists(cfg["data_file"]):
            print(f"SKIP {cfg['key']}: {cfg['data_file']} not found")
            continue

        data = json.load(open(cfg["data_file"], encoding="utf-8"))
        dept_key = cfg["key"]

        for t in data:
            t["areas"] = infer_areas(t, dept_key)
            t["profileUrl"] = f"https://teacher.tku.edu.tw/StfTchrSmy.aspx?tid={t['uid']}"
            for p in t.get("publications", []):
                if p.get("title"):  p["title"]  = " ".join(p["title"].split())
                if p.get("source"): p["source"] = " ".join(p["source"].split())

        data.sort(key=lambda t: RANK_ORDER.get(t.get("rank",""), 9))
        build_dept_page(cfg, data, dept_key)

        has_pub = sum(1 for t in data if t.get("publications"))
        hub_info.append({**cfg, "total": len(data), "has_pub": has_pub})

    build_hub(hub_info)
    print("\nAll pages built!")


if __name__ == "__main__":
    main()
