# V1.4.3 中文釋義完整化

## 目的
修正大量單字顯示「中文釋義待補充」的問題。

## 新機制
網站會優先讀取：
`data/vocabulary-zh.json`

這個檔案由 GitHub Actions 自動產生，包含：
- 108 課綱 Level 1～6
- 原有 Level 7 補充字
- 詞性
- 繁體中文（台灣）釋義
- 釋義來源標記

## 上傳檔案
請覆蓋／新增：
- `app.js`
- `index.html`
- `sw.js`
- `data/vocabulary-zh.json`
- `tools/build_vocab_zh.py`
- `.github/workflows/build-vocab-zh.yml`

## 上傳後
進 GitHub：
Actions → Build vocabulary meanings → Run workflow

成功後，Action 會把完整 `data/vocabulary-zh.json` 自動 commit 回 main。

之後重新整理 GitHub Pages，即會優先使用本地中文字庫。
如果本地檔尚未建好，V1.4.3 仍會自動退回原本的線上字庫，不會讓網站直接壞掉。

## 不影響學習紀錄
`STORAGE_KEY` 仍維持 `hs7000-v1`，所以原有學習進度、錯題、收藏不會被清掉。
