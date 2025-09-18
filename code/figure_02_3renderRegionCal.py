#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
读取 CSV，按要求统计并打印：
1) 读取 /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/dataFrameForBrainRender_addNoise.csv；
2) group 为切片编号，region 为区域编号；
3) 统计所有切片下，不同区域的 density、diffuseFluo、energy、intensity 的均值；
4) 将均值做颜色映射（科研级配色，线性归一化，值越大颜色越强），并打印每个区域对应的值与颜色；
5) 逐个切片打印该指标下各区域的均值与颜色；
6) 将"所有切片聚合(各区域均值)"和"热力图数据"的数值与颜色映射导出为单个 CSV 到 analysisData 目录：figure_02_spinal_all_slices.csv。
"""

import os
import sys
import argparse
from typing import Dict, List, Tuple

import pandas as pd

try:
	import matplotlib
	import matplotlib.cm as cm
	import matplotlib.colors as mcolors
	import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
	print("[警告] 未找到 matplotlib，将跳过颜色映射，仅打印数值。", file=sys.stderr)
	matplotlib = None
	cm = None
	mcolors = None
	plt = None


# 全局变量已移至参数解析器中




def load_dataframe(csv_path: str, required_columns: list, metrics: list) -> pd.DataFrame:
	if not os.path.exists(csv_path):
		print(f"[错误] 文件不存在: {csv_path}", file=sys.stderr)
		sys.exit(1)
	df = pd.read_csv(csv_path)

	missing = [c for c in required_columns if c not in df.columns]
	if missing:
		print(f"[错误] CSV 缺少必要列: {missing}", file=sys.stderr)
		sys.exit(1)

	# 规范数据类型
	df["group"] = pd.to_numeric(df["group"], errors="coerce")
	df["region"] = pd.to_numeric(df["region"], errors="coerce")
	for m in metrics:
		df[m] = pd.to_numeric(df[m], errors="coerce")

	# 丢弃关键字段缺失的行
	df = df.dropna(subset=["group", "region"] + metrics)
	df = df.astype({"group": int, "region": int})
	return df


def _get_metric_cmap(metric: str, colormap_style: str = "scientific", print_friendly: bool = False):
	"""
	根据指标返回适合科研发表的科学配色方案
	使用经过科学验证的配色方案，确保色盲友好和打印友好
	"""
	if not matplotlib:
		return None
	m = metric.lower()
	
	# 如果选择打印友好模式，使用灰度配色
	if print_friendly:
		return mcolors.LinearSegmentedColormap.from_list(
			"grayscale_scientific",
			["#ffffff", "#f0f0f0", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525", "#000000"],
			N=256
		)
	
	# 根据配色风格选择不同的配色方案
	if colormap_style == "diverging":
		# 发散型配色，适合有正负值的数据
		return mcolors.LinearSegmentedColormap.from_list(
			"diverging_red_blue",
			["#67001f", "#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7", 
			 "#d1e5f0", "#92c5de", "#4393c3", "#2166ac", "#053061"],
			N=256
		)
	elif colormap_style == "grayscale":
		# 灰度配色
		return mcolors.LinearSegmentedColormap.from_list(
			"grayscale_scientific",
			["#ffffff", "#f0f0f0", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525", "#000000"],
			N=256
		)
	elif colormap_style == "viridis":
		# 使用viridis，科学界广泛接受
		return cm.get_cmap("viridis")
	else:  # scientific (默认)
		# 科研级别的配色方案 - 基于ColorBrewer和科学期刊标准
		if m == "energy":
			# 使用从白色到深红色的渐变，适合表示能量/强度
			# 基于ColorBrewer的Reds配色方案
			return mcolors.LinearSegmentedColormap.from_list(
				"scientific_red", 
				["#ffffff", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"], 
				N=256
			)
		elif m == "diffusefluo":
			# 使用从白色到深蓝色的渐变，适合表示弥散荧光
			# 基于ColorBrewer的Blues配色方案
			return mcolors.LinearSegmentedColormap.from_list(
				"scientific_blue", 
				["#ffffff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"], 
				N=256
			)
		elif m == "density":
			# 使用从白色到深绿色的渐变，适合表示密度
			# 基于ColorBrewer的Greens配色方案
			return mcolors.LinearSegmentedColormap.from_list(
				"scientific_green", 
				["#ffffff", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#006d2c", "#00441b"], 
				N=256
			)
		elif m == "intensity":
			# 使用从白色到深紫色的渐变，适合表示强度
			# 基于ColorBrewer的Purples配色方案
			return mcolors.LinearSegmentedColormap.from_list(
				"scientific_purple", 
				["#ffffff", "#f2f0f7", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#54278f", "#3f007d"], 
				N=256
			)
		else:
			# 默认使用viridis，这是科学界广泛接受的配色，色盲友好
			return cm.get_cmap("viridis")


def _value_to_unit_interval(v: float) -> float:
	if v is None:
		return 0.0
	if v < 0.0:
		return 0.0
	if v > 1.0:
		return 1.0
	return float(v)


def values_to_color(values: Dict[int, float], metric: str, normalize: bool, colormap_style: str = "scientific", print_friendly: bool = False) -> tuple:
	"""将数值映射为颜色 hex。
	normalize=True: 按数据的 min-max 线性归一到 [0,1]
	normalize=False: 假定输入已经在 [0,1]，仅裁剪到该区间

	返回: (acronym->hex颜色, (vmin, vmax))
	"""
	if not matplotlib or not values:
		return {}, (0.0, 1.0)

	v_list = list(values.values())
	data_vmin = min(v_list)
	data_vmax = max(v_list)

	if normalize:
		if data_vmax == data_vmin:
			normed_vals = {k: 0.5 for k in values.keys()}
			vmin, vmax = data_vmin, data_vmax
		else:
			norm = mcolors.Normalize(vmin=data_vmin, vmax=data_vmax)
			normed_vals = {k: float(norm(v)) for k, v in values.items()}
			vmin, vmax = data_vmin, data_vmax
	else:
		# 不进行归一化，认为值已经在 [0,1]
		normed_vals = {k: _value_to_unit_interval(v) for k, v in values.items()}
		vmin, vmax = 0.0, 1.0

	cmap = _get_metric_cmap(metric, colormap_style, print_friendly)
	color_map = {}
	for k, nv in normed_vals.items():
		rgba = cmap(nv)
		hex_color = mcolors.to_hex(rgba)
		color_map[k] = hex_color
	return color_map, (vmin, vmax)


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


def format_region_dict(d: Dict[int, float]) -> str:
	# 为了和示例风格一致，按区域编号降序输出
	items = sorted(d.items(), key=lambda x: x[0], reverse=True)
	return "{" + ", ".join([f"{k}: {v}" for k, v in items]) + "}"


def format_color_dict(d: Dict[int, str]) -> str:
	items = sorted(d.items(), key=lambda x: x[0], reverse=True)
	return "{" + ", ".join([f"{k}: '{v}'" for k, v in items]) + "}"


def compute_region_means(df: pd.DataFrame, metric: str) -> Dict[int, float]:
	grp = df.groupby("region")[metric].mean()
	return {int(k): float(v) for k, v in grp.items()}


def compute_slice_region_means(df: pd.DataFrame, metric: str) -> Dict[int, Dict[int, float]]:
	result: Dict[int, Dict[int, float]] = {}
	for group, sub in df.groupby("group"):
		grp = sub.groupby("region")[metric].mean()
		result[int(group)] = {int(k): float(v) for k, v in grp.items()}
	return result


def build_overall_rows(metric: str, region_means: Dict[int, float], color_map: Dict[int, str]) -> List[Dict[str, object]]:
	rows: List[Dict[str, object]] = []
	for region, val in sorted(region_means.items()):
		rows.append({
			"metric": metric,
			"scope": "all_slices",
			"region": region,
			"value": val,
			"color": color_map.get(region, "")
		})
	return rows


def build_heatmap_rows(df: pd.DataFrame, metric: str, colormap_style: str = "scientific", print_friendly: bool = False) -> List[Dict[str, object]]:
	"""
	为热力图生成颜色数据行
	计算每个切片-区域的均值并生成对应的颜色映射
	"""
	rows: List[Dict[str, object]] = []
	
	# 计算每个切片-区域的均值
	grp = df.groupby(["group", "region"])[metric].mean().reset_index()
	
	# 获取所有唯一的值用于颜色映射
	all_values = grp[metric].values
	if len(all_values) == 0:
		return rows
	
	# 计算归一化值
	data_vmin = all_values.min()
	data_vmax = all_values.max()
	
	if data_vmax == data_vmin:
		normed_vals = {i: 0.5 for i in range(len(all_values))}
		vmin, vmax = data_vmin, data_vmax
	else:
		norm = mcolors.Normalize(vmin=data_vmin, vmax=data_vmax)
		normed_vals = {i: float(norm(v)) for i, v in enumerate(all_values)}
		vmin, vmax = data_vmin, data_vmax
	
	# 获取颜色映射
	cmap = _get_metric_cmap(metric, colormap_style, print_friendly)
	
	# 为每个切片-区域组合生成颜色数据
	for idx, row in grp.iterrows():
		group = int(row["group"])
		region = int(row["region"])
		value = float(row[metric])
		normed_val = normed_vals[idx]
		
		# 计算颜色
		rgba = cmap(normed_val)
		hex_color = mcolors.to_hex(rgba)
		
		rows.append({
			"metric": metric,
			"scope": "heatmap",
			"group": group,
			"region": region,
			"value": value,
			"normalized_value": normed_val,
			"color": hex_color,
			"vmin": vmin,
			"vmax": vmax
		})
	
	return rows


def print_metric_report(df: pd.DataFrame, metric: str, normalize: bool, save_colorbar: bool, output_dir: str, colormap_style: str = "scientific", print_friendly: bool = False) -> List[Dict[str, object]]:
	print(f"{metric}指标...")

	acc_rows: List[Dict[str, object]] = []

	# 所有切片 - 区域均值
	region_means_all = compute_region_means(df, metric)
	if region_means_all:
		vmin = min(region_means_all.values())
		vmax = max(region_means_all.values())
		print(f"所有切片，指标: {metric}")
		print(f"数值范围: {vmin:.3f} - {vmax:.3f}")
		print(f"区域数据: {format_region_dict(region_means_all)}")
		colors_all, used_range = values_to_color(region_means_all, metric, normalize, colormap_style, print_friendly)
		if colors_all:
			print(f"颜色映射: {format_color_dict(colors_all)}")
		# 生成色条PNG（科研级别）
		metric_lower = metric.lower()
		if matplotlib and save_colorbar:
			cmap = _get_metric_cmap(metric, colormap_style, print_friendly)
			# 归一化时，色条应固定显示 0-1；非归一化时，使用 used_range（0-1）
			vmin_bar, vmax_bar = (0.0, 1.0) if normalize else (used_range[0], used_range[1])
			out_png = os.path.join(output_dir, f"colorbar_{metric_lower}.png")
			save_colorbar_png(cmap, vmin_bar, vmax_bar, out_png, f"{metric.capitalize()} Color Scale")
			print(f"[已导出] 科研级色条: {out_png}")
		# 累积 overall 行
		acc_rows.extend(build_overall_rows(metric, region_means_all, colors_all))
	else:
		print("[信息] 所有切片下无可用数据。")

	# 分切片 - 区域均值（仅打印，不导出）
	slice_region_means = compute_slice_region_means(df, metric)
	for group in sorted(slice_region_means.keys()):
		region_dict = slice_region_means[group]
		if not region_dict:
			continue
		print(f"切片 {group}，指标: {metric}")
		print(f"区域数据: {format_region_dict(region_dict)}")
		colors_slice, _ = values_to_color(region_dict, metric, normalize, colormap_style, print_friendly)
		if colors_slice:
			print(f"颜色映射: {format_color_dict(colors_slice)}")

	return acc_rows


def get_alternative_scientific_colormaps():
	"""
	提供额外的科研级别配色方案选项
	返回一个字典，包含不同用途的配色方案
	"""
	colormaps = {
		# 发散型配色（适合有正负值的数据）
		'diverging_red_blue': mcolors.LinearSegmentedColormap.from_list(
			"diverging_red_blue",
			["#67001f", "#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7", 
			 "#d1e5f0", "#92c5de", "#4393c3", "#2166ac", "#053061"],
			N=256
		),
		
		# 发散型配色（红-白-蓝）
		'diverging_red_white_blue': mcolors.LinearSegmentedColormap.from_list(
			"diverging_red_white_blue",
			["#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#ffffff", 
			 "#d1e5f0", "#92c5de", "#4393c3", "#2166ac"],
			N=256
		),
		
		# 热力图专用配色
		'heatmap_scientific': mcolors.LinearSegmentedColormap.from_list(
			"heatmap_scientific",
			["#000080", "#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff8000", "#ff0000"],
			N=256
		),
		
		# 灰度配色（适合打印）
		'grayscale_scientific': mcolors.LinearSegmentedColormap.from_list(
			"grayscale_scientific",
			["#ffffff", "#f0f0f0", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525", "#000000"],
			N=256
		)
	}
	return colormaps


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="统计各区域指标并生成颜色映射与色条。")
	
	# 文件路径参数
	parser.add_argument("--csv-path", 
	                   default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/dataFrameForBrainRender_addNoise.csv",
	                   help="输入CSV文件路径")
	parser.add_argument("--output-dir", 
	                   default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData",
	                   help="输出目录路径")
	
	# 数据处理参数
	norm_group = parser.add_mutually_exclusive_group()
	norm_group.add_argument("--normalize", dest="normalize", action="store_true", help="按 min-max 归一化到 [0,1] 进行着色 (默认)")
	norm_group.add_argument("--no-normalize", dest="normalize", action="store_false", help="不做归一化，假设输入已在 [0,1]")
	parser.set_defaults(normalize=True)
	parser.add_argument("--save-colorbar", action="store_true", help="为所有指标生成色条PNG (默认不生成)")
	
	# 科研配色选项
	parser.add_argument("--colormap-style", 
	                   choices=["scientific", "diverging", "grayscale", "viridis"], 
	                   default="scientific",
	                   help="选择配色风格: scientific(科研标准), diverging(发散型), grayscale(灰度), viridis(默认)")
	parser.add_argument("--high-dpi", action="store_true", help="使用高DPI (300) 生成图片")
	parser.add_argument("--print-friendly", action="store_true", help="使用打印友好的配色方案")
	parser.add_argument("--all-metrics-colorbar", action="store_true", help="为所有指标生成色条，不仅仅是energy和diffusefluo")
	
	# 数据列配置
	parser.add_argument("--required-columns", 
	                   nargs="+",
	                   default=["group", "region", "density", "diffuseFluo", "energy", "intensity"],
	                   help="必需的CSV列名")
	parser.add_argument("--metrics", 
	                   nargs="+",
	                   default=["density", "diffuseFluo", "energy", "intensity"],
	                   help="要处理的指标列表")
	
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	
	# 显示配色方案信息
	print(f"🎨 使用配色风格: {args.colormap_style}")
	if args.high_dpi:
		print("📐 使用高DPI (300) 生成图片")
	if args.print_friendly:
		print("🖨️ 使用打印友好配色方案")
	if args.save_colorbar:
		print("📊 将生成科研级色条图片")
	
	df = load_dataframe(args.csv_path, args.required_columns, args.metrics)

	# 仅保留必要列，避免其它杂项影响
	df = df[args.required_columns].copy()

	# 确保输出目录存在
	os.makedirs(args.output_dir, exist_ok=True)

	# 累积所有指标的数据行
	all_rows: List[Dict[str, object]] = []

	for metric in args.metrics:
		# 生成SVG颜色数据（all_slices）
		all_rows.extend(print_metric_report(df, metric, args.normalize, args.save_colorbar, args.output_dir, args.colormap_style, args.print_friendly))
		
		# 生成热力图颜色数据
		heatmap_rows = build_heatmap_rows(df, metric, args.colormap_style, args.print_friendly)
		all_rows.extend(heatmap_rows)
		print(f"已生成 {metric} 热力图颜色数据: {len(heatmap_rows)} 个数据点")

	# 写单个 CSV（包含SVG和热力图的所有颜色数据）
	out_path = os.path.join(args.output_dir, "figure_02_spinal_all_slices.csv")
	
	# 确定CSV列名
	columns = ["metric", "scope", "region", "value", "color"]
	
	# 检查是否有热力图数据，如果有则添加额外列
	has_heatmap_data = any(row.get("scope") == "heatmap" for row in all_rows)
	if has_heatmap_data:
		columns.extend(["group", "normalized_value", "vmin", "vmax"])
	
	pd.DataFrame(all_rows, columns=columns).to_csv(out_path, index=False)
	print(f"[已导出] 科研级数据文件: {out_path}")
	print(f"📊 总数据行数: {len(all_rows)}")
	print(f"🎨 配色风格: {args.colormap_style}")
	print("🎉 科研级颜色映射分析完成！")
	print("💡 提示: 使用 --colormap-style 参数可以尝试不同的配色风格")


if __name__ == "__main__":
	main()
