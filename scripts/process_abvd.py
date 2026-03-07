#!/usr/bin/env python3
"""將 Lexibank ABVD CLDF 資料轉換為 clean CSV 格式."""

import pandas as pd
from pathlib import Path


def main():
    # 路徑設定
    data_dir = Path(__file__).parent.parent / "data"
    raw_dir = data_dir / "raw" / "cldf"
    processed_dir = data_dir / "processed"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("ABVD 資料轉換")
    print("=" * 60)
    
    # 讀取 CLDF 資料
    print("\n[1/3] 讀取語言資料...")
    languages = pd.read_csv(raw_dir / "languages.csv", comment="#")
    print(f"  語言數量: {len(languages)}")
    
    # 讀取詞彙資料
    print("\n[2/3] 讀取詞彙資料...")
    forms = pd.read_csv(raw_dir / "forms.csv", comment="#")
    print(f"  詞彙記錄數: {len(forms)}")
    
    # 讀取語義（概念）資料
    print("\n[3/3] 讀取語義資料...")
    parameters = pd.read_csv(raw_dir / "parameters.csv", comment="#")
    print(f"  語義數量: {len(parameters)}")
    
    # 合併資料
    print("\n[4/4] 合併與清理...")
    
    # 建立語言ID到名稱的映射
    lang_map = languages.set_index('ID')['Name'].to_dict()
    
    # 建立語義ID到名稱的映射
    param_map = parameters.set_index('ID')['Name'].to_dict()
    
    # 選擇需要的欄位並重新命名
    clean_df = forms[['Language_ID', 'Parameter_ID', 'Value', 'Form', 'Cognacy', 'Loan']].copy()
    clean_df.columns = ['language_id', 'meaning_id', 'form_raw', 'form', 'cognate_class', 'loan']
    
    # 映射語言名稱和語義名稱
    clean_df['language_name'] = clean_df['language_id'].map(lang_map)
    clean_df['meaning'] = clean_df['meaning_id'].map(param_map)
    
    # 去除空值
    original_count = len(clean_df)
    clean_df = clean_df.dropna(subset=['form', 'meaning'])
    clean_df = clean_df[clean_df['form'].str.strip() != '']
    clean_df = clean_df[clean_df['meaning'].str.strip() != '']
    cleaned_count = len(clean_df)
    
    print(f"  原始記錄: {original_count}")
    print(f"  清理後記錄: {cleaned_count} (移除 {original_count - cleaned_count} 個空值)")
    
    # 重新排列欄位順序
    clean_df = clean_df[['language_id', 'language_name', 'meaning_id', 'meaning', 
                        'form', 'form_raw', 'cognate_class', 'loan']]
    
    # 排序
    clean_df = clean_df.sort_values(['language_name', 'meaning'])
    
    # 輸出 clean_wordlist.csv
    output_file = processed_dir / "clean_wordlist.csv"
    clean_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n已儲存: {output_file}")
    
    # 輸出 languages.csv
    lang_df = languages[['ID', 'Name', 'Glottocode', 'ISO639P3code', 'Macroarea', 
                        'Latitude', 'Longitude', 'Family']].copy()
    lang_df.columns = ['id', 'name', 'glottocode', 'iso639_3', 'macroarea', 
                       'latitude', 'longitude', 'family']
    lang_output = processed_dir / "languages.csv"
    lang_df.to_csv(lang_output, index=False, encoding='utf-8')
    print(f"已儲存: {lang_output}")
    
    # 輸出 meanings.csv (parameters)
    meanings_df = parameters[['ID', 'Name', 'Concepticon_ID', 'Concepticon_Gloss']].copy()
    meanings_df.columns = ['id', 'name', 'concepticon_id', 'concepticon_gloss']
    meanings_output = processed_dir / "meanings.csv"
    meanings_df.to_csv(meanings_output, index=False, encoding='utf-8')
    print(f"已儲存: {meanings_output}")
    
    # 統計資訊
    print("\n" + "=" * 60)
    print("資料統計")
    print("=" * 60)
    print(f"\n涵蓋語言數: {clean_df['language_name'].nunique()}")
    print(f"涵蓋語義數: {clean_df['meaning'].nunique()}")
    print(f"總詞彙記錄數: {len(clean_df)}")
    
    # 區域分布
    lang_stats = clean_df.groupby('language_name').size().sort_values(ascending=False)
    print(f"\n前 10 大語言（詞彙數）:")
    for name, count in lang_stats.head(10).items():
        print(f"  - {name}: {count}")
    
    print("\n" + "=" * 60)
    print("轉換完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
