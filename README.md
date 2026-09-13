# 高中英文 7000 字學習系統 V1.0

## 功能
- 108 課綱高中英文參考詞彙 Level 1–6
- 舊制高中字表差集作為進階補充層（最多 1,000 字）
- 每日新字、到期複習、簡化間隔重複
- 英文發音（瀏覽器 Web Speech API）
- 英→中測驗、錯題本
- 字庫搜尋與級別篩選
- 本機學習紀錄、匯出/匯入
- PWA，可加入 iPhone 主畫面

## GitHub Pages
將整個資料夾上傳到 GitHub repository 根目錄，Settings → Pages → Deploy from a branch → main / root。

## 字庫資料來源
1. 大考中心《高中英文參考詞彙表（111學年度起適用）》整理 JSON：EngTW/English-for-Programmers
2. 舊制「大學學測4000字及指考7000字」公開整理：mahavivo/english-wordlists

本專案預設於瀏覽器執行時下載字庫；第一次成功載入後 Service Worker 會快取資料。

## 注意
V1 中文釋義優先以舊制字表對照。108 新增、但舊制字表沒有對應的少數詞，會顯示「中文釋義待補充」。V1.1 可再補齊完整中文釋義、字根字首、固定搭配與更多例句。
