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


# 全局变量已移至参数解析器中


def load_colors_by_metric(csv_path):
    """读取CSV，按metric聚合得到颜色映射。

    CSV列: metric,scope,region,value,color
    将每个metric下的记录按行序映射为区域索引(从1开始)到颜色字符串。
    """
    colors_by_metric = defaultdict(dict)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_by_metric = defaultdict(list)
        for row in reader:
            # 只处理SVG相关的数据（scope为all_slices）
            if row.get("scope") == "all_slices":
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


def load_heatmap_data(csv_path):
    """读取CSV，获取热力图数据。

    CSV列: metric,scope,group,region,value,color,normalized_value,vmin,vmax
    返回每个metric的热力图数据字典。
    """
    heatmap_data = defaultdict(dict)
    metric_info = {}
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 只处理热力图相关的数据（scope为heatmap）
            if row.get("scope") == "heatmap":
                metric = row["metric"]
                group = int(row["group"])
                region = int(row["region"])
                value = float(row["value"])
                color = row["color"]
                normalized_value = float(row["normalized_value"])
                vmin = float(row["vmin"])
                vmax = float(row["vmax"])
                
                # 存储热力图数据
                if metric not in heatmap_data:
                    heatmap_data[metric] = {}
                if group not in heatmap_data[metric]:
                    heatmap_data[metric][group] = {}
                
                heatmap_data[metric][group][region] = {
                    "value": value,
                    "color": color,
                    "normalized_value": normalized_value
                }
                
                # 存储metric的全局信息
                metric_info[metric] = {"vmin": vmin, "vmax": vmax}
    
    return heatmap_data, metric_info


# 注意：颜色计算逻辑已移至 figure_02_3renderRegionCal.py
# 此文件现在只负责读取CSV中的颜色数据并绘图


def save_colorbar_png(cmap, vmin: float, vmax: float, out_png: str, label: str) -> None:
    """
    生成科研级别的色条图片
    """
    if not matplotlib or not plt:
        return
    
    # 科研级别的色条设置
    fig, ax = plt.subplots(figsize=(6, 0.8), dpi=300)
    fig.subplots_adjust(bottom=0.3, top=0.7)
    
    # 创建颜色条
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cb = matplotlib.colorbar.ColorbarBase(
        ax, 
        cmap=cmap, 
        norm=norm, 
        orientation="horizontal",
        ticks=[vmin, (vmin + vmax) / 2, vmax]
    )
    
    # 设置标签和标题（科研风格）
    ax.set_title(label, fontsize=12, fontweight='bold', pad=15)
    cb.set_label(f'{label} Value', fontsize=11, fontweight='bold', labelpad=10)
    
    # 设置刻度标签
    cb.ax.tick_params(labelsize=10, width=1, length=4)
    cb.ax.set_xticklabels([f'{vmin:.2f}', f'{(vmin + vmax) / 2:.2f}', f'{vmax:.2f}'])
    
    # 设置边框
    for spine in ax.spines.values():
        spine.set_linewidth(1)
        spine.set_edgecolor('black')
    
    # 保存高分辨率图片
    fig.savefig(out_png, dpi=300, bbox_inches="tight", facecolor='white', edgecolor='none')
    plt.close(fig)


