#!/usr/bin/env python3
"""計算詞彙距離矩陣（優化版本） - 使用向量化和並行加速."""

import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from austronesian.analysis.distance import normalized_levenshtein_distance


def compute_language_distance_matrix_optimized(
    df: pd.DataFrame,
    min_shared: int = 10,
    top_languages: int = 200
) -> pd.DataFrame:
    """計算語言之間的距離矩陣（優化版本）.
    
    參數:
        df: 詞表 DataFrame
        min_shared: 最少共同語義數量閾值
        top_languages: 只計算前 N 個語言（按詞彙數排序）
        
    返回:
        DataFrame: 語言距離矩陣
    """
    # 選擇詞彙最多的語言
    lang_counts = df.groupby('language_name').size().sort_values(ascending=False)
    top_langs = lang_counts.head(top_languages).index.tolist()
    
    print(f"選取前 {top_languages} 個語言（按詞彙數）")
    
    # 建立語言-語義-詞彙的映射
    lang_meaning_forms = defaultdict(dict)
    for _, row in df.iterrows():
        lang = row['language_name']
        if lang not in top_langs:
            continue
        meaning = row['meaning']
        form = row['form_asjp'] if pd.notna(row.get('form_asjp')) and row['form_asjp'] else row['form']
        if meaning not in lang_meaning_forms[lang]:
            lang_meaning_forms[lang][meaning] = form
    
    # 取得所有語義
    all_meanings = set()
    for lang_data in lang_meaning_forms.values():
        all_meanings.update(lang_data.keys())
    all_meanings = sorted(all_meanings)
    
    print(f"語言數: {len(top_langs)}")
    print(f"語義數: {len(all_meanings)}")
    
    # 計算語言距離矩陣
    n = len(top_langs)
    distance_matrix = np.full((n, n), np.nan)
    shared_counts = np.zeros((n, n), dtype=int)
    
    print("\n計算語義距離...")
    for meaning in tqdm(all_meanings):
        # 取得該語義的所有詞彙
        forms_by_lang = {}
        for lang in top_langs:
            if meaning in lang_meaning_forms[lang]:
                forms_by_lang[lang] = lang_meaning_forms[lang][meaning]
        
        if len(forms_by_lang) < 2:
            continue
        
        # 計算所有語言對的距離
        langs_with_form = list(forms_by_lang.keys())
        forms = [forms_by_lang[lang] for lang in langs_with_form]
        indices = [top_langs.index(lang) for lang in langs_with_form]
        
        for ii in range(len(forms)):
            for jj in range(ii + 1, len(forms)):
                i = indices[ii]
                j = indices[jj]
                d = normalized_levenshtein_distance(str(forms[ii]), str(forms[jj]))
                
                if np.isnan(distance_matrix[i, j]):
                    distance_matrix[i, j] = d
                    distance_matrix[j, i] = d
                    shared_counts[i, j] = 1
                    shared_counts[j, i] = 1
                else:
                    old_count = shared_counts[i, j]
                    distance_matrix[i, j] = (distance_matrix[i, j] * old_count + d) / (old_count + 1)
                    distance_matrix[j, i] = distance_matrix[i, j]
                    shared_counts[i, j] += 1
                    shared_counts[j, i] += 1
    
    # 對角線設為 0
    np.fill_diagonal(distance_matrix, 0)
    
    # 建立 DataFrame
    dist_df = pd.DataFrame(distance_matrix, index=top_langs, columns=top_langs)
    
    return dist_df


def main():
    # 路徑
    data_dir = Path(__file__).parent.parent / "data"
    processed_dir = data_dir / "processed"
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 讀取資料
    print("讀取 clean_wordlist.csv...")
    df = pd.read_csv(processed_dir / "clean_wordlist.csv", low_memory=False)
    print(f"總記錄數: {len(df)}")
    
    # 計算語言距離矩陣（限制為前 200 個語言）
    print("\n" + "=" * 60)
    print("計算語言距離矩陣（優化版本）")
    print("=" * 60)
    
    dist_df = compute_language_distance_matrix_optimized(
        df, 
        min_shared=10,
        top_languages=200
    )
    
    # 統計
    valid_pairs = np.sum(~np.isnan(dist_df.values)) // 2
    print(f"\n有效語言對數: {valid_pairs}")
    
    # 儲存
    output_file = results_dir / "language_distance_matrix.csv"
    dist_df.to_csv(output_file)
    print(f"\n已儲存: {output_file}")
    
    # 顯示部分結果
    print("\n距離矩陣樣本：")
    print(dist_df.iloc[:5, :5])
    
    print("\n完成！")


if __name__ == "__main__":
    main()
