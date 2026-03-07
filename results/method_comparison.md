# 多方法比較實驗報告

**最後更新**: 2026-03-07

---

## 實驗設計

比較四種字串距離度量方法 ＋ 一種 cognate-based 外部效度基線：

1. **Levenshtein Distance**: 標準編輯距離（正規化至 [0,1]）
2. **Sound-Class Distance**: 將音素映射到發音類別（輔音 C / 元音 V）後計算距離
3. **Weighted Levenshtein**: 加權編輯距離（元音替換成本 0.5，較低）
4. **LDND (ASJP-style)**: Levenshtein Divided by Length Normalized Distance，與 Wichmann et al. (2010) 精神一致
5. **Cognate-based (CSR)**: 共享同源詞比率（使用 ABVD cognate_class 標籤），距離 = 1 - CSR

- 語言數: **100 語言**（按詞彙數排序取前 100）
- 語義數: **210 個 Swadesh concepts**

---

## 方法間 Mantel Test（Spearman + 9999 置換）

使用置換檢定評估方法間距離相關的顯著性，避免直接使用普通 p-value（距離矩陣非獨立）。

| 方法對 | Spearman r | p-value（置換） | 語言對數 |
|--------|-----------|----------------|----------|
| levenshtein vs sound_class | 0.7229 | 0.0001 | 4950 |
| levenshtein vs weighted | 0.8872 | 0.0001 | 4950 |
| sound_class vs weighted | 0.7990 | 0.0001 | 4950 |

> 所有方法對的 Mantel r 均顯著 > 0（p < 0.0001）。
> 高相關不等於更有語言學效度；需對照 Glottolog 樹來判斷。

---

## 外部效度：Cognate-based 距離 vs 字串距離

| 比較 | Spearman r | p-value |
|------|-----------|---------|
| Cognate CSR 距離 vs Levenshtein | **0.3112** | 3.0e-107 |

- 平均 CSR（共享同源率）：210 個語義均有 cognate 標籤
- **解讀**：字串距離與同源詞距離正相關（r=0.31），雖然中等強度，但在 4950 對語言中極顯著。
  這表示 Levenshtein 距離**確實能捕捉到部分語系關係**，但不是同源詞的直接代理。

---

## Glottolog 5.3 評估（Robinson-Foulds Distance + Clade Metrics）

使用 Glottolog 5.3 完整 Newick 樹進行外部效度評估。
45 個樣本語言（45/100）在 Glottolog Austronesian 子樹中找到精確匹配。

| 方法 | Cophenetic r | Norm RF | Pair Precision | Pair Recall | F1 | Clade Purity |
|------|-------------|---------|----------------|-------------|-----|--------------|
| Levenshtein | **0.9193** | 0.6875 | 0.2684 | 0.0631 | 0.1022 | **0.7465** |
| Sound-Class | 0.8760 | 0.7812 | **0.3281** | **0.1388** | **0.1951** | 0.6843 |
| Weighted | 0.8970 | **0.6250** | 0.2678 | 0.0750 | 0.1172 | 0.7495 |

**解讀**：
- **Norm RF**: Weighted 最低（0.625），表示與 Glottolog 拓撲最接近
- **Levenshtein** cophenetic r 最高（0.92），距離保真度最佳
- **Sound-Class** F1 最高（0.20），次語系分組稍優
- 以 45 個共享葉節點（45/100）對照 Glottolog 5.3 完整 Austronesian 子樹（2755 葉）
- 注意：RF 值對應 UPGMA 樹結構，非直接 NJ（skbio 在此環境不可用）
---

## 有效語言對數

| 方法 | 語言數 | 有效語言對 |
|------|--------|----------|
| levenshtein | 100 | 4950 |
| sound_class | 100 | 4950 |
| weighted | 100 | 4950 |
| cognate (CSR) | 100 | 4950（210 語義均有標籤）|

---

## 結論

1. **最穩健方法**：Levenshtein（最高 cophenetic r，最高 clade purity）
2. **最接近 Glottolog 拓撲**：Weighted（Norm RF=0.625，最低）
3. **Mantel test 確認**：三種字串距離方法高度一致（r=0.72-0.89），均顯著
4. **外部效度確認**：字串距離與 cognate-based 距離正相關（r=0.31, p<10⁻¹⁰⁰）
5. **RF distance 完成**：對照 Glottolog 5.3 Austronesian 子樹，45 個語言匹配，Norm RF=0.625–0.781

---

## 尚未執行的分析

- **Bootstrap over concepts**：✅ 已完成（`results/bootstrap_summary.json`）
  - CV=0.016，穩定對比率 99.98%
- **RF distance**：✅ 已完成（Glottolog 5.3 完整樹，45 個語言，Norm RF=0.625-0.781）
- **LDND 完整矩陣**：`compare_methods.py` 已加入 LDND，重新執行需 ~30 分鐘（非緊急）

---

## 輸出檔案清單

| 檔案 | 說明 |
|------|------|
| `distance_matrix_levenshtein.csv` | 100×100 Levenshtein 距離 |
| `distance_matrix_sound_class.csv` | 100×100 Sound-Class 距離 |
| `distance_matrix_weighted.csv` | 100×100 Weighted Levenshtein 距離 |
| `distance_matrix_cognate.csv` | 100×100 Cognate-based (CSR) 距離 |
| `language_distance_matrix.csv` | 200×200 Levenshtein 距離（主矩陣）|
| `mantel_test_results.json` | Mantel test 數值結果 |
| `mantel_report.md` | Mantel test 報告 |
| `tree_evaluation_results.json` | Glottolog 評估數值 |
| `tree_evaluation_report.md` | Glottolog 評估報告 |
| `cognate_distance_summary.json` | Cognate 距離統計摘要 |
| `cognate_distance_report.md` | Cognate 距離報告 |
| `austronesian_tree.nwk` | 真 NJ 樹（scikit-bio Q-matrix）|
| `austronesian_tree_upgma.nwk` | UPGMA 基線樹 |
