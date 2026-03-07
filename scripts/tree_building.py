#!/usr/bin/env python3
"""親緣樹生成腳本 - 使用 Neighbor Joining / UPGMA 從距離矩陣生成系統發育樹."""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.cluster.hierarchy import linkage, dendrogram, to_tree
from scipy.spatial.distance import squareform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# for Newick format
def get_newick(node, parent_dist, leaf_names):
    """將 scipy 聚類結果轉換為 Newick 格式."""
    if node.is_leaf():
        return f"{leaf_names[node.id]}:{parent_dist}"
    else:
        children = []
        for child in node.left, node.right:
            if child is not None:
                children.append(get_newick(child, node.dist / 2, leaf_names))
        return f"({','.join(children)}):{parent_dist}"


def compute_neighbor_joining(dist_matrix: pd.DataFrame) -> str:
    """使用 Neighbor Joining 算法生成親緣樹.
    
    參數:
        dist_matrix: 語言距離矩陣
        
    返回:
        Newick 格式的樹字串
    """
    # 轉換為濃縮距離矩陣（上三角）
    languages = dist_matrix.index.tolist()
    n = len(languages)
    
    # 處理 NaN 值：使用平均值填充
    dist_values = dist_matrix.values.copy()
    nan_mask = np.isnan(dist_values)
    
    # 對每個語言，用其他語言的平均距離填充 NaN
    for i in range(n):
        if nan_mask[i].any():
            valid_vals = dist_values[i, ~nan_mask[i]]
            if len(valid_vals) > 0:
                fill_val = np.mean(valid_vals)
                dist_values[i, nan_mask[i]] = fill_val
                dist_values[nan_mask[i], i] = fill_val
    
    # 確保對稱
    dist_values = (dist_values + dist_values.T) / 2
    np.fill_diagonal(dist_values, 0)
    
    # 濃縮為一維距離向量
    condensed = squareform(dist_values)
    
    # 使用 average linkage（類似 Neighbor Joining）
    Z = linkage(condensed, method='average')
    
    # 轉換為樹結構
    tree = to_tree(Z)
    
    # 生成 Newick 格式
    newick = get_newick(tree, tree.dist, languages)
    
    return newick


def compute_upgma(dist_matrix: pd.DataFrame) -> str:
    """使用 UPGMA 算法生成親緣樹."""
    languages = dist_matrix.index.tolist()
    n = len(languages)
    
    # 處理 NaN 值
    dist_values = dist_matrix.values.copy()
    nan_mask = np.isnan(dist_values)
    
    for i in range(n):
        if nan_mask[i].any():
            valid_vals = dist_values[i, ~nan_mask[i]]
            if len(valid_vals) > 0:
                fill_val = np.mean(valid_vals)
                dist_values[i, nan_mask[i]] = fill_val
                dist_values[nan_mask[i], i] = fill_val
    
    dist_values = (dist_values + dist_values.T) / 2
    np.fill_diagonal(dist_values, 0)
    
    # UPGMA (average linkage)
    condensed = squareform(dist_values)
    Z = linkage(condensed, method='average')
    
    tree = to_tree(Z)
    newick = get_newick(tree, tree.dist, languages)
    
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
    print("\n生成 Neighbor Joining 樹...")
    nj_newick = compute_neighbor_joining(dist_df)
    
    # 儲存 Newick 格式
    nj_file = results_dir / "austronesian_tree.nwk"
    with open(nj_file, 'w') as f:
        f.write(nj_newick + ";")
    print(f"已儲存: {nj_file}")
    
    # 生成 UPGMA 樹
    print("\n生成 UPGMA 樹...")
    upgma_newick = compute_upgma(dist_df)
    
    upgma_file = results_dir / "austronesian_tree_upgma.nwk"
    with open(upgma_file, 'w') as f:
        f.write(upgma_newick + ";")
    print(f"已儲存: {upgma_file}")
    
    print("\n完成！")


if __name__ == "__main__":
    main()
