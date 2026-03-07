#!/usr/bin/env python3
"""RF Distance 評估 - 對照 Glottolog 語系結構評估 NJ 樹品質.

計算:
1. Robinson-Foulds (RF) 距離（對照 Glottolog 5.3 完整 Newick 樹）
2. Clade-level precision / recall（能否正確恢復 sub-family clades）
3. Cophenetic correlation（重建樹 vs 參考距離）
4. Normalised RF（RF / max_RF，越低越好）

用法:
    python3 scripts/evaluate_tree.py
"""

import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

import ete3

from scipy.cluster.hierarchy import linkage, fcluster, cophenet
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr


# ---------------------------------------------------------------------------
# Glottolog 樹載入與語言匹配
# ---------------------------------------------------------------------------

def load_glottolog_austronesian_tree(newick_path: Path) -> ete3.Tree:
    """從 Glottolog 5.3 Newick 檔載入 Austronesian 子樹。"""
    text = newick_path.read_text(encoding='utf-8')
    parts = text.split(';')
    for p in parts:
        if 'Austronesian [aust1307]' in p:
            return ete3.Tree(p.strip() + ';', format=1)
    raise ValueError("找不到 Austronesian 子樹 (Austronesian [aust1307])")


def build_glottocode_leaf_map(tree: ete3.Tree) -> dict:
    """建立 {glottocode: leaf_node} 映射。"""
    mapping = {}
    for leaf in tree.get_leaves():
        m = re.search(r'\[([a-z0-9]{4}\d{4})\]', leaf.name)
        if m:
            mapping[m.group(1)] = leaf
    return mapping


def match_languages_to_glottolog(
    langs: list,
    lang_df: pd.DataFrame,
    gc_map: dict,
) -> tuple[list, list]:
    """
    返回 (matched_langs, unmatched_langs)。
    matched_langs: 在 Glottolog 樹中找到葉節點的語言名稱清單。
    """
    matched, unmatched = [], []
    for lang in langs:
        if lang not in lang_df.index:
            unmatched.append(lang)
            continue
        val = lang_df.loc[lang, 'glottocode']
        gc = str(val.iloc[0]) if hasattr(val, 'iloc') else str(val)
        if gc in gc_map:
            matched.append(lang)
        else:
            unmatched.append(lang)
    return matched, unmatched


# ---------------------------------------------------------------------------
# Robinson-Foulds Distance
# ---------------------------------------------------------------------------

def compute_rf_distance(
    predicted_nwk: str,
    glotto_tree: ete3.Tree,
    langs: list,
    lang_df: pd.DataFrame,
    gc_map: dict,
    safe_to_orig: dict = None,
) -> dict:
    """
    計算預測樹與 Glottolog 參考樹的 Robinson-Foulds distance。

    Returns dict with:
        rf: 原始 RF 值
        max_rf: 最大可能 RF 值
        norm_rf: normalised RF (rf / max_rf)
        n_shared_leaves: 共享葉節點數
    """
    # 解析預測樹（sanitized names）
    pred_tree = ete3.Tree(predicted_nwk, format=1, quoted_node_names=True)

    # Build safe_name -> glottocode mapping
    # safe_to_orig: {safe_name: original_lang_name}
    lang_to_gc = {}
    for lang in langs:
        if lang in lang_df.index:
            val = lang_df.loc[lang, 'glottocode']
            gc_val = str(val.iloc[0]) if hasattr(val, 'iloc') else str(val)
            lang_to_gc[lang] = gc_val

    # safe_name -> glottocode (via original name)
    safe_to_gc = {}
    if safe_to_orig:
        for safe, orig in safe_to_orig.items():
            if orig in lang_to_gc:
                safe_to_gc[safe] = lang_to_gc[orig]
    else:
        safe_to_gc = lang_to_gc

    # 重新命名預測樹葉節點為 glottocode（讓兩棵樹可對照）
    for leaf in pred_tree.get_leaves():
        gc = safe_to_gc.get(leaf.name)
        if gc and gc in gc_map:
            leaf.name = gc

    # 修剪 Glottolog 樹到只保留共同葉節點
    shared_gcs = set(leaf.name for leaf in pred_tree.get_leaves()
                     if re.match(r'^[a-z]{4}\d{4}$', leaf.name))
    glotto_pruned = glotto_tree.copy()
    all_leaves_gc = {leaf.name: leaf
                     for leaf in glotto_pruned.get_leaves()
                     if re.search(r'\[([a-z0-9]{4}\d{4})\]', leaf.name)}

    # Rename Glottolog leaf nodes to glottocodes (only leaf nodes)
    leaf_gc_renamed = {}
    for leaf in glotto_pruned.get_leaves():
        m = re.search(r'\[([a-z0-9]{4}\d{4})\]', leaf.name)
        if m:
            gc = m.group(1)
            leaf.name = gc
            leaf_gc_renamed[gc] = leaf

    # Only keep shared leaves (pass node objects to avoid ambiguity)
    to_keep_nodes = [leaf_gc_renamed[gc] for gc in shared_gcs if gc in leaf_gc_renamed]
    if len(to_keep_nodes) < 4:
        return {"rf": None, "max_rf": None, "norm_rf": None,
                "n_shared_leaves": len(to_keep_nodes)}

    # Prune both trees using node objects
    glotto_pruned.prune(to_keep_nodes, preserve_branch_length=False)
    # For pred_tree, use node objects too
    pred_leaf_map = {leaf.name: leaf for leaf in pred_tree.get_leaves()
                     if re.match(r'^[a-z]{4}\d{4}$', leaf.name)}
    pred_to_keep = [pred_leaf_map[gc] for gc in shared_gcs if gc in pred_leaf_map]
    pred_tree.prune(pred_to_keep, preserve_branch_length=False)

    # Compute RF
    rf_result = pred_tree.robinson_foulds(glotto_pruned, unrooted_trees=True)
    rf = rf_result[0]
    max_rf = rf_result[1]
    norm_rf = rf / max_rf if max_rf > 0 else 0.0

    return {
        "rf": int(rf),
        "max_rf": int(max_rf),
        "norm_rf": float(norm_rf),
        "n_shared_leaves": len(to_keep_nodes),
    }


