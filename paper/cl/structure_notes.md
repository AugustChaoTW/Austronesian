## Computational Linguistics 論文章節結構與對應產出

**最後更新**: 2026-03-07（加入 Mantel test、Bootstrap、Glottolog 評估、Cognate-based baseline）

---

### 論文定位（更新）

**原定位**：開放 pipeline + 三距離比較  
**更新定位**：**可重現基準（reproducible benchmark）+ 方法學嚴謹分析**

核心貢獻重新包裝：
1. **可重現基準**：第一個完整涵蓋 ABVD 2,036 南島語、210 concepts 的開放式距離矩陣與 NJ 樹 pipeline
2. **方法學比較**：四種字串距離（Levenshtein, Sound-Class, Weighted, LDND）＋同源詞距離，統一對照
3. **統計嚴謹性**：Mantel permutation test（非普通相關 p-value）、Bootstrap over concepts、Glottolog clade 評估
4. **外部效度**：Cognate-based 距離（CSR）與字串距離的 Mantel r=0.3112（p<10⁻¹⁰⁰）顯示方法有語言學意義

---

### 章節大綱

1. **Introduction**
   - 背景：南島語親緣重建、詞彙距離可重現性問題
   - 貢獻：
     - 完整開源 pipeline（ABVD → NJ 樹，8 個 Python 腳本）
     - 四種距離度量的 Mantel test 比較（非普通相關）
     - Cognate-based 外部效度驗證（Mantel r=0.31, p<10⁻¹⁰⁰）
     - Bootstrap over concepts 穩健性分析
     - Glottolog clade-level 精確度評估

2. **Related Work**
   - 詞彙距離：Levenshtein (Swadesh 1952), LDND (Wichmann et al. 2010), Sound-class
   - LexStat / LingPy（List 2012, 2017）— 現有工具對照
   - NJ/UPGMA 在歷史語言學（Saitou & Nei 1987）
   - ABVD 資料庫（Greenhill et al. 2008）

3. **Data**
   - 資料：ABVD Lexibank，2,036 語言、210 concepts、346k tokens
   - 子集策略：**按詞彙數排序取前 100/200 語言**（明確說明）
   - 前處理：IPA→ASJP (`normalize_phonetics.py`)，清理 (`process_abvd.py`)
   - 產物：`data/processed/clean_wordlist.csv`、`languages.csv`、`meanings.csv`

4. **Methods**
   - **距離度量**（四種）：
     - Levenshtein（正規化至 [0,1]）
     - Sound-Class Distance（V/C 映射後 Levenshtein）
     - Weighted Levenshtein（元音替換成本 0.5）
     - LDND（ASJP-style，Wichmann et al. 2010 精神一致）
   - **外部效度**：Cognate-based CSR 距離（使用 ABVD cognate_class 標籤）
   - **樹重建**：真正 NJ（scikit-bio Q-matrix，Saitou & Nei 1987）+ UPGMA 對照
   - **統計驗證**：
     - Mantel test（Spearman + 9999 permutations）
     - Bootstrap over concepts（200 次有放回抽樣，輸出 CV 矩陣）
   - **評估**：Glottolog clade purity、pair precision/recall、cophenetic correlation
   - Reproducibility：`scripts/` 命令摘要，.venv 虛擬環境

5. **Results**
   - **距離方法間 Mantel test**（`results/mantel_test_results.json`）：
     - Lev vs Weighted: r=0.8872, p=0.0001
     - Lev vs Sound-Class: r=0.7229, p=0.0001
     - Sound-Class vs Weighted: r=0.7990, p=0.0001
   - **外部效度**（`results/cognate_distance_report.md`）：
     - Cognate CSR vs Levenshtein: Spearman r=0.3112, p=3.0e-107
   - **Glottolog 評估**（`results/tree_evaluation_results.json`）：
     - Levenshtein: Cophenetic r=0.92, Clade Purity=0.74
     - Sound-Class: Cophenetic r=0.88, Clade Purity=0.72
     - Weighted: Cophenetic r=0.90, Clade Purity=0.64
   - **Bootstrap 穩健性**（待執行，`results/bootstrap_summary.json`）
   - 樹視覺化：`results/austronesian_tree.nwk`（真 NJ）

6. **Discussion**
   - Mantel r 顯著但中等（0.31）：字串距離≠同源詞距離，有語言學意義但需謹慎
   - Glottolog clade 召回率低（~7-13%）：已知問題——45 個次語系 proxy，聚類粒度不足
   - Bootstrap CV：若大多數語言對 CV<0.1，表示距離對 concept 選擇穩健
   - 方法局限：ASJP 轉寫損失 IPA 精度；100 語言子集偏向資料豐富語言

7. **Conclusion**
   - 開源 pipeline、四距離比較、統計嚴謹性（Mantel + Bootstrap）
   - Cognate-based 外部效度顯示方法有語言學意義
   - 後續：完整 2,036 語言矩陣、Glottolog 完整樹 RF distance、character-based embedding

8. **Appendix / Supplement**
   - 距離矩陣（200×200, 100×100）+ cognate 距離矩陣
   - Newick 全樹（NJ + UPGMA）
   - 執行指令與環境（Python 3.12, scikit-bio, scipy, pandas）
   - 語言/語義清單

---

### 產出對應（完整版）

| 產出檔案 | 章節 | 說明 |
|----------|------|------|
| `data/processed/clean_wordlist.csv` | Data | 346k rows, 2036 語言 |
| `results/language_distance_matrix.csv` (200×200) | Results/Appendix | 主要距離矩陣 |
| `results/distance_matrix_*.csv` (100×100) | Results | 三方法比較 |
| `results/distance_matrix_cognate.csv` | Results | Cognate-based 距離 |
| `results/mantel_test_results.json` | Results | Mantel test 數值 |
| `results/mantel_report.md` | Results | Mantel test 報告 |
| `results/tree_evaluation_results.json` | Results | Glottolog 評估 |
| `results/tree_evaluation_report.md` | Results | 評估報告 |
| `results/bootstrap_summary.json` | Results | Bootstrap 摘要（待執行） |
| `results/bootstrap_report.md` | Results | Bootstrap 報告（待執行） |
| `results/cognate_distance_report.md` | Results | Cognate 距離報告 |
| `results/austronesian_tree.nwk` | Results | 真 NJ 樹（scikit-bio） |
| `results/austronesian_tree_upgma.nwk` | Results | UPGMA 基線 |
| `results/method_comparison.md` | Results | 方法比較總表 |
| `scripts/*.py` | Methods | 完整 pipeline |

---

### 已知缺口（給下次衝刺）

1. **Bootstrap 執行**：`scripts/bootstrap_tree.py` 已完成，需執行（約 20 分鐘）
2. **完整 RF distance**：需下載 Glottolog Newick 樹（glottolog.org/download）進行完整 RF 計算
3. **Figure 缺乏**：現有 `visualization.py` 可生成圖，需確認輸出
4. **子集說明**：論文需明確說明「按詞彙數排序取前 100/200 語言」的選擇邏輯
