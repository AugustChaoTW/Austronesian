#!/usr/bin/env python3
"""Cognate-based 距離計算 - 外部效度基線.

使用 ABVD 提供的 `cognate_class` 標籤計算語言對的
共享同源詞比例（Jaccard-style），作為與字串距離方法的外部對照。

共享同源比率（Cognate Sharing Rate, CSR）定義:
    CSR(L1, L2) = |shared_cognate_pairs| / |total_meaning_pairs|

其中 shared_cognate_pair：
    兩語言在同一 meaning 上具有相同（或重疊）的 cognate_class 標籤。

距離 = 1 - CSR (高 CSR = 語言親緣近 = 距離低)

用法:
    .venv/bin/python3 scripts/cognate_distance.py
"""

import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from scipy.stats import spearmanr


# ---------------------------------------------------------------------------
# 工具函式
# ---------------------------------------------------------------------------

def _parse_cognate_classes(raw: str) -> set[int]:
    """
    解析 cognate_class 欄位（可能是 '3' 或 '1, 15' 等）。
    返回 cognate class id 的集合。
    """
    if not raw or str(raw) == 'nan':
        return set()
    parts = re.split(r'[,\s]+', str(raw).strip())
    result = set()
    for p in parts:
        p = p.strip()
        if p and p.isdigit():
            result.add(int(p))
    return result


def _have_shared_cognate(cc1: set[int], cc2: set[int]) -> bool:
    """兩組 cognate classes 是否有交集（即為同源詞）."""
    return bool(cc1 & cc2)


# ---------------------------------------------------------------------------
# 主函式
# ---------------------------------------------------------------------------

def compute_cognate_distance_matrix(top_langs: int = 100) -> pd.DataFrame:
    """
    計算 top_langs 個語言的 cognate-based 距離矩陣。
    返回 DataFrame（distance = 1 - CSR）。
    """
    data_dir = Path(__file__).parent.parent / "data" / "processed"
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("讀取詞表資料...")
    df = pd.read_csv(data_dir / "clean_wordlist.csv", low_memory=False)

    # 選取前 top_langs 語言
    lang_counts = df.groupby('language_name').size().sort_values(ascending=False)
    langs = lang_counts.head(top_langs).index.tolist()
    print(f"使用語言數: {len(langs)}")

    # 建立 lang → meaning → cognate_classes 索引
    lang_meaning_cognates: dict = defaultdict(dict)
    for _, row in df.iterrows():
        lang = row['language_name']
        if lang not in langs:
            continue
        meaning = row['meaning']
        cognate_set = _parse_cognate_classes(row.get('cognate_class', ''))
        if cognate_set:
            # 一個 meaning 下若有多個記錄，合併 cognate classes
            if meaning in lang_meaning_cognates[lang]:
                lang_meaning_cognates[lang][meaning] |= cognate_set
            else:
                lang_meaning_cognates[lang][meaning] = cognate_set

    all_meanings = sorted(set().union(*[set(d.keys()) for d in lang_meaning_cognates.values()]))
    print(f"具 cognate 標籤的語義數: {len(all_meanings)}")

    # 計算距離矩陣
    n = len(langs)
    shared_counts = np.zeros((n, n), dtype=int)
    total_counts = np.zeros((n, n), dtype=int)
    lang_idx = {lang: i for i, lang in enumerate(langs)}

    print("計算 cognate sharing rate...")
    for meaning in tqdm(all_meanings):
        pairs = [(lang, lang_meaning_cognates[lang][meaning])
                 for lang in langs
                 if meaning in lang_meaning_cognates.get(lang, {})]
        if len(pairs) < 2:
            continue
        for ii in range(len(pairs)):
            for jj in range(ii + 1, len(pairs)):
                la, cc1 = pairs[ii]
                lb, cc2 = pairs[jj]
                i, j = lang_idx[la], lang_idx[lb]
                total_counts[i, j] += 1
                total_counts[j, i] += 1
                if _have_shared_cognate(cc1, cc2):
                    shared_counts[i, j] += 1
                    shared_counts[j, i] += 1

    # CSR 矩陣，避免除以零
    with np.errstate(invalid='ignore'):
        csr = np.where(total_counts > 0, shared_counts / total_counts, np.nan)

    # 距離 = 1 - CSR
    distance_mat = 1.0 - csr
    np.fill_diagonal(distance_mat, 0.0)

    dist_df = pd.DataFrame(distance_mat, index=langs, columns=langs)

    # 輸出
    output_path = results_dir / "distance_matrix_cognate.csv"
    dist_df.to_csv(output_path)
    print(f"\n已儲存: {output_path}")

    # 摘要統計
    upper = distance_mat[np.triu_indices(n, k=1)]
    upper_csr = csr[np.triu_indices(n, k=1)]
    valid = ~np.isnan(upper)
    summary = {
        "n_languages": n,
        "n_meanings_with_cognates": len(all_meanings),
        "n_valid_pairs": int(np.sum(valid)),
        "mean_csr": float(np.nanmean(upper_csr)),
        "std_csr": float(np.nanstd(upper_csr)),
        "mean_cognate_distance": float(np.nanmean(upper[valid])),
        "median_cognate_distance": float(np.nanmedian(upper[valid])),
    }

    # 與其他距離方法的 Spearman 相關
    print("\n計算與 Levenshtein 距離的 Mantel 相關...")
    lev_df = pd.read_csv(results_dir / "distance_matrix_levenshtein.csv", index_col=0)
    lev_df = lev_df.reindex(index=langs, columns=langs)
    lev_upper = lev_df.values[np.triu_indices(n, k=1)]

    mask = valid & ~np.isnan(lev_upper)
    if mask.sum() > 10:
        r, p = spearmanr(upper[mask], lev_upper[mask])
        summary["mantel_r_vs_levenshtein"] = float(r)
        summary["mantel_p_vs_levenshtein"] = float(p)
        print(f"  Spearman r vs Levenshtein: {r:.4f} (p={p:.4e})")

    json_path = results_dir / "cognate_distance_summary.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    _write_report(summary, dist_df, results_dir)
    return dist_df


