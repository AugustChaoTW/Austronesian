# Mantel Test 結果報告

使用 Spearman 順位相關 + 9999 次置換検定。
處理距離矩陣非獨立性問題，避免直接報告普通相關系數的 p-value。

| 方法對 | r (Spearman) | p-value (permutation) | 語言對數 |
|--------|-------------|----------------------|----------|
| levenshtein_vs_sound_class | 0.7229 | 0.0001 | 4950 |
| levenshtein_vs_weighted | 0.8872 | 0.0001 | 4950 |
| sound_class_vs_weighted | 0.7990 | 0.0001 | 4950 |

## 診斷

所有方法對的 Mantel r 均顯著 > 0，置換 p < 0.05 表示距離穩健性。
高相關不等於更有語言學效度；需對照 Glottolog 樹來判斷。