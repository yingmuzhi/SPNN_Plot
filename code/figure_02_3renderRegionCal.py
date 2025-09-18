#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
读取 CSV，按要求统计并打印：
1) 检查是否在 env_cp38_pnnWholeBrain2 环境中运行；
2) 读取 /data/SegPNN_CR/_ymz/20250909_Figure02/code/dataFrameForBrainRender_addNoise.csv；
3) mid 为切片编号，acronym 为区域编号；
4) 统计所有切片下，不同区域的 density、diffuseFluo、energy、intensity 的均值；
5) 将均值做颜色映射（viridis，线性归一化，值越大颜色越强），并打印每个区域对应的值与颜色；
6) 逐个切片打印该指标下各区域的均值与颜色；
7) 仅将“所有切片聚合(各区域均值)”的数值与颜色映射导出为单个 CSV 到 code 目录：figure_02_spinal_all_slices.csv。
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


CSV_PATH = \
	"/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/dataFrameForBrainRender_addNoise.csv"
OUTPUT_DIR = \
	"/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData"
REQUIRED_COLUMNS = [
	"group",            # 切片编号
	"region",        # 区域编号
	"density",
	"diffuseFluo",
	"energy",
	"intensity",
]
METRICS = ["density", "diffuseFluo", "energy", "intensity"]


def check_env(target_env_name: str = "env_cp38_pnnWholeBrain2") -> None:
	"""检查当前 Conda 环境名称，若不匹配则给出提示。"""
	conda_env = os.environ.get("CONDA_DEFAULT_ENV") or os.environ.get("VIRTUAL_ENV")
	if conda_env and os.path.basename(str(conda_env)) == target_env_name:
		return
	print(
		f"[提示] 建议在 Conda 环境 '{target_env_name}' 中运行此脚本。当前环境: "
		f"{os.environ.get('CONDA_DEFAULT_ENV') or '未知'}",
		file=sys.stderr,
	)


def load_dataframe(csv_path: str) -> pd.DataFrame:
	if not os.path.exists(csv_path):
		print(f"[错误] 文件不存在: {csv_path}", file=sys.stderr)
		sys.exit(1)
	df = pd.read_csv(csv_path)

	missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
	if missing:
		print(f"[错误] CSV 缺少必要列: {missing}", file=sys.stderr)
		sys.exit(1)

	# 规范数据类型
	df["group"] = pd.to_numeric(df["group"], errors="coerce")
	df["region"] = pd.to_numeric(df["region"], errors="coerce")
	for m in METRICS:
		df[m] = pd.to_numeric(df[m], errors="coerce")

	# 丢弃关键字段缺失的行
	df = df.dropna(subset=["group", "region"] + METRICS)
	df = df.astype({"group": int, "region": int})
	return df


def _get_metric_cmap(metric: str):
	"""根据指标返回相应的颜色映射。
	- energy: 白 -> 红
	- diffuseFluo: 白 -> 蓝
	- 其他: viridis
	"""
	if not matplotlib:
		return None
	m = metric.lower()
	if m == "energy":
		return mcolors.LinearSegmentedColormap.from_list("white_red", ["#ffffff", "#ff0000"], N=256)
	if m == "diffusefluo":
		return mcolors.LinearSegmentedColormap.from_list("white_blue", ["#ffffff", "#0000ff"], N=256)
	return cm.get_cmap("viridis")


def _value_to_unit_interval(v: float) -> float:
	if v is None:
		return 0.0
	if v < 0.0:
		return 0.0
	if v > 1.0:
		return 1.0
	return float(v)


def values_to_color(values: Dict[int, float], metric: str, normalize: bool) -> tuple:
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

	cmap = _get_metric_cmap(metric)
	color_map = {}
	for k, nv in normed_vals.items():
		rgba = cmap(nv)
		hex_color = mcolors.to_hex(rgba)
		color_map[k] = hex_color
	return color_map, (vmin, vmax)


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


def print_metric_report(df: pd.DataFrame, metric: str, normalize: bool, save_colorbar: bool) -> List[Dict[str, object]]:
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
		colors_all, used_range = values_to_color(region_means_all, metric, normalize)
		if colors_all:
			print(f"颜色映射: {format_color_dict(colors_all)}")
		# 若为 energy 或 diffuseFluo，则输出 colorbar png
		metric_lower = metric.lower()
		if metric_lower in ("energy", "diffusefluo") and matplotlib and save_colorbar:
			cmap = _get_metric_cmap(metric)
			# 归一化时，色条应固定显示 0-1；非归一化时，使用 used_range（0-1）
			vmin_bar, vmax_bar = (0.0, 1.0) if normalize else (used_range[0], used_range[1])
			out_png = os.path.join(OUTPUT_DIR, f"colorbar_{metric_lower}.png")
			save_colorbar_png(cmap, vmin_bar, vmax_bar, out_png, f"{metric} color scale")
			print(f"[已导出] {out_png}")
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
		colors_slice, _ = values_to_color(region_dict, metric, normalize)
		if colors_slice:
			print(f"颜色映射: {format_color_dict(colors_slice)}")

	return acc_rows


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="统计各区域指标并生成颜色映射与色条。")
	norm_group = parser.add_mutually_exclusive_group()
	norm_group.add_argument("--normalize", dest="normalize", action="store_true", help="按 min-max 归一化到 [0,1] 进行着色 (默认)")
	norm_group.add_argument("--no-normalize", dest="normalize", action="store_false", help="不做归一化，假设输入已在 [0,1]")
	parser.set_defaults(normalize=True)
	parser.add_argument("--save-colorbar", action="store_true", help="为 energy 和 diffuseFluo 生成色条PNG (默认不生成)")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	check_env("env_cp38_pnnWholeBrain2")
	df = load_dataframe(CSV_PATH)

	# 仅保留必要列，避免其它杂项影响
	df = df[REQUIRED_COLUMNS].copy()

	# 确保输出目录存在
	os.makedirs(OUTPUT_DIR, exist_ok=True)

	# 累积所有指标的 all_slices 行
	all_rows: List[Dict[str, object]] = []

	for metric in METRICS:
		all_rows.extend(print_metric_report(df, metric, args.normalize, args.save_colorbar))

	# 写单个 CSV
	out_path = os.path.join(OUTPUT_DIR, "figure_02_spinal_all_slices.csv")
	pd.DataFrame(all_rows, columns=["metric", "scope", "region", "value", "color"]).to_csv(out_path, index=False)
	print(f"[已导出] {out_path}")


if __name__ == "__main__":
	main()
