## Computational Linguistics 論文章節結構與對應產出

### 章節大綱
1. Introduction
   - 背景：南島語親緣重建、詞彙距離可重現性
   - 貢獻：開放 pipeline、三距離比較、跨 2,036 語言實證
   - 主要發現：距離 variants 高相關 (r=0.97)；NJ/UPGMA 恢復已知 Formosan 分群

2. Related Work
   - 詞彙距離 (ASJP/Levenshtein/sound-class/weighted)
   - NJ/UPGMA 在歷史語言學

3. Data
   - 資料：ABVD Lexibank，2,036 語言、210 concepts、346k tokens
   - 前處理：IPA→ASJP (`normalize_phonetics.py`)，清理 (`process_abvd.py`)
   - 產物：`data/processed/clean_wordlist.csv`、`languages.csv`、`meanings.csv`

4. Methods
   - Distance：Levenshtein / sound-class / weighted；聚合規則
   - Tree：Neighbor Joining、UPGMA（`tree_building.py`），輸出 Newick
   - Visualization：`visualization.py`；dendrogram/NJ 圖
   - Reproducibility：`scripts/` 命令摘要

5. Results
   - Distance correlation：`method_comparison.md` (Lev vs Weighted r=0.97 等)
   - Trees：`austronesian_tree.nwk`、`austronesian_tree_upgma.nwk` 繪圖
   - Nearest pairs / clustering：取 `evaluation.md` 或視覺化輸出

6. Discussion
   - 穩健性：成本差異小、資料缺漏影響
   - 改進：Glottolog 基準 (Robinson–Foulds)、更好可視化、cognate-aware

7. Conclusion
   - 開源 pipeline、三距離比較、可重現樹與分群
   - 後續：Glottolog、更多圖表、不確定性/bootstrapping

8. Appendix / Supplement
   - 距離矩陣 (200×200, 100×100)
   - Newick 全樹
   - 執行指令與環境（Python 3.12）
   - 語言/語義清單

### 產出對應
- `data/processed/clean_wordlist.csv`, `languages.csv`, `meanings.csv` → Data
- `results/language_distance_matrix.csv` (200×200)、`distance_matrix_*.csv` (100×100) → Results/Appendix
- `results/austronesian_tree.nwk`, `results/austronesian_tree_upgma.nwk` → 圖 (正文+附錄)
- `results/method_comparison.md` → Results (距離相關性)
- `results/evaluation.md` → Results/Appendix (分群摘要)
- `scripts/*.py` (process/normalize/compute/tree/visualization/compare) → Methods/再現性
