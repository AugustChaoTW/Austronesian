#!/usr/bin/env python3
"""將 ASJP 轉寫正規化應用於詞表資料."""

import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from austronesian.analysis.phonetics import normalize_asjp, extract_asjp_word


def main():
    data_dir = Path(__file__).parent.parent / "data"
    processed_dir = data_dir / "processed"
    
    # 讀取 clean_wordlist.csv
    print("讀取 clean_wordlist.csv...")
    df = pd.read_csv(processed_dir / "clean_wordlist.csv", low_memory=False)
    print(f"總記錄數: {len(df)}")
    
    # 產生 ASJP 形式
    print("\n產生 ASJP 轉寫...")
    df['form_asjp'] = df['form'].apply(lambda x: extract_asjp_word(str(x)) if pd.notna(x) else "")
    
    # 顯示範例
    print("\n轉換範例：")
    samples = df[['language_name', 'meaning', 'form', 'form_asjp']].sample(10, random_state=42)
    for _, row in samples.iterrows():
        print(f"  {row['form']:20} -> {row['form_asjp']:20} ({row['language_name'][:15]})")
    
    # 統計
    non_empty = df[df['form_asjp'].str.len() > 0]
    print(f"\n有效 ASJP 記錄: {len(non_empty)}/{len(df)} ({100*len(non_empty)/len(df):.1f}%)")
    
    # 儲存
    output_file = processed_dir / "clean_wordlist.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n已更新: {output_file}")
    
    print("\n完成！")


if __name__ == "__main__":
    main()