# ---------------------------------------------------------------------------
# Sub-family 分組（from Glottolog 樹）
# ---------------------------------------------------------------------------

def get_subfamilies_from_glottolog(
    glotto_tree: ete3.Tree,
    langs: list,
    lang_df: pd.DataFrame,
    gc_map: dict,
    depth: int = 3,
) -> dict:
    """
    從 Glottolog 樹萃取每個語言的次語系標籤（節點深度 3）。
    返回 {lang_name: subfamily_label}。
    """
    groups = {}
    for lang in langs:
        if lang not in lang_df.index:
            groups[lang] = 'unknown'
            continue
        val = lang_df.loc[lang, 'glottocode']
        gc = str(val.iloc[0]) if hasattr(val, 'iloc') else str(val)
        if gc not in gc_map:
            groups[lang] = 'unknown_gc'
            continue
        leaf = gc_map[gc]
        # 往上爬 depth 層，取祖先節點名稱作為標籤
        node = leaf
        for _ in range(depth):
            if node.up:
                node = node.up
        # 萃取節點名稱中的 glottocode 或文字標籤
        m = re.search(r'\[([a-z0-9]{4}\d{4})\]', node.name)
        if m:
            groups[lang] = m.group(1)
        else:
            # 用節點文字（去掉特殊字元）
            groups[lang] = re.sub(r'\s+', '_', node.name.strip())[:20]
    return groups


# ---------------------------------------------------------------------------
# Clade Precision / Recall
# ---------------------------------------------------------------------------

def _flat_clustering(mat: np.ndarray, langs: list, k: int) -> dict:
    """UPGMA 聚類到 k 個群，返回 {lang: cluster_id}."""
    flat = squareform(mat, checks=False)
    flat = np.clip(flat, 0, None)
    Z = linkage(flat, method='average')
    labels = fcluster(Z, t=k, criterion='maxclust')
    return {lang: int(labels[i]) for i, lang in enumerate(langs)}


