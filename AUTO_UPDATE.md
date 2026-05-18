# 每週自動更新說明

## ⏰ 排程資訊

| 項目 | 內容 |
|---|---|
| **Workflow 名稱** | Update Faculty Data |
| **狀態** | active ✅ |
| **Cron 設定** | `0 17 * * 0` |
| **執行時間** | 每週日 17:00 UTC＝**每週一 01:00 Taipei** |
| **第一次自動執行** | 下週一凌晨 1 點 |
| **手動觸發頁面** | [Run workflow](https://github.com/kellytseng-beep/tku-faculty-search/actions/workflows/update-faculty.yml)（右上角有 **Run workflow** 按鈕） |

## 🔁 每週做什麼

1. **重抓各系官網** → 偵測新進/離職/**職等變化**（log 會用 `⚡ RANK CHANGED` 標出）
2. **重抓歐語 4 組獨立站**（法/德/西/俄）
3. **重抓 NSC 著作** → 新發表的論文自動加入
4. **重抓 TPR 教學實踐計畫**
5. **重抓 NSTC 國科會計畫**
6. **重建 HTML**
7. **自動 `git commit` + `git push`** → GitHub Pages 同步更新

## 💡 補充

- 你關電腦完全沒影響，cron 跑在 GitHub 雲端
- 想要永久排除某位老師時，直接編輯 [`excluded_teachers.json`](excluded_teachers.json)
- 想看更新紀錄：[Actions 頁面](https://github.com/kellytseng-beep/tku-faculty-search/actions)

## 🌐 公開網址

- **總覽**：<https://kellytseng-beep.github.io/tku-faculty-search/faculty_hub.html>
- 英文系：<https://kellytseng-beep.github.io/tku-faculty-search/tflx_teachers.html>
- 日文系：<https://kellytseng-beep.github.io/tku-faculty-search/tfjx_teachers.html>
- 歐語系：<https://kellytseng-beep.github.io/tku-faculty-search/tfox_teachers.html>

> 第一次推到 GitHub 後，Pages 部署大約需要 1-2 分鐘才會生效。
