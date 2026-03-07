#!/usr/bin/env python3
"""親緣樹生成腳本 - 使用真正的 Neighbor Joining (scikit-bio) 與 UPGMA 從距離矩陣生成系統發育樹.

注意：
- NJ (Neighbor Joining)：使用 scikit-bio 的 nj()，基於 Q-matrix 迭代找鄰接對
  (Saitou & Nei 1987)。與 average-linkage 不同，NJ 使用加性樹準則，不假設 ultrametric。
- UPGMA：使用 scipy average-linkage，假設 ultrametric（等速率演化），作為對照基線。
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import squareform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# scikit-bio for true Neighbor Joining
try:
    from skbio import DistanceMatrix
    from skbio.tree import nj as skbio_nj
    HAS_SKBIO = True
except ImportError:
    HAS_SKBIO = False
    print("警告：scikit-bio 未安裝，NJ 將退回 average-linkage 近似。"
          "安裝方式：pip install scikit-bio")

# for Newick format
def get_newick_scipy(node, parent_dist, leaf_names):
    """將 scipy 聚類結果轉換為 Newick 格式 (用於 UPGMA)."""
    if node.is_leaf():
        return f"{leaf_names[node.id]}:{parent_dist:.6f}"
    else:
        children = []
        for child in node.left, node.right:
            if child is not None:
                children.append(get_newick_scipy(child, node.dist / 2, leaf_names))
        return f"({','.join(children)}):{parent_dist:.6f}"


def _fill_nan(dist_values: np.ndarray) -> np.ndarray:
    """將 NaN 值用行平均填充，確保矩陣對稱且對角線為 0."""
    n = dist_values.shape[0]
    nan_mask = np.isnan(dist_values)
    for i in range(n):
        if nan_mask[i].any():
            valid_vals = dist_values[i, ~nan_mask[i]]
            fill_val = np.mean(valid_vals) if len(valid_vals) > 0 else 0.8
            dist_values[i, nan_mask[i]] = fill_val
            dist_values[nan_mask[i], i] = fill_val
    dist_values = (dist_values + dist_values.T) / 2
    np.fill_diagonal(dist_values, 0)
    return dist_values

def compute_neighbor_joining(dist_matrix: pd.DataFrame) -> str:
    """使用真正的 Neighbor Joining 算法生成親緣樹 (scikit-bio nj()).

    NJ 使用 Q-matrix 迭代尋找最近鄰接對，基於加性樹準則。
    不假設 ultrametric（等速率演化），適合含速率差異的語言演化。

    參數:
        dist_matrix: 語言距離矩陣 (DataFrame)

    返回:
        Newick 格式的樹字串
    """
    languages = dist_matrix.index.tolist()
    dist_values = _fill_nan(dist_matrix.values.copy())

    if HAS_SKBIO:
        dist_values = np.clip(dist_values, 0, None)
        dm = DistanceMatrix(dist_values, ids=languages)
        tree = skbio_nj(dm)
        newick = str(tree).strip()
        if not newick.endswith(";"):
            newick += ";"
        return newick
    else:
        print("警告：使用 average-linkage 作為 NJ 的近似替代（非精確 NJ）。")
        condensed = squareform(dist_values)
        Z = linkage(condensed, method='average')
        tree = to_tree(Z)
        newick = get_newick_scipy(tree, tree.dist, languages)
        return newick


def compute_upgma(dist_matrix: pd.DataFrame) -> str:
    """使用 UPGMA 算法生成親緣樹（假設 ultrametric，作為對照基線）.

    UPGMA = Unweighted Pair Group Method with Arithmetic Mean。
    假設所有譜系以相同速率演化（ultrametric 時計假設）。
    在語言中此假設通常不成立，故作為基線比較而非主要方法。
    """
    languages = dist_matrix.index.tolist()
    dist_values = _fill_nan(dist_matrix.values.copy())

    condensed = squareform(dist_values)
    Z = linkage(condensed, method='average')
    tree = to_tree(Z)
    newick = get_newick_scipy(tree, tree.dist, languages)
    return newick


def plot_tree(newick: str, output_path: Path, title: str = "Austronesian Language Phylogeny"):
    """繪製親緣樹."""
    # 讀取 Newick 並繪製
    from ete3 import Tree
    
    t = Tree(newick)
    
    # 繪製
    fig, ax = plt.subplots(figsize=(20, 30))
    t.render("%%d" % output_path, w=200, units="px", ax=ax)
    
    plt.title(title, fontsize=16)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def main():
    # 路徑
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = Path(__file__).parent.parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # 讀取距離矩陣
    print("讀取距離矩陣...")
    dist_df = pd.read_csv(results_dir / "language_distance_matrix.csv", index_col=0)
    print(f"語言數: {len(dist_df)}")
    
    # 生成 Neighbor Joining 樹
    print("\n生成 Neighbor Joining 樹（scikit-bio 真正 NJ）...")
    nj_newick = compute_neighbor_joining(dist_df)

    nj_file = results_dir / "austronesian_tree.nwk"
    with open(nj_file, 'w') as f:
        f.write(nj_newick if nj_newick.endswith(";") else nj_newick + ";")
    print(f"已儲存: {nj_file}")
    
    # 生成 UPGMA 樹
    print("\n生成 UPGMA 樹...")
    upgma_newick = compute_upgma(dist_df)
    
    upgma_file = results_dir / "austronesian_tree_upgma.nwk"
    with open(upgma_file, 'w') as f:
        f.write(upgma_newick + ";")
    print(f"已儲存: {upgma_file}")
    
    if HAS_SKBIO:
        print("\n✓ NJ 使用 scikit-bio（真正 Q-matrix Neighbor Joining）")
    else:
        print("\n⚠ NJ 使用 average-linkage 近似（請安裝 scikit-bio）")
    print("✓ UPGMA 使用 scipy average-linkage（ultrametric 基線）")
    print("\n完成！")


if __name__ == "__main__":
    main()