def compute_clade_metrics(predicted_groups: dict, reference_groups: dict) -> dict:
    """計算 clade-level 精確度/召回率。"""
    langs = list(predicted_groups.keys())
    ref_labels = [reference_groups.get(l, 'unknown') for l in langs]
    pred_labels = [predicted_groups.get(l, -1) for l in langs]

    unique_ref = sorted(set(ref_labels))

    # Clade purity
    ref_purity_scores = []
    for rg in unique_ref:
        if rg == 'unknown':
            continue
        ref_members = [l for l, r in zip(langs, ref_labels) if r == rg]
        if len(ref_members) < 2:
            continue
        pred_of_members = [predicted_groups.get(l, -1) for l in ref_members]
        most_common_pred = max(set(pred_of_members), key=pred_of_members.count)
        purity = pred_of_members.count(most_common_pred) / len(pred_of_members)
        ref_purity_scores.append(purity)

    mean_purity = float(np.mean(ref_purity_scores)) if ref_purity_scores else 0.0

    # Pair-based precision / recall
    n = len(langs)
    tp = fp = fn = 0
    for i in range(n):
        for j in range(i + 1, n):
            same_ref = (ref_labels[i] == ref_labels[j]) and (ref_labels[i] != 'unknown')
            same_pred = (pred_labels[i] == pred_labels[j])
            if same_ref and same_pred:
                tp += 1
            elif (not same_ref) and same_pred:
                fp += 1
            elif same_ref and (not same_pred):
                fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "pair_precision": precision,
        "pair_recall": recall,
        "f1": f1,
        "mean_clade_purity": mean_purity,
        "n_reference_groups": len([g for g in unique_ref if g not in ('unknown', 'unknown_gc')]),
        "n_predicted_clusters": len(set(pred_labels)),
    }


# ---------------------------------------------------------------------------
# Cophenetic Correlation
# ---------------------------------------------------------------------------

def cophenetic_correlation(mat: np.ndarray) -> float:
    """計算 UPGMA cophenetic 相關（樹結構 vs 原始距離的 Pearson r）。"""
    flat = squareform(mat, checks=False)
    flat = np.clip(flat, 0, None)
    Z = linkage(flat, method='average')
    c, _ = cophenet(Z, flat)
    return float(c)


# ---------------------------------------------------------------------------
# NJ 樹建立（用於 RF 計算）
# ---------------------------------------------------------------------------

def sanitize_name(name: str) -> str:
    """Replace characters unsafe in Newick quoted names."""
    return name.replace("'", "_").replace('"', '_')


def build_nj_newick(mat: np.ndarray, langs: list) -> tuple[str, dict]:
    """用 scipy UPGMA 建樹，返回 (newick_str, safe_to_orig_map)。"""
    safe_names = [sanitize_name(l) for l in langs]
    name_map = {safe: orig for safe, orig in zip(safe_names, langs)}

    from scipy.cluster.hierarchy import to_tree
    flat = squareform(mat, checks=False)
    flat = np.clip(flat, 0, None)
    Z = linkage(flat, method='average')

    def to_newick_node(node, names):
        if node.is_leaf():
            return f"'{names[node.id]}'"
        left = to_newick_node(node.left, names)
        right = to_newick_node(node.right, names)
        return f"({left},{right})"

    root = to_tree(Z)
    nwk = to_newick_node(root, safe_names) + ";"
    return nwk, name_map


# ---------------------------------------------------------------------------
# 主程式
# ---------------------------------------------------------------------------

