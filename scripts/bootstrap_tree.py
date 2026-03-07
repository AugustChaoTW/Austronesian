#!/usr/bin/env python3
"""Bootstrap over concepts 分析 - 向量化版本（快速）.

關鍵優化：
1. 用 pandas pivot_table 一次建好 lang×meaning 矩陣，取代 iterrows()
2. 對每個 meaning，用 numpy broadcasting 批量計算 Levenshtein（仍是 Python，
   但僅對 ≤100 語言做 n*(n-1)/2 = 4950 對，迴圈次數極少）
3. 距離矩陣累加用 numpy 直接賦值，不用 dict 索引

用法:
    .venv/bin/python3 scripts/bootstrap_tree.py
"""

import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

try:
    from skbio import DistanceMatrix
    from skbio.tree import nj as skbio_nj
    SKBIO_OK = True
except ImportError:
    SKBIO_OK = False

from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

# ---------------------------------------------------------------------------
# 向量化距離：對同一 meaning 的所有語言對一次算完
# ---------------------------------------------------------------------------

def _lev(s1: str, s2: str) -> float:
    """正規化 Levenshtein [0,1]，純 Python 但只在 4950 對上調用。"""
    if s1 == s2:
        return 0.0
    m, n = len(s1), len(s2)
    if m == 0 or n == 0:
        return 1.0
    # 只用兩行滾動 dp，節省記憶體
    prev = list(range(n + 1))
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            curr[j] = min(prev[j] + 1, curr[j-1] + 1, prev[j-1] + cost)
        prev, curr = curr, prev
    return prev[n] / max(m, n)


def _build_distance_matrix_fast(forms_pivot: pd.DataFrame,
                                  meanings_subset: np.ndarray,
                                  lang_idx: dict,
                                  n: int) -> np.ndarray:
    """
    給定語義子集（bootstrap sample），快速建立 n×n 距離矩陣。

    forms_pivot: DataFrame, index=language_name, columns=meaning, values=form_asjp
                 已預先計算好，這裡只 subset columns。
    """
    mat_sum = np.zeros((n, n), dtype=np.float32)
    mat_cnt = np.zeros((n, n), dtype=np.int32)

    # 對每個 meaning（去重後），取出有值的語言行
    unique_meanings, counts = np.unique(meanings_subset, return_counts=True)

    for meaning, cnt in zip(unique_meanings, counts):
        if meaning not in forms_pivot.columns:
            continue
        col = forms_pivot[meaning].dropna()
        # 只保留在 lang_idx 中的語言
        col = col[col.index.isin(lang_idx)]
        if len(col) < 2:
            continue
        lang_list = col.index.tolist()
        form_list = col.values.tolist()
        indices = [lang_idx[l] for l in lang_list]

        for ii in range(len(form_list)):
            for jj in range(ii + 1, len(form_list)):
                i, j = indices[ii], indices[jj]
                d = _lev(form_list[ii], form_list[jj])
                # 有放回抽樣：該 meaning 出現 cnt 次，等效加 cnt 次
                mat_sum[i, j] += d * cnt
                mat_sum[j, i] += d * cnt
                mat_cnt[i, j] += cnt
                mat_cnt[j, i] += cnt

    with np.errstate(invalid='ignore'):
        mat = np.where(mat_cnt > 0,
                       mat_sum.astype(np.float64) / mat_cnt,
                       np.nan)
    np.fill_diagonal(mat, 0.0)

    # 填補 NaN（用行均值）
    row_means = np.nanmean(mat, axis=1)
    for i in range(n):
        nan_mask = np.isnan(mat[i])
        if nan_mask.any():
            fill = row_means[i] if not np.isnan(row_means[i]) else 0.5
            mat[i, nan_mask] = fill
            mat[nan_mask, i] = fill
    return mat


def _nj_newick(mat: np.ndarray, langs: list) -> str:
    if SKBIO_OK:
        dm = DistanceMatrix(mat, ids=langs)
        tree = skbio_nj(dm)
        return str(tree)
    flat = squareform(np.clip(mat, 0, None), checks=False)
    Z = linkage(flat, method='average')
    return "UPGMA_FALLBACK"


# ---------------------------------------------------------------------------
# 主程式
# ---------------------------------------------------------------------------

