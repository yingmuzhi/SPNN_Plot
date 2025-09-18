#!/usr/bin/env python3
"""
根据CSV为每个metric渲染脊髓分区SVG着色图
要求：
1) 读取 /data/SegPNN_CR/_ymz/20250909_Figure02/code/figure_02_spinal_all_slices.csv
2) 针对每一个 metric 使用 figure_02_3renderSVG.SVGColorRenderer 进行渲染
3) 代码风格参考 demo_svg_colors.py
4) 基于 /data/SegPNN_CR/_ymz/20250909_Figure02/coordinate/spinalCord_6regions.svg 进行渲染
"""

import os
import sys
import csv
import argparse
from collections import defaultdict

# 确保可以导入同目录下的渲染类
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from figure_02_3renderSVG import SVGColorRenderer

try:
    import pandas as pd
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
except Exception as exc:  # pragma: no cover
    pd = None
    matplotlib = None
    plt = None
    mcolors = None


CSV_FILE = \
    "/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/figure_02_spinal_all_slices.csv"
SVG_FILE = \
    "/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/originData/spinalCord_6regions.svg"
OUTPUT_DIR = \
    "/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/output/regionPlot"
DATA_CSV = \
    "/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/dataFrameForBrainRender_addNoise.csv"
REQUIRED_COLUMNS = [
    "group",
    "region",
    "density",
    "diffuseFluo",
    "energy",
    "intensity",
]
METRICS = ["density", "diffuseFluo", "energy", "intensity"]


def load_colors_by_metric(csv_path):
    """读取CSV，按metric聚合得到颜色映射。

    CSV列: metric,scope,acronym,value,color
    将每个metric下的记录按行序映射为区域索引(从1开始)到颜色字符串。
    """
    colors_by_metric = defaultdict(dict)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_by_metric = defaultdict(list)
        for row in reader:
            rows_by_metric[row["metric"]].append(row)

    # 保持原顺序：写入的先后顺序即区域索引，从1开始
    for metric, rows in rows_by_metric.items():
        region_index = 1
        for row in rows:
            color = row.get("color", "").strip()
            if not color:
                continue
            colors_by_metric[metric][region_index] = color
            region_index += 1
    return colors_by_metric


def _get_metric_cmap(metric: str):
    if not matplotlib:
        return None
    m = str(metric).lower()
    if m == "energy":
        return mcolors.LinearSegmentedColormap.from_list("white_red", ["#ffffff", "#ff0000"], N=256)
    if m == "diffusefluo":
        return mcolors.LinearSegmentedColormap.from_list("white_blue", ["#ffffff", "#0000ff"], N=256)
    return plt.get_cmap("viridis")


def _clip01(x: float) -> float:
    if x is None:
        return 0.0
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _load_dataframe(csv_path: str) -> "pd.DataFrame":
    if pd is None:
        raise RuntimeError("pandas/matplotlib 不可用，无法生成热图")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"数据CSV不存在: {csv_path}")
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV 缺少必要列: {missing}")
    df["group"] = pd.to_numeric(df["group"], errors="coerce")
    df["region"] = pd.to_numeric(df["region"], errors="coerce")
    for m in METRICS:
        df[m] = pd.to_numeric(df[m], errors="coerce")
    df = df.dropna(subset=["group", "region"] + METRICS)
    df = df.astype({"group": int, "region": int})
    return df


def _normalize_series(s: "pd.Series") -> "pd.Series":
    vmin = s.min()
    vmax = s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin:
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - vmin) / (vmax - vmin)