def run_evaluation():
    results_dir = Path(__file__).parent.parent / "results"
    data_dir = Path(__file__).parent.parent / "data" / "processed"
    ext_dir = Path(__file__).parent.parent / "data" / "external"
    langs_file = data_dir / "languages.csv"
    glottolog_nwk = ext_dir / "tree_glottolog_newick.txt"

    print("讀取距離矩陣...")
    lev_df = pd.read_csv(results_dir / "distance_matrix_levenshtein.csv", index_col=0)
    langs = lev_df.index.tolist()
    print(f"語言數: {len(langs)}")

    matrices = {
        "levenshtein": lev_df.values,
        "sound_class": pd.read_csv(
            results_dir / "distance_matrix_sound_class.csv", index_col=0
        ).reindex(index=langs, columns=langs).values,
        "weighted": pd.read_csv(
            results_dir / "distance_matrix_weighted.csv", index_col=0
        ).reindex(index=langs, columns=langs).values,
    }

    # 修正 NaN
    for key in matrices:
        mat = matrices[key].copy()
        for i in range(mat.shape[0]):
            row_mean = np.nanmean(mat[i])
            mat[i] = np.where(
                np.isnan(mat[i]),
                row_mean if not np.isnan(row_mean) else 0.5,
                mat[i],
            )
        np.fill_diagonal(mat, 0.0)
        matrices[key] = mat

    print("\n載入 Glottolog 5.3 Austronesian 樹...")
    glotto_tree = load_glottolog_austronesian_tree(glottolog_nwk)
    gc_map = build_glottocode_leaf_map(glotto_tree)
    print(f"Glottolog Austronesian 葉節點: {len(gc_map)}")

    lang_df = pd.read_csv(langs_file).drop_duplicates(subset='name').set_index('name')
    matched, unmatched = match_languages_to_glottolog(langs, lang_df, gc_map)
    print(f"樣本語言匹配到 Glottolog: {len(matched)}/{len(langs)}")
    if unmatched:
        print(f"  未匹配: {unmatched}")

    # 次語系分組（depth=3）
    subfamilies = get_subfamilies_from_glottolog(glotto_tree, langs, lang_df, gc_map, depth=3)
    n_subfam = len(set(v for v in subfamilies.values() if v not in ('unknown', 'unknown_gc')))
    print(f"Glottolog 次語系組數 (depth=3): {n_subfam}")

    results = {}
    for method, mat in matrices.items():
        print(f"\n評估方法: {method}")

        # Cophenetic correlation
        cc = cophenetic_correlation(mat)
        print(f"  Cophenetic correlation: {cc:.4f}")

        # Clade precision/recall（k = 次語系組數）
        k = max(2, n_subfam)
        predicted_groups = _flat_clustering(mat, langs, k)
        clade_metrics = compute_clade_metrics(predicted_groups, subfamilies)
        print(f"  Pair precision: {clade_metrics['pair_precision']:.4f}")
        print(f"  Pair recall:    {clade_metrics['pair_recall']:.4f}")
        print(f"  F1:             {clade_metrics['f1']:.4f}")
        print(f"  Clade purity:   {clade_metrics['mean_clade_purity']:.4f}")

        print(f"  計算 Robinson-Foulds distance...")
        nwk, safe_map = build_nj_newick(mat, langs)
        rf_result = compute_rf_distance(nwk, glotto_tree, langs, lang_df, gc_map,
                                        safe_to_orig=safe_map)
        print(f"  RF={rf_result['rf']}, MaxRF={rf_result['max_rf']}, "
              f"Norm RF={rf_result['norm_rf']:.4f}, "
              f"Shared leaves={rf_result['n_shared_leaves']}")

        results[method] = {
            "cophenetic_correlation": cc,
            "rf_distance": rf_result["rf"],
            "max_rf": rf_result["max_rf"],
            "norm_rf": rf_result["norm_rf"],
            "n_shared_leaves": rf_result["n_shared_leaves"],
            **clade_metrics,
        }

    # 儲存結果
    json_path = results_dir / "tree_evaluation_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n已儲存: {json_path}")

    _write_report(results, results_dir)
    return results


def _write_report(results: dict, results_dir: Path):
    lines = [
        "# 樹評估報告（Glottolog 5.3 對照）",
        "",
        "使用 Glottolog 5.3 完整 Newick 樹評估 NJ 樹品質。",
        "RF distance 為對照 Glottolog Austronesian 子樹的 Robinson-Foulds 距離（越低越好）。",
        "",
        "| 方法 | Cophenetic r | Norm RF | Pair Precision | Pair Recall | F1 | Clade Purity |",
        "|------|-------------|---------|----------------|-------------|-----|--------------|",
    ]
    for method, res in results.items():
        norm_rf_str = f"{res['norm_rf']:.4f}" if res['norm_rf'] is not None else "N/A"
        lines.append(
            f"| {method} "
            f"| {res['cophenetic_correlation']:.4f} "
            f"| {norm_rf_str} "
            f"| {res['pair_precision']:.4f} "
            f"| {res['pair_recall']:.4f} "
            f"| {res['f1']:.4f} "
            f"| {res['mean_clade_purity']:.4f} |"
        )
    lines += [
        "",
        "## 說明",
        "",
        "- **Cophenetic r**: 樹的距離保真度（越高越好）",
        "- **Norm RF**: Normalised Robinson-Foulds distance，對照 Glottolog 5.3（越低越好）",
        "- **Pair Precision**: 在同一預測 cluster 的語言對中，真正同語系的比例",
        "- **Pair Recall**: 同語系語言對中，被成功分到同一 cluster 的比例",
        "- **Clade Purity**: 每個 Glottolog 組中，最多成員落在同一 predicted cluster 的比率",
        "",
        "## 外部效度說明",
        "",
        "Robinson-Foulds distance 直接對照 Glottolog 5.3 Austronesian 子樹，",
        "為目前南島語系語言分類的黃金標準。",
        "Normalised RF < 0.5 表示樹結構與 Glottolog 有相當程度的一致性。",
    ]
    report_path = results_dir / "tree_evaluation_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"已儲存報告: {report_path}")


if __name__ == "__main__":
    run_evaluation()