def run_bootstrap(n_bootstrap: int = 200,
                  top_langs: int = 100,
                  random_seed: int = 42) -> dict:
    rng = np.random.default_rng(random_seed)
    data_dir = Path(__file__).parent.parent / "data" / "processed"
    results_dir = Path(__file__).parent.parent / "results"

    print("讀取詞表資料...", flush=True)
    df = pd.read_csv(data_dir / "clean_wordlist.csv", low_memory=False)

    # 選取前 top_langs 語言
    lang_counts = df.groupby('language_name').size().sort_values(ascending=False)
    langs = lang_counts.head(top_langs).index.tolist()
    lang_idx = {l: i for i, l in enumerate(langs)}
    n = len(langs)
    print(f"使用語言數: {n}", flush=True)

    # ── 向量化建索引：pivot_table 一次搞定 ──────────────────────────────────
    print("建立 lang×meaning pivot 表...", flush=True)
    sub = df[df['language_name'].isin(langs)].copy()
    # 優先 form_asjp，fallback to form
    sub['_form'] = sub['form_asjp'].where(
        sub['form_asjp'].notna() & (sub['form_asjp'].astype(str) != 'nan'),
        sub['form']
    )
    sub = sub[sub['_form'].notna() & (sub['_form'].astype(str) != 'nan')]
    # 每個 (language, meaning) 取第一個 form
    pivot = sub.groupby(['language_name', 'meaning'])['_form'].first().unstack(fill_value=np.nan)
    # 確保 row order = langs
    pivot = pivot.reindex(index=langs)

    all_meanings = pivot.columns.tolist()
    all_meanings_arr = np.array(all_meanings)
    print(f"語義數: {len(all_meanings)}", flush=True)

    # ── Bootstrap ────────────────────────────────────────────────────────────
    all_matrices = []
    print(f"\n執行 {n_bootstrap} 次 bootstrap...", flush=True)

    for b in range(n_bootstrap):
        # 有放回抽樣 meanings（bootstrap 精神：unique meanings + counts）
        sample_idx = rng.integers(0, len(all_meanings), size=len(all_meanings))
        sample_meanings = all_meanings_arr[sample_idx]

        mat = _build_distance_matrix_fast(pivot, sample_meanings, lang_idx, n)
        all_matrices.append(mat)

        if (b + 1) % 20 == 0:
            print(f"  {b+1}/{n_bootstrap} 完成", flush=True)

    # ── 統計量 ───────────────────────────────────────────────────────────────
    print("\n計算統計量...", flush=True)
    stacked = np.array(all_matrices)   # (n_bootstrap, n, n)
    mean_mat = np.nanmean(stacked, axis=0)
    std_mat  = np.nanstd(stacked,  axis=0)
    with np.errstate(invalid='ignore'):
        cv_mat = np.where(mean_mat > 0, std_mat / mean_mat, 0.0)

    # 輸出矩陣
    pd.DataFrame(mean_mat, index=langs, columns=langs).to_csv(
        results_dir / "bootstrap_distance_mean.csv")
    pd.DataFrame(std_mat,  index=langs, columns=langs).to_csv(
        results_dir / "bootstrap_distance_std.csv")
    pd.DataFrame(cv_mat,   index=langs, columns=langs).to_csv(
        results_dir / "bootstrap_distance_cv.csv")
    print("已儲存距離矩陣", flush=True)

    # 共識樹
    final_newick = _nj_newick(mean_mat, langs)
    (results_dir / "bootstrap_consensus_tree.nwk").write_text(final_newick)
    print("已儲存共識樹", flush=True)

    # 摘要
    upper_cv = cv_mat[np.triu_indices(n, k=1)]
    summary = {
        "n_bootstrap": n_bootstrap,
        "n_languages": n,
        "n_meanings": len(all_meanings),
        "stable_pairs_ratio":   float(np.mean(upper_cv < 0.1)),
        "unstable_pairs_ratio": float(np.mean(upper_cv > 0.5)),
        "mean_cv":   float(np.mean(upper_cv)),
        "median_cv": float(np.median(upper_cv)),
    }
    (results_dir / "bootstrap_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))

    _write_report(summary, results_dir)
    return summary


def _write_report(summary: dict, results_dir: Path):
    lines = [
        "# Bootstrap over Concepts 報告",
        "",
        f"- Bootstrap 次數: {summary['n_bootstrap']}",
        f"- 語言數: {summary['n_languages']}",
        f"- 語義數: {summary['n_meanings']}",
        "",
        "## 距離穩定性",
        "",
        "| 指標 | 值 |",
        "|------|-----|",
        f"| 穩定語言對比率 (CV < 0.1) | {summary['stable_pairs_ratio']:.3f} |",
        f"| 不穩定語言對比率 (CV > 0.5) | {summary['unstable_pairs_ratio']:.3f} |",
        f"| 平均 CV | {summary['mean_cv']:.4f} |",
        f"| 中位數 CV | {summary['median_cv']:.4f} |",
        "",
        "## 解讀",
        "",
        "CV（變異係數）越低，表示對 concept 抽樣越穩健。",
        "穩定對比率高（>80%）表示距離矩陣具 bootstrap 可信度。",
        "",
        "## 輸出檔案",
        "",
        "- `bootstrap_distance_mean.csv`：bootstrap 平均距離矩陣",
        "- `bootstrap_distance_std.csv`：標準差矩陣",
        "- `bootstrap_distance_cv.csv`：變異係數矩陣",
        "- `bootstrap_consensus_tree.nwk`：基於平均矩陣的 NJ 共識樹",
    ]
    path = results_dir / "bootstrap_report.md"
    path.write_text("\n".join(lines), encoding='utf-8')
    print(f"已儲存報告: {path}", flush=True)


if __name__ == "__main__":
    summary = run_bootstrap(n_bootstrap=200, top_langs=100, random_seed=42)
    print("\n=== Bootstrap 摘要 ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
