# 高中英文 7000｜V1.4.2 語料品質修正版

這個更新包只包含 V1.4.2 需要覆蓋的檔案，不會動到你網站其他功能與學習紀錄。

## 這版修正內容

1. **排除考卷固定題幹詞**
   - passage / following / question / blank / choose 等不再被當成「學測高頻單字」。
2. **詞形還原**
   - `made → make`
   - `used / using → use`
   - `studies → study`
   - 常見不規則變化也會合併。
3. **保留 surfaceForms**
   - JSON 仍會記錄一個 lemma 實際出現過哪些表面形式，方便之後查核。
4. **題型切分強化**
   - 可處理 PDF 擷取後中文標題中間被插入空白的狀況。
   - 分類：詞彙題、綜合測驗、文意選填、篇章結構、閱讀測驗、混合題、中譯英、英文作文。
5. **工作報告年份隔離**
   - 102、105～108 仍使用大考中心官方工作報告來源，但會先定位「英文考科」真正試卷區段，再做語料統計，避免後段報告內容污染詞頻。
6. **品質驗證**
   - Workflow 會檢查 15 年資料、語料量、題型覆蓋、boilerplate 洩漏與 lemma 回歸測試。

## 上傳方式

請覆蓋這兩個檔案：

- `.github/workflows/build-gsat-corpus.yml`
- `tools/build_gsat_corpus.py`

Commit 到 `main` 後，GitHub Actions 會因為這兩個路徑被修改而自動執行 **Build GSAT corpus**。

成功後，`data/gsat-corpus-stats.json` 會自動更新成：

```json
"version": "1.4.2"
```

網站原本 V1.4.1 的單字詳細頁可繼續讀取相同欄位：
`count`、`yearCount`、`years`、`byYear`、`sections`。
因此不需要重做整個前端。

## 建議檢查

Action 成功後可打開 `data/gsat-corpus-stats.json`，確認：

- `summary.papers = 15`
- `summary.sectionCoverageYears >= 8`
- `quality.lemmatized = true`
- `quality.boilerplateFiltered = true`
- `words` 中不應再有 `passage`、`following`、`questions` 等固定題幹詞
- `made` 應合併進 `make`
- `used` 應合併進 `use`
