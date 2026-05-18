# 淡江大學外國語文學院師資查詢系統

整合英文系、日文系、歐語系（法/德/西/俄）共 88 位專任教師的：
- 發表著作（國科會研究人才資料庫）
- 國科會研究計畫
- 教學實踐研究計畫
- 當學期課表（淡江教師歷程）

## 線上頁面

- 總覽：[faculty_hub.html](faculty_hub.html)
- 英文系：[tflx_teachers.html](tflx_teachers.html) （30 位）
- 日文系：[tfjx_teachers.html](tfjx_teachers.html) （22 位）
- 歐語系：[tfox_teachers.html](tfox_teachers.html) （37 位，含 4 組別 tab）

## 功能

- 依姓名、論著關鍵字、專長搜尋
- 依職稱、研究領域、語組（歐語系）篩選
- 寄信：單選、多選、跨系所累計（用 `localStorage` 保留選取）
- 手機／平板／桌機 RWD

## 自動更新

每週一 01:00 (Taipei) 由 GitHub Actions 自動重抓資料並 commit。詳見 [.github/workflows/update-faculty.yml](.github/workflows/update-faculty.yml)。

可手動觸發：GitHub repo → Actions → "Update Faculty Data" → "Run workflow"。

職等變更會在工作流程 log 中以 `⚡ RANK CHANGED:` 標記出來。

### 永久排除教師

編輯 [`excluded_teachers.json`](excluded_teachers.json) 加入要永久排除的姓名，下次自動更新時不會被加回。

## 資料來源

| 來源 | 用途 |
|---|---|
| [tflx/tfjx/tfox.tku.edu.tw](https://www.tflx.tku.edu.tw/) | 各系專任師資頁（姓名、職等、email、專長） |
| [tffx/tfgx/tfsx/tfux.tku.edu.tw](https://www.tffx.tku.edu.tw/) | 歐語系 4 組（法/德/西/俄）獨立網站 |
| [teacher.tku.edu.tw](https://teacher.tku.edu.tw/) | 教師歷程、當學期課表 |
| [nscpeople.onrender.com](https://nscpeople.onrender.com/) | 國科會研究人才資料庫的著作 |
| [tpr.moe.edu.tw](https://tpr.moe.edu.tw/plan/result) | 教學實踐研究計畫 |
| [wsts.nstc.gov.tw](https://wsts.nstc.gov.tw/STSWeb/Award/AwardMultiQuery.aspx) | 國科會補助研究計畫 |

## 本地手動執行

```bash
pip install requests beautifulsoup4

# 完整重抓並重建（約 15-20 分鐘）
python scrape_dept_sites.py    # 各系官網（roster + email + 職等）
python merge_dept_data.py       # 合併資料、偵測職等變化
python fix_missing.py           # 4 組別細項
python refresh_publications.py  # 重抓 NSC 著作
python scrape_tpr.py            # TPR 計畫
python scrape_nstc.py           # NSTC 計畫
python build_all_depts.py       # 重建 HTML
```

開啟 `faculty_hub.html` 即可使用。
