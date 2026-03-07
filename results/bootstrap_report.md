# Bootstrap over Concepts 報告

- Bootstrap 次數: 200
- 語言數: 100
- 語義數: 210

## 距離穩定性

| 指標 | 值 |
|------|-----|
| 穩定語言對比率 (CV < 0.1) | 1.000 |
| 不穩定語言對比率 (CV > 0.5) | 0.000 |
| 平均 CV | 0.0159 |
| 中位數 CV | 0.0147 |

## 解讀

CV（變異係數）越低，表示對 concept 抽樣越穩健。
穩定對比率高（>80%）表示距離矩陣具 bootstrap 可信度。

## 輸出檔案

- `bootstrap_distance_mean.csv`：bootstrap 平均距離矩陣
- `bootstrap_distance_std.csv`：標準差矩陣
- `bootstrap_distance_cv.csv`：變異係數矩陣
- `bootstrap_consensus_tree.nwk`：基於平均矩陣的 NJ 共識樹