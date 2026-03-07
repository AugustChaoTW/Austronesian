#!/usr/bin/env python3
"""ABVD 資料下載腳本 - 從 Austronesian Basic Vocabulary Database 下載語料."""

import json
import time
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from austronesian.databases.abvd import ABVDClient


def main():
    # 設定路徑
    data_dir = Path(__file__).parent.parent / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 建立 ABVD client (延遲設為 0.3 秒，避免過度負載伺服器)
    client = ABVDClient(delay=0.3)
    
    print("=" * 60)
    print("ABVD 資料下載")
    print("=" * 60)
    
    # Step 1: 下載所有語言元資料
    print("\n[1/4] 取得語言列表...")
    languages_file = raw_dir / "languages.json"
    
    if languages_file.exists():
        print(f"  已存在: {languages_file}")
        with open(languages_file, "r", encoding="utf-8") as f:
            languages = json.load(f)
    else:
        languages = client.list_languages()
        lang_data = [
            {
                "id": lang.id,
                "name": lang.name,
                "family": lang.family,
                "subfamily": lang.subfamily,
                "glottocode": lang.glottocode,
                "iso639_3": lang.iso639_3,
                "region": lang.region,
                "latitude": lang.latitude,
                "longitude": lang.longitude,
                "notes": lang.notes,
            }
            for lang in languages
        ]
        with open(languages_file, "w", encoding="utf-8") as f:
            json.dump(lang_data, f, ensure_ascii=False, indent=2)
        print(f"  已儲存: {languages_file}")
    
    print(f"  共有 {len(languages)} 個語言")
    
    # Step 2: 下載所有詞彙資料
    print("\n[2/4] 下載詞彙資料（這需要一些時間...）")
    words_file = raw_dir / "all_words.json"
    
    if words_file.exists():
        print(f"  已存在: {words_file}")
        with open(words_file, "r", encoding="utf-8") as f:
            all_words = json.load(f)
    else:
        all_words = []
        
        # 依區域分組顯示進度
        regions = {}
        for lang in languages:
            region = lang.region or "Unknown"
            if region not in regions:
                regions[region] = []
            regions[region].append(lang)
        
        total_langs = len(languages)
        
        for i, lang in enumerate(tqdm(languages, desc="  下載詞彙")):
            try:
                words = client.get_words(lang.id)
                for w in words:
                    all_words.append({
                        "language_id": w.language_id,
                        "language_name": w.language_name,
                        "word_id": w.word_id,
                        "meaning": w.meaning,
                        "form": w.form,
                        "phonemic": w.phonemic,
                        "cognate_class": w.cognate_class,
                        "loan": w.loan,
                    })
            except Exception as e:
                print(f"  警告: 語言 {lang.id} ({lang.name}) 下載失敗: {e}")
                continue
            
            # 每 50 個語言儲存一次（避免記憶體問題）
            if (i + 1) % 50 == 0:
                with open(words_file, "w", encoding="utf-8") as f:
                    json.dump(all_words, f, ensure_ascii=False)
                print(f"  [進度 {i+1}/{total_langs}] 已暫存")
        
        # 最終儲存
        with open(words_file, "w", encoding="utf-8") as f:
            json.dump(all_words, f, ensure_ascii=False, indent=2)
        print(f"  已儲存: {words_file}")
    
    print(f"  共有 {len(all_words)} 個詞彙記錄")
    
    # Step 3: 轉換為 DataFrame 並清理
    print("\n[3/4] 資料清理...")
    df = pd.DataFrame(all_words)
    
    # 移除空值
    original_count = len(df)
    df = df.dropna(subset=["form", "meaning"])
    df = df[df["form"].str.strip() != ""]
    df = df[df["meaning"].str.strip() != ""]
    cleaned_count = len(df)
    
    print(f"  原始記錄: {original_count}")
    print(f"  清理後記錄: {cleaned_count} (移除 {original_count - cleaned_count} 個空值)")
    
    # 顯示語言統計
    lang_stats = df.groupby("language_name").size().sort_values(ascending=False)
    print(f"  涵蓋語言數: {len(lang_stats)}")
    print(f"  前 10 大語言:")
    for name, count in lang_stats.head(10).items():
        print(f"    - {name}: {count} 個詞彙")
    
    # Step 4: 儲存 clean_wordlist.csv
    print("\n[4/4] 儲存 clean_wordlist.csv...")
    output_file = processed_dir / "clean_wordlist.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"  已儲存: {output_file}")
    
    # 額外輸出：languages.csv
    langs_output = processed_dir / "languages.csv"
    lang_df = pd.DataFrame([
        {
            "id": lang.id,
            "name": lang.name,
            "family": lang.family,
            "subfamily": lang.subfamily,
            "glottocode": lang.glottocode,
            "iso639_3": lang.iso639_3,
            "region": lang.region,
            "latitude": lang.latitude,
            "longitude": lang.longitude,
        }
        for lang in languages
    ])
    lang_df.to_csv(langs_output, index=False, encoding="utf-8")
    print(f"  已儲存: {langs_output}")
    
    print("\n" + "=" * 60)
    print("下載完成！")
    print("=" * 60)
    print(f"\n輸出檔案:")
    print(f"  - {languages_file}")
    print(f"  - {words_file}")
    print(f"  - {output_file}")
    print(f"  - {langs_output}")


if __name__ == "__main__":
    main()
