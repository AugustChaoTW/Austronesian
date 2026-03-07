## Computational Linguistics (CL) 投稿模板

- 已下載官方最新版樣式檔（2025-01-01）：
  - `clv2025.cls`
  - `compling.bst`
  - `COLI_template.tex` / `COLI_template.pdf`
  - `COLI_template.bib`
- 來源（官方 Style Guide）: https://submissions.cljournal.org/index.php/cljournal/StyleGuide
- 重要：避免使用舊版 `clv3`；投稿請採用 `\documentclass[manuscript]{clv2025}`（初稿建議 manuscript 模式以產生雙倍行距與行號）。

### 建議目錄結構

```
paper/cl/
├── clv2025.cls
├── compling.bst
├── COLI_template.tex  # 可複製為稿件主文件
├── COLI_template.bib  # 參考文獻範例
├── COLI_template.pdf  # 官方示例
└── figures/           # 請放置圖檔
```

### 使用提示

1. 編譯：建議 pdfLaTeX；若用 ArabTeX，需加 `alocal.sty`（未隨附）。
2. 作者/機構：`clv2025` 已優化多作者/多機構格式；依手冊填寫 `\author{}` 與 `\affil{}`。
3. 與 ACL 會議樣式不同：`clv2025` 是單欄期刊格式，不可混用 `acl.sty`。
4. 投稿前再確認官方連結是否有更新日期（目前為 2025-01-01 標記）。