def _write_report(summary: dict, dist_df: pd.DataFrame, results_dir: Path):
    # 找出最近/最遠的語言對
    n = len(dist_df)
    langs = dist_df.index.tolist()
    mat = dist_df.values
    upper = [(mat[i, j], langs[i], langs[j])
             for i in range(n) for j in range(i + 1, n)
             if not np.isnan(mat[i, j])]
    upper_sorted = sorted(upper)

    closest = upper_sorted[:5]
    farthest = upper_sorted[-5:]

    lines = [
        "# Cognate-based 距離報告",
        "",
        "使用 ABVD cognate_class 標籤計算語言對的共享同源詞比率（CSR）。",
        "距離 = 1 - CSR；0 = 所有比較語義均為同源，1 = 無任何同源詞。",
        "",
        "## 統計摘要",
        "",
        f"- 語言數: {summary['n_languages']}",
        f"- 具同源標籤的語義數: {summary['n_meanings_with_cognates']}",
        f"- 有效語言對數: {summary['n_valid_pairs']}",
        f"- 平均 CSR: {summary['mean_csr']:.4f}",
        f"- CSR 標準差: {summary['std_csr']:.4f}",
        f"- 平均 cognate 距離: {summary['mean_cognate_distance']:.4f}",
        "",
    ]

    if "mantel_r_vs_levenshtein" in summary:
        lines += [
            "## 外部效度：與 Levenshtein 距離的 Spearman 相關",
            "",
            f"- Mantel r = {summary['mantel_r_vs_levenshtein']:.4f}",
            f"- p-value = {summary['mantel_p_vs_levenshtein']:.4e}",
            "",
            "> 若 r 顯著 > 0，表示字串距離能捕捉到真實語系關係。",
            "",
        ]

    lines += [
        "## 最近語言對（最多同源詞）",
        "",
        "| 距離 | 語言 A | 語言 B |",
        "|------|--------|--------|",
    ]
    for d, la, lb in closest:
        lines.append(f"| {d:.4f} | {la} | {lb} |")

    lines += [
        "",
        "## 最遠語言對（最少同源詞）",
        "",
        "| 距離 | 語言 A | 語言 B |",
        "|------|--------|--------|",
    ]
    for d, la, lb in farthest:
        lines.append(f"| {d:.4f} | {la} | {lb} |")

    report_path = results_dir / "cognate_distance_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"已儲存報告: {report_path}")


if __name__ == "__main__":
    dist_df = compute_cognate_distance_matrix(top_langs=100)
    print("\n完成！")