def save_colorbar_png(cmap, vmin: float, vmax: float, out_png: str, label: str) -> None:
    if not matplotlib or not plt:
        return
    fig, ax = plt.subplots(figsize=(4, 0.4), dpi=200)
    fig.subplots_adjust(bottom=0.5)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cb = matplotlib.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation="horizontal")
    ax.set_title(label, fontsize=8)
    cb.set_label(label, fontsize=8)
    for tick in cb.ax.get_xticklabels():
        tick.set_fontsize(8)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def generate_heatmap_for_metric(df: "pd.DataFrame", metric: str, output_dir: str, normalize: bool) -> None:
    os.makedirs(output_dir, exist_ok=True)
    # 计算每个切片-区域的均值
    grp = df.groupby(["group", "region"])[metric].mean().reset_index()
    if normalize:
        grp[metric] = _normalize_series(grp[metric])
        vmin, vmax = 0.0, 1.0
    else:
        grp[metric] = grp[metric].apply(_clip01)
        vmin, vmax = 0.0, 1.0

    # 透视成热力图矩阵：行=group（升序），列=region（升序）
    pivot = grp.pivot(index="group", columns="region", values=metric).sort_index(axis=0).sort_index(axis=1)

    cmap = _get_metric_cmap(metric)

    # 绘制热图
    fig, ax = plt.subplots(figsize=(8, 6), dpi=200)
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax, origin="lower")
    ax.set_xlabel("region (region)")
    ax.set_ylabel("group (slice)")
    ax.set_title(f"{metric} summary heatmap")
    # 刻度为稀疏显示，避免过密
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(c) for c in pivot.columns], fontsize=6, rotation=90)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([str(i) for i in pivot.index], fontsize=6)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    out_png = os.path.join(output_dir, f"spinal_data_summary_{metric.lower()}.png")
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)

    # 同步保存色条（0-1）
    colorbar_png = os.path.join(output_dir, f"colorbar_{metric.lower()}.png")
    save_colorbar_png(cmap, 0.0, 1.0, colorbar_png, f"{metric} color scale")


def render_metrics(svg_path, colors_by_metric, output_dir):
    """对每个metric渲染一张SVG，并输出对应的区域信息文件。"""
    if not os.path.exists(svg_path):
        print(f"SVG文件不存在: {svg_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    renderer = SVGColorRenderer(svg_path)
    elements = renderer.extract_paths_and_polygons()
    if not elements:
        print("未找到任何图形元素")
        return

    for metric, region_colors in colors_by_metric.items():
        safe_metric = str(metric).replace("/", "_")
        output_svg = os.path.join(output_dir, f"colored_regions_{safe_metric}.svg")
        renderer.apply_colors_to_svg(elements, region_colors, output_svg)

        info_file = os.path.join(output_dir, f"region_info_{safe_metric}.txt")
        renderer.create_region_info(elements, region_colors, info_file)
        print(f"已生成 {metric}: {output_svg}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成分区着色SVG与四个指标的热力图和色条")
    norm_group = parser.add_mutually_exclusive_group()
    norm_group.add_argument("--normalize", dest="normalize", action="store_true", help="热力图以min-max归一化到[0,1]")
    norm_group.add_argument("--no-normalize", dest="normalize", action="store_false", help="热力图不归一化，假定数值已在[0,1]")
    parser.set_defaults(normalize=True)
    parser.add_argument("--skip-svg", action="store_true", help="跳过SVG渲染步骤")
    parser.add_argument("--skip-heatmap", action="store_true", help="跳过热力图生成步骤")
    return parser.parse_args()


def main():
    args = parse_args()

    # 1) 渲染SVG（基于已汇总的CSV颜色）
    if not args.skip_svg:
        if not os.path.exists(CSV_FILE):
            print(f"CSV文件不存在: {CSV_FILE}")
        else:
            print("开始读取CSV并渲染每个metric的分区颜色...")
            colors_by_metric = load_colors_by_metric(CSV_FILE)
            if not colors_by_metric:
                print("CSV中没有可用的颜色数据")
            else:
                render_metrics(SVG_FILE, colors_by_metric, OUTPUT_DIR)
                print("SVG渲染完成！")

    # 2) 生成四个指标的热力图与色条（基于原始数据CSV）
    if not args.skip_heatmap:
        try:
            df = _load_dataframe(DATA_CSV)
        except Exception as e:
            print(f"无法加载数据以生成热力图: {e}")
            return
        for metric in METRICS:
            try:
                generate_heatmap_for_metric(df, metric, OUTPUT_DIR, args.normalize)
                print(f"已生成热力图与色条: {metric}")
            except Exception as e:
                print(f"生成 {metric} 热力图失败: {e}")

    print("全部任务完成！")


if __name__ == "__main__":
    main()


