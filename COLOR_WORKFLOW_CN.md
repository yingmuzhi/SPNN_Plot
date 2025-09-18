# 颜色计算与可视化工作流程（中文）

## 📋 概述

经过重构后，颜色计算和可视化分为两个独立步骤：

1. `figure_02_3renderRegionCal.py` — 负责颜色计算与映射，输出含颜色的 CSV
2. `figure_02_3renderRegionPlot.py` — 只读取 CSV 的颜色并绘图（SVG 与热力图）

## 🔄 工作流程

### 步骤 1：颜色计算（`figure_02_3renderRegionCal.py`）

```bash
# 使用默认科研配色
python figure_02_3renderRegionCal.py

# 使用发散型配色
python figure_02_3renderRegionCal.py --colormap-style diverging

# 使用打印友好配色（灰度）
python figure_02_3renderRegionCal.py --print-friendly

# 生成色条图片（建议论文配图同时导出）
python figure_02_3renderRegionCal.py --save-colorbar
```

- 输出文件：`src/analysisData/figure_02_spinal_all_slices.csv`
- CSV 字段：
  - `metric`：指标（density, diffuseFluo, energy, intensity）
  - `scope`：数据范围（`all_slices` 用于 SVG、`heatmap` 用于热力图）
  - `region`：区域编号
  - `group`：切片编号（仅热力图）
  - `value`：原始数值
  - `color`：十六进制颜色值
  - `normalized_value`：归一化数值（仅热力图）
  - `vmin`, `vmax`：该指标数值范围（仅热力图）

### 步骤 2：可视化绘图（`figure_02_3renderRegionPlot.py`）

```bash
# 生成所有图表
python figure_02_3renderRegionPlot.py

# 只生成 SVG
python figure_02_3renderRegionPlot.py --skip-heatmap

# 只生成热力图
python figure_02_3renderRegionPlot.py --skip-svg

# 指定自定义路径
python figure_02_3renderRegionPlot.py \
  --csv-file /path/to/figure_02_spinal_all_slices.csv \
  --output-dir /path/to/output
```

## 📊 数据一致性

- SVG 渲染：使用 `scope = all_slices` 的颜色，区域均值→唯一颜色
- 热力图：使用 `scope = heatmap` 的颜色，切片×区域矩阵→每格颜色
- 颜色完全由 `figure_02_3renderRegionCal.py` 计算并固化到 CSV，绘图脚本不再重复计算

## 🎨 配色来源与规范

参考配色（色盲友好、科研常用）：

- ColorBrewer 顺序色带（Sequential）：
  - Reds（能量/强度）
  - Blues（弥散荧光）
  - Greens（密度）
  - Purples（强度）
- Viridis（感知均匀、色盲友好）
- 发散配色 Red–Blue（用于有正负方向或偏离基线的指标）
- Grayscale 灰度（打印友好）

实现要点：

- 所有颜色映射在 `figure_02_3renderRegionCal.py` 中一次性计算与固化；
- `figure_02_3renderRegionPlot.py` 仅读取 `color` 字段绘图，保证 SVG 与热力图一致；
- 常用参数：
  - `--colormap-style scientific|diverging|grayscale|viridis`
  - `--print-friendly` 强制灰度
  - `--save-colorbar` 导出色条

建议：

- 单调递增型指标（density/diffuseFluo/energy/intensity）：优先 ColorBrewer 顺序色带或 viridis；
- 有正负/相对变化指标：使用发散配色（红–蓝）；
- 期刊黑白打印：使用 `--print-friendly`；
- 论文图建议同时导出色条，确保可解释与可复现。

## ✅ 优势

1. 一致性：SVG 与热力图来源一致的颜色
2. 可维护：颜色逻辑集中、绘图逻辑简单
3. 灵活性：命令行切换风格与输出
4. 可重现：CSV 固化颜色，记录 `vmin/vmax`

## 🔧 故障排除

- 若 CSV 不存在：先运行 `figure_02_3renderRegionCal.py`
- 若颜色数据缺失：检查输入数据列是否齐全（`group, region, metrics`）
- 若热力图异常：确认 CSV 中存在 `scope = heatmap` 的行
