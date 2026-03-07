# 樹評估報告（Glottolog 5.3 對照）

使用 Glottolog 5.3 完整 Newick 樹評估 NJ 樹品質。
RF distance 為對照 Glottolog Austronesian 子樹的 Robinson-Foulds 距離（越低越好）。

| 方法 | Cophenetic r | Norm RF | Pair Precision | Pair Recall | F1 | Clade Purity |
|------|-------------|---------|----------------|-------------|-----|--------------|
| levenshtein | 0.9193 | 0.6875 | 0.2684 | 0.0631 | 0.1022 | 0.7465 |
| sound_class | 0.8760 | 0.7812 | 0.3281 | 0.1388 | 0.1951 | 0.6843 |
| weighted | 0.8970 | 0.6250 | 0.2678 | 0.0750 | 0.1172 | 0.7495 |

## 說明

- **Cophenetic r**: 樹的距離保真度（越高越好）
- **Norm RF**: Normalised Robinson-Foulds distance，對照 Glottolog 5.3（越低越好）
- **Pair Precision**: 在同一預測 cluster 的語言對中，真正同語系的比例
- **Pair Recall**: 同語系語言對中，被成功分到同一 cluster 的比例
- **Clade Purity**: 每個 Glottolog 組中，最多成員落在同一 predicted cluster 的比率

## 外部效度說明

Robinson-Foulds distance 直接對照 Glottolog 5.3 Austronesian 子樹，
為目前南島語系語言分類的黃金標準。
Normalised RF < 0.5 表示樹結構與 Glottolog 有相當程度的一致性。