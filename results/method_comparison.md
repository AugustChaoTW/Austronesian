# 多方法比較實驗報告

## 實驗設計

比較三種距離度量方法：

1. **Levenshtein Distance**: 標準編輯距離
2. **Sound-Class Distance**: 將音素映射到發音類別（輔音/元音）後計算距離
3. **Weighted Levenshtein**: 加權編輯距離（元音替換成本較低）

## 結果

| 方法 | 語言數 | 有效語言對 |
|------|--------|----------|
| levenshtein | 100 | 5000 |
| sound_class | 100 | 5000 |
| weighted | 100 | 5000 |

## 方法相關性

- levenshtein_vs_sound_class: r = 0.8522
- levenshtein_vs_weighted: r = 0.9714
- sound_class_vs_weighted: r = 0.8706

## 結論

Sound-class 距離與加權 Levenshtein 距離在發音相似性上有類似假設。建議使用加權 Levenshtein 距離作為主要方法。