def generate_heatmap_for_metric(heatmap_data: dict, metric_info: dict, metric: str, output_dir: str) -> None:
    """
    使用CSV中的颜色数据生成热力图
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if metric not in heatmap_data:
        print(f"警告: 未找到 {metric} 的热力图数据")
        return
    
    # 获取该metric的热力图数据
    metric_data = heatmap_data[metric]
    metric_global_info = metric_info[metric]
    
    # 构建热力图矩阵
    groups = sorted(metric_data.keys())
    regions = set()
    for group_data in metric_data.values():
        regions.update(group_data.keys())
    regions = sorted(regions)
    
    # 创建矩阵
    matrix = []
    for group in groups:
        row = []
        for region in regions:
            if region in metric_data[group]:
                # 使用CSV中的归一化值
                row.append(metric_data[group][region]["normalized_value"])
            else:
                row.append(0.0)  # 缺失数据用0填充
        matrix.append(row)
    
    # 转换为numpy数组
    import numpy as np
    matrix = np.array(matrix)
    
    # 获取颜色范围
    vmin = metric_global_info["vmin"]
    vmax = metric_global_info["vmax"]
    
    # 科研级别的热图绘制
    plt.style.use('default')  # 使用默认样式确保一致性
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)  # 提高DPI和尺寸
    
    # 绘制热图（使用CSV中预计算的颜色）
    # 注意：这里我们使用imshow，但颜色已经在CSV中预计算了
    # 为了保持一致性，我们仍然使用colormap，但值应该与CSV中的归一化值一致
    im = ax.imshow(matrix, aspect="auto", vmin=0.0, vmax=1.0, origin="lower")
    
    # 设置标签和标题（科研风格）
    ax.set_xlabel("Spinal Cord Region", fontsize=12, fontweight='bold')
    ax.set_ylabel("Group (Slice)", fontsize=12, fontweight='bold')
    ax.set_title(f"{metric.capitalize()} Distribution Heatmap", fontsize=14, fontweight='bold', pad=20)
    
    # 设置刻度标签
    ax.set_xticks(range(len(regions)))
    ax.set_xticklabels([f"Region {r}" for r in regions], fontsize=10, rotation=45, ha='right')
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([f"Group {g}" for g in groups], fontsize=10)
    
    # 添加网格线（科研风格）
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 设置颜色条（科研风格）
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.8)
    cbar.set_label(f'{metric.capitalize()} Value', fontsize=11, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)
    
    # 调整布局
    fig.tight_layout()
    
    # 保存高分辨率图片
    out_png = os.path.join(output_dir, f"spinal_data_summary_{metric.lower()}.png")
    fig.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)

    # 生成科研级别的色条
    colorbar_png = os.path.join(output_dir, f"colorbar_{metric.lower()}.png")
    save_colorbar_png(im.get_cmap(), vmin, vmax, colorbar_png, f"{metric.capitalize()} Color Scale")


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
    parser = argparse.ArgumentParser(description="基于CSV颜色数据生成分区着色SVG与热力图")
    
    # 文件路径参数
    parser.add_argument("--csv-file", 
                       default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/figure_02_spinal_all_slices.csv",
                       help="颜色数据CSV文件路径")
    parser.add_argument("--svg-file", 
                       default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/originData/spinalCord_6regions.svg",
                       help="SVG模板文件路径")
    parser.add_argument("--output-dir", 
                       default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/output/regionPlot",
                       help="输出目录")
    
    # 处理选项
    parser.add_argument("--skip-svg", action="store_true", help="跳过SVG渲染步骤")
    parser.add_argument("--skip-heatmap", action="store_true", help="跳过热力图生成步骤")
    
    # 数据配置
    parser.add_argument("--metrics", 
                       nargs="+",
                       default=["density", "diffuseFluo", "energy", "intensity"],
                       help="要处理的指标列表")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("🎨 基于CSV颜色数据生成可视化图表")
    print(f"📁 颜色数据文件: {args.csv_file}")
    print(f"🖼️ SVG模板文件: {args.svg_file}")
    print(f"📂 输出目录: {args.output_dir}")

    # 1) 渲染SVG（基于已汇总的CSV颜色）
    if not args.skip_svg:
        if not os.path.exists(args.csv_file):
            print(f"❌ CSV文件不存在: {args.csv_file}")
        else:
            print("🔄 开始读取CSV并渲染每个metric的分区颜色...")
            colors_by_metric = load_colors_by_metric(args.csv_file)
            if not colors_by_metric:
                print("❌ CSV中没有可用的SVG颜色数据")
            else:
                render_metrics(args.svg_file, colors_by_metric, args.output_dir)
                print("✅ SVG渲染完成！")

    # 2) 生成四个指标的热力图与色条（基于CSV中的颜色数据）
    if not args.skip_heatmap:
        try:
            print("🔄 开始读取CSV中的热力图颜色数据...")
            heatmap_data, metric_info = load_heatmap_data(args.csv_file)
            if not heatmap_data:
                print("❌ CSV中没有可用的热力图颜色数据")
            else:
                for metric in args.metrics:
                    try:
                        generate_heatmap_for_metric(heatmap_data, metric_info, metric, args.output_dir)
                        print(f"✅ 已生成热力图与色条: {metric}")
                    except Exception as e:
                        print(f"❌ 生成 {metric} 热力图失败: {e}")
        except Exception as e:
            print(f"❌ 无法加载热力图颜色数据: {e}")
            return

    print("🎉 全部任务完成！")
    print(f"📊 生成的图片已保存到: {args.output_dir}")
    print("💡 提示: 颜色计算在 figure_02_3renderRegionCal.py 中完成")


if __name__ == "__main__":
    main()


