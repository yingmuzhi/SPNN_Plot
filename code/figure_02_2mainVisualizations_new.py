import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_1samp, wilcoxon
import os
import shutil
from matplotlib import cm
from matplotlib.ticker import FixedLocator
import argparse

# 简化的Atlas类，不依赖allensdk
class SimpleAtlas:
    def __init__(self):
        # 简单的区域ID到名称的映射
        self.region_names = {
            120: "Cervical spinal cord",
            121: "Thoracic spinal cord", 
            122: "Lumbar spinal cord",
            123: "Sacral spinal cord",
            124: "Coccygeal spinal cord",
            125: "Cervical enlargement",
            126: "Lumbar enlargement"
        }
    
    def ids_to_names(self, region_ids):
        """将区域ID转换为名称"""
        names = []
        for region_id in region_ids:
            if region_id in self.region_names:
                names.append(self.region_names[region_id])
            else:
                names.append(f"Area {region_id}")
        return names

# 创建简化的Atlas对象
A = SimpleAtlas()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Figure 02 visualizations with configurable parameters")
    parser.add_argument(
        "--input-csv",
        default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/dataFrameForBrainRender_addNoise.csv",
        help="Path to prepared CSV file (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/output",
        help="Directory to save outputs (default: %(default)s)",
    )
    parser.add_argument(
        "--clear-output",
        action="store_true",
        help="If set, remove existing output directory before saving results",
    )
    # Heatmap options per metric
    parser.add_argument("--cmap-diffuse", default="PuBu", help="Colormap for diffuseFluo heatmap (default: PuBu)")
    parser.add_argument("--cmap-energy", default="OrRd", help="Colormap for energy heatmap (default: OrRd)")
    parser.add_argument("--cmap-density", default="BuGn", help="Colormap for density heatmap (default: BuGn)")
    parser.add_argument("--cmap-intensity", default="Purples", help="Colormap for intensity heatmap (default: Purples)")

    parser.add_argument("--vmin-diffuse", type=float, default=0.0, help="vmin for diffuseFluo heatmap (default: 0)")
    parser.add_argument("--vmax-diffuse", type=float, default=2.0, help="vmax for diffuseFluo heatmap (default: 2)")
    parser.add_argument("--vmin-energy", type=float, default=0.0, help="vmin for energy heatmap (default: 0)")
    parser.add_argument("--vmax-energy", type=float, default=3.0, help="vmax for energy heatmap (default: 3)")
    parser.add_argument("--vmin-density", type=float, default=0.0, help="vmin for density heatmap (default: 0)")
    parser.add_argument("--vmax-density", type=float, default=140.0, help="vmax for density heatmap (default: 140)")
    parser.add_argument("--vmin-intensity", type=float, default=0.0, help="vmin for intensity heatmap (default: 0)")
    parser.add_argument("--vmax-intensity", type=float, default=1.0, help="vmax for intensity heatmap (default: 1)")

    parser.add_argument("--fig-w", type=float, default=5.0, help="Figure width for heatmaps (inches, default: 5)")
    parser.add_argument("--fig-h", type=float, default=8.0, help="Figure height for heatmaps (inches, default: 8)")
    parser.add_argument("--font-scaling", type=float, default=0.8, help="Font scaling factor for heatmaps (default: 0.8)")

    return parser.parse_args()


args = parse_args()

######### 1. Setup output directory
# --------------------------------------------------------------------
output_dir = args.output_dir
if os.path.exists(output_dir) and args.clear_output:
    print(f"Removing existing output directory: {output_dir}")
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)
print(f"Created output directory: {output_dir}")

######### 2. load data
# --------------------------------------------------------------------
# Use prepared data
prepared_csv = args.input_csv
if not os.path.exists(prepared_csv):
    raise FileNotFoundError(
        f"Prepared CSV not found: {prepared_csv}. Run figure_02_1prepareDataForBrainRender.py or 1x_addNoise.py first."
    )

raw = pd.read_csv(prepared_csv)

# Expect columns: ['group','density','diffuseFluo','energy','intensity','region']
required_cols = {"group","density","diffuseFluo","energy","intensity","region"}
missing = required_cols - set(raw.columns)
if missing:
    raise ValueError(f"Missing required columns in prepared CSV: {missing}")

print("原始数据预览:")
print(raw.head())
print(f"\n数据形状: {raw.shape}")
print(f"切片数量: {raw['group'].nunique()}")
print(f"区域数量: {raw['region'].nunique()}")
print(f"切片列表: {sorted(raw['group'].unique())}")
print(f"区域列表: {sorted(raw['region'].unique())}")

# 重新组织数据：切片为横坐标，区域为纵坐标
# 创建透视表，切片为列，区域为行
metrics = ['diffuseFluo', 'energy', 'density', 'intensity']
data_dict = {}

for metric in metrics:
    # 创建透视表：行为region（区域），列为group（切片），值为metric
    pivot_df = raw.pivot_table(
        index='region', 
        columns='group', 
        values=metric, 
        fill_value=0
    )
    data_dict[metric] = pivot_df
    print(f"\n{metric} 数据形状: {pivot_df.shape}")
    print(f"区域: {pivot_df.index.tolist()}")
    print(f"切片: {pivot_df.columns.tolist()}")


######### 2. 自定义热力图函数（仿造 gt.midOntologyHeatmap 美学）
def create_mid_ontology_heatmap(data, atlas, title=None, cmap='PuBu', vmin=None, vmax=None,
                                figsize=(5, 8), fontScaling=1.0):
    """
    使用 seaborn.clustermap 创建与 gt.midOntologyHeatmap 视觉风格相近的热力图：
    - 无聚类，仅作为矩阵展示
    - 美化的颜色条，固定位置和字号
    - 轴标签与标题字号比例与原函数一致
    """
    # 处理 NaN 的 colormap
    my_cmap = plt.get_cmap(cmap).copy()
    try:
        my_cmap.set_bad('lightgray')
    except Exception:
        pass

    # 自动 vmin/vmax（若未提供）
    data_values = data.values
    if vmin is None:
        vmin = np.nanpercentile(data_values, 5)
    if vmax is None:
        vmax = np.nanpercentile(data_values, 95)

    # 行标签：区域名称
    try:
        row_labels = atlas.ids_to_names(list(data.index))
    except Exception:
        row_labels = [str(i) for i in list(data.index)]

    # 构造一个带有名称索引的副本用于显示（clustermap 不直接接受自定义 yticklabels 列表）
    data_for_plot = data.copy()
    data_for_plot.index = row_labels

    # 使用 clustermap，关闭所有聚类与树状图，设置 colorbar 位置
    axObj = sns.clustermap(
        data_for_plot,
        figsize=figsize,
        cmap=my_cmap,
        vmin=vmin,
        vmax=vmax,
        mask=data_for_plot.isna(),
        row_cluster=False,
        col_cluster=False,
        yticklabels=True,
        xticklabels=True,
        dendrogram_ratio=0.01,
        colors_ratio=0.05,
        cbar_pos=(1, .3, .03, .3),
        cbar_kws={"ticks": [vmin, vmax]}
    )

    # 轴与标题美化
    axObj.ax_heatmap.set_xlabel('Mice', fontdict={'fontsize': int(28 * fontScaling)})
    axObj.ax_heatmap.set_ylabel('Spinal cord area', fontdict={'fontsize': int(28 * fontScaling)})
    # 标题在左侧；刻度标签在右侧
    try:
        axObj.ax_heatmap.yaxis.set_label_position('left')
        axObj.ax_heatmap.yaxis.set_ticks_position('right')
        axObj.ax_heatmap.yaxis.tick_right()
        # 同时在右侧显示 yticklabels
        axObj.ax_heatmap.set_yticklabels(axObj.ax_heatmap.get_yticklabels(), rotation=0)
        # 左侧标题适当左移
        axObj.ax_heatmap.yaxis.set_label_coords(-0.12, 0.5)
    except Exception:
        pass
    axObj.ax_cbar.tick_params(labelsize=int(20 * fontScaling))

    # X 轴刻度简化：旋转、较小字号
    axObj.ax_heatmap.set_xticklabels(axObj.ax_heatmap.get_xmajorticklabels(), rotation=45)
    axObj.ax_heatmap.tick_params(axis='x', labelsize=int(14 * fontScaling))
    axObj.ax_heatmap.tick_params(axis='y', labelsize=int(12 * fontScaling))

    if title:
        axObj.ax_heatmap.set_title(title, fontsize=int(28 * fontScaling))

    return axObj


######### 3. 仿造gt.coarseOntologyBarplot的柱状图函数
def create_coarse_ontology_barplot(data, atlas, title, cmap='PuBu', figsize=(4, 6), 
                                  fontScaling=1, xlabel=None, areaNames=True):
    """
    仿造gt.coarseOntologyBarplot函数创建柱状图
    创建带有均值和SEM以及单个数据点的柱状图
    """
    # Style. white background and no ticks
    sns.set_style('white')
    
    # Set up colors for the bars and single animals
    colormap = cm.get_cmap(cmap)
    barColor = colormap(0.4)
    animalColor = colormap(0.85)
    
    # Create the figure and axes objects
    f, ax = plt.subplots(figsize=figsize)
    
    # Background Bar Plot
    meltedData = data.melt(ignore_index=False, value_name='metricValue')
    
    # 获取区域名称
    area_names = []
    for region_id in meltedData.index.tolist():
        try:
            name = atlas.ids_to_names([region_id])[0]
            area_names.append(name)
        except:
            area_names.append(f"Area {region_id}")
    
    bp = sns.barplot(
        data=meltedData,
        ax=ax,
        y=area_names,
        x='metricValue',
        orient="h",
        alpha=1,
        linewidth=.5,
        edgecolor="black",
        color=barColor,
        errorbar='se'
    )
    
    # Plot single animals
    sns.stripplot(
        ax=ax,
        y=area_names,
        x='metricValue',
        data=meltedData,
        size=6,
        orient="h",
        jitter=True,
        alpha=.8,
        linewidth=0.6,
        edgecolor="black",
        color=animalColor,
    )
    
    # Customize Plot
    bp.xaxis.grid(True)
    maxValue = int(np.ceil(meltedData['metricValue'].max()))
    xticksLocations = [x for x in range(maxValue + 1)]
    ax.xaxis.set_major_locator(FixedLocator(xticksLocations))
    ax.xaxis.set_tick_params(labelsize=22*fontScaling)
    ax.yaxis.set_tick_params(labelsize=18*fontScaling)
    if title:
        ax.set_title(title, fontsize=25*fontScaling)
    if xlabel:
        ax.xaxis.set_label_text(xlabel, fontsize=20*fontScaling)
    if not areaNames:
        ax.yaxis.set_ticks([])
    sns.despine(bottom=True, left=False)
    
    return ax


######### 4. 生成热力图
print("\n" + "="*50)
print("生成热力图...")

# 4.1 WFA Diffuse Fluorescence 热力图
print("绘制 WFA Diffuse Fluorescence 热力图...")
ax1 = create_mid_ontology_heatmap(
    data_dict['diffuseFluo'], 
    A,
    title='WFA Diffuse Fluorescence',
    cmap=args.cmap_diffuse,
    vmin=args.vmin_diffuse,
    vmax=args.vmax_diffuse,
    figsize=(args.fig_w, args.fig_h),
    fontScaling=args.font_scaling
)
plt.savefig(f'{output_dir}/diffuseHeatmap_new.svg', bbox_inches='tight')
plt.show()

# 4.2 PNN Energy 热力图
print("绘制 PNN Energy 热力图...")
ax2 = create_mid_ontology_heatmap(
    data_dict['energy'], 
    A,
    title='PNN Energy',
    cmap=args.cmap_energy,
    vmin=args.vmin_energy,
    vmax=args.vmax_energy,
    figsize=(args.fig_w, args.fig_h),
    fontScaling=args.font_scaling
)
plt.savefig(f'{output_dir}/energyHeatmap_new.svg', bbox_inches='tight')
plt.show()

# 4.3 PNN Density 热力图
print("绘制 PNN Density 热力图...")
ax3 = create_mid_ontology_heatmap(
    data_dict['density'], 
    A,
    title='PNN Density',
    cmap=args.cmap_density,
    vmin=args.vmin_density,
    vmax=args.vmax_density,
    figsize=(args.fig_w, args.fig_h),
    fontScaling=args.font_scaling
)
plt.savefig(f'{output_dir}/densityHeatmap_new.svg', bbox_inches='tight')
plt.show()

# 4.4 PNN Intensity 热力图
print("绘制 PNN Intensity 热力图...")
ax4 = create_mid_ontology_heatmap(
    data_dict['intensity'], 
    A,
    title='PNN Intensity',
    cmap=args.cmap_intensity,
    vmin=args.vmin_intensity,
    vmax=args.vmax_intensity,
    figsize=(args.fig_w, args.fig_h),
    fontScaling=args.font_scaling
)
plt.savefig(f'{output_dir}/intensityHeatmap_new.svg', bbox_inches='tight')
plt.show()


######### 5. 生成柱状图
print("\n" + "="*50)
print("生成柱状图...")

# 5.1 WFA Diffuse Fluorescence 柱状图
print("绘制 WFA Diffuse Fluorescence 柱状图...")
ax5 = create_coarse_ontology_barplot(
    data_dict['diffuseFluo'], 
    A,
    title='WFA Diffuse Fluorescence',
    cmap=args.cmap_diffuse,
    xlabel='(A.U.)',
    areaNames=True
)
plt.savefig(f'{output_dir}/diffuseBarplot_new.svg', bbox_inches='tight')
plt.show()

# 5.2 PNN Energy 柱状图
print("绘制 PNN Energy 柱状图...")
ax6 = create_coarse_ontology_barplot(
    data_dict['energy'], 
    A,
    title='PNN Energy',
    cmap=args.cmap_energy,
    xlabel='(A.U.)',
    areaNames=True
)
plt.savefig(f'{output_dir}/energyBarplot_new.svg', bbox_inches='tight')
plt.show()


######### 6. 关联图（仿造 gt.metricsCorrelation）
print("\n" + "="*50)
print("生成关联图...")

# 6.1 PNN Energy vs WFA Diffuse Fluorescence 关联图
print("绘制 PNN Energy vs WFA Diffuse Fluorescence 关联图...")
from scipy.stats import spearmanr
from sklearn.linear_model import HuberRegressor
from matplotlib.ticker import MaxNLocator

plt.figure(figsize=(6, 5))
ax_corr = plt.gca()

# 组织数据到 DataFrame，按 region（区域）区分
corr_rows = []
for region in data_dict['diffuseFluo'].index:
    for slice_id in data_dict['diffuseFluo'].columns:
        x_val = data_dict['diffuseFluo'].loc[region, slice_id]
        y_val = data_dict['energy'].loc[region, slice_id]
        if not (np.isnan(x_val) or np.isnan(y_val) or x_val == 0 or y_val == 0):
            corr_rows.append({'region': region, 'x': x_val, 'y': y_val})

corr_df = pd.DataFrame(corr_rows)

if not corr_df.empty:
    sns.set_style('white')

    # 区域调色板（使用固定映射，名称来自 A.ids_to_names）
    unique_regions = sorted(corr_df['region'].unique())
    area_names = A.ids_to_names(unique_regions)
    palette = sns.color_palette('tab10', n_colors=len(unique_regions))
    color_map = {region: palette[i] for i, region in enumerate(unique_regions)}

    # 绘制散点
    sns.scatterplot(
        ax=ax_corr,
        data=corr_df,
        x='x',
        y='y',
        hue='region',
        palette=color_map,
        linewidth=0.4,
        edgecolor='k',
        s=110,
        legend=False,
        alpha=0.95,
    )

    # 为每个区域拟合鲁棒回归线
    for region in unique_regions:
        sub = corr_df[corr_df['region'] == region]
        if len(sub) >= 2:
            huber = HuberRegressor(epsilon=2)
            huber.fit(sub['x'].values.reshape(-1, 1), sub['y'].values.ravel())
            newX = np.linspace(sub['x'].min(), sub['x'].max(), num=25)
            newY = huber.predict(newX.reshape(-1, 1))
            ax_corr.plot(newX, newY, color=color_map[region], alpha=0.9, linewidth=2.2)

    # 图例（区域名称）
    handles = []
    labels = []
    for region in unique_regions:
        h = plt.Line2D([0], [0], marker='o', color=color_map[region], label=A.ids_to_names([region])[0],
                       markerfacecolor=color_map[region], markersize=6, linewidth=0)
        handles.append(h)
        labels.append(A.ids_to_names([region])[0])
    ax_corr.legend(handles, labels, bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False)

    # 等比例与 1:1 参考线
    lims = [
        np.min([ax_corr.get_xlim(), ax_corr.get_ylim()]),
        np.max([ax_corr.get_xlim(), ax_corr.get_ylim()]),
    ]
    ax_corr.plot(lims, lims, 'darkgray', alpha=0.6, zorder=0)
    ax_corr.set_aspect('equal', adjustable='box')

    # 全局 Spearman 相关
    coeff, pval = spearmanr(corr_df['x'], corr_df['y'])
    textColor = plt.cm.get_cmap("OrRd")(0.85)
    ax_corr.text(
        0.95, 0.20,
        r"$r_{s}$" + f"$ = ${coeff:0.2}",
        transform=ax_corr.transAxes,
        fontsize=14,
        ha='right',
        color=textColor if pval < 0.05 else 'dimgray'
    )
    ax_corr.text(
        0.95, 0.08,
        f"$p = ${pval:0.1e}".replace('e-0','e-'),
        transform=ax_corr.transAxes,
        fontsize=14,
        ha='right',
        color=textColor if pval < 0.05 else 'dimgray'
    )

    # 轴与标签风格
    ax_corr.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
    ax_corr.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
    ax_corr.tick_params(axis='x', labelsize=12)
    ax_corr.tick_params(axis='y', labelsize=12)
    ax_corr.set_xlabel('WFA Diffuse Fluorescence (A.U.)', fontsize=14)
    ax_corr.set_ylabel('PNN Energy (A.U.)', fontsize=14)
    ax_corr.set_title('PNN Energy vs WFA Diffuse Fluorescence', fontsize=16, fontweight='bold')
    sns.despine()

plt.tight_layout()
plt.savefig(f'{output_dir}/correlation_new.svg', bbox_inches='tight')
plt.show()

# 6.2 按区域分别绘制并保存单独的 correlation 图
if 'corr_df' in locals() and not corr_df.empty:
    for region in unique_regions:
        sub = corr_df[corr_df['region'] == region]
        if sub.empty:
            continue
        plt.figure(figsize=(5, 4))
        ax_sub = plt.gca()
        # 散点
        plt.scatter(sub['x'], sub['y'], s=90, c=[color_map[region]], edgecolors='k', linewidths=0.4, alpha=0.95)
        # 拟合线
        if len(sub) >= 2:
            huber = HuberRegressor(epsilon=2)
            huber.fit(sub['x'].values.reshape(-1, 1), sub['y'].values.ravel())
            newX = np.linspace(sub['x'].min(), sub['x'].max(), num=25)
            newY = huber.predict(newX.reshape(-1, 1))
            ax_sub.plot(newX, newY, color=color_map[region], alpha=0.9, linewidth=2.2)
        # 1:1线
        lims = [
            np.min([ax_sub.get_xlim(), ax_sub.get_ylim()]),
            np.max([ax_sub.get_xlim(), ax_sub.get_ylim()]),
        ]
        ax_sub.plot(lims, lims, 'darkgray', alpha=0.6, zorder=0)
        ax_sub.set_aspect('equal', adjustable='box')
        #（已按要求还原：不在单图上叠加均值±SEM与名称）
        # 文本
        coeff, pval = spearmanr(sub['x'], sub['y'])
        textColor = plt.cm.get_cmap("OrRd")(0.85)
        ax_sub.text(0.95, 0.20, r"$r_{s}$" + f"$ = ${coeff:0.2}", transform=ax_sub.transAxes, fontsize=12,
                    ha='right', color=textColor if pval < 0.05 else 'dimgray')
        ax_sub.text(0.95, 0.08, f"$p = ${pval:0.1e}".replace('e-0','e-'), transform=ax_sub.transAxes, fontsize=12,
                    ha='right', color=textColor if pval < 0.05 else 'dimgray')
        # 轴
        ax_sub.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
        ax_sub.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
        ax_sub.tick_params(axis='x', labelsize=12)
        ax_sub.tick_params(axis='y', labelsize=12)
        ax_sub.set_xlabel('WFA Diffuse Fluorescence (A.U.)', fontsize=13)
        ax_sub.set_ylabel('PNN Energy (A.U.)', fontsize=13)
        ax_sub.set_title(A.ids_to_names([region])[0], fontsize=14, fontweight='bold')
        sns.despine()
        plt.tight_layout()
        plt.savefig(f"{output_dir}/correlation_{region}.svg", bbox_inches='tight')
        plt.close()

# 6.3 拼接多子图图像（不同 ax）
if 'corr_df' in locals() and not corr_df.empty:
    # 仿造 3x4 子图布局，并遍历 f.axes 的写法
    cols = 4
    rows = int(np.ceil(len(unique_regions) / cols)) if len(unique_regions) > 0 else 1
    f, axs = plt.subplots(nrows=rows, ncols=cols, figsize=(cols*4, rows*3.8), squeeze=True)
    axes = f.axes

    for i, ax in enumerate(axes):
        if i >= len(unique_regions):
            ax.set_visible(False)
            continue
        region = unique_regions[i]
        sub = corr_df[corr_df['region'] == region]
        if sub.empty:
            ax.set_visible(False)
            continue

        # 绘制散点
        ax.scatter(sub['x'], sub['y'], s=90, c=[color_map[region]], edgecolors='k', linewidths=0.4, alpha=0.95)

        # 拟合线（Huber）
        if len(sub) >= 2:
            huber = HuberRegressor(epsilon=2)
            huber.fit(sub['x'].values.reshape(-1, 1), sub['y'].values.ravel())
            newX = np.linspace(sub['x'].min(), sub['x'].max(), num=25)
            newY = huber.predict(newX.reshape(-1, 1))
            ax.plot(newX, newY, color=color_map[region], alpha=0.9, linewidth=2)

        # 1:1参考线与等比例轴
        lims = [np.min([ax.get_xlim(), ax.get_ylim()]), np.max([ax.get_xlim(), ax.get_ylim()])]
        ax.plot(lims, lims, 'darkgray', alpha=0.6, zorder=0)
        ax.set_aspect('equal', adjustable='box')
        #（已按要求还原：不在拼图上叠加均值±SEM与名称）

        # 统计文本位置：左上（tl）或右下（br）交替
        txtLocLeft = (i % 8) in [1,2,3,4]
        coeff, pval = spearmanr(sub['x'], sub['y'])
        textColor = plt.cm.get_cmap('OrRd')(0.85)
        if txtLocLeft:
            ax.text(0.05, 0.88, r"$r_{s}$" + f"$ = ${coeff:0.2}", transform=ax.transAxes, fontsize=11,
                    ha='left', color=textColor if pval < 0.05 else 'dimgray')
            ax.text(0.05, 0.75, f"$p = ${pval:0.1e}".replace('e-0','e-'), transform=ax.transAxes, fontsize=11,
                    ha='left', color=textColor if pval < 0.05 else 'dimgray')
        else:
            ax.text(0.95, 0.20, r"$r_{s}$" + f"$ = ${coeff:0.2}", transform=ax.transAxes, fontsize=11,
                    ha='right', color=textColor if pval < 0.05 else 'dimgray')
            ax.text(0.95, 0.08, f"$p = ${pval:0.1e}".replace('e-0','e-'), transform=ax.transAxes, fontsize=11,
                    ha='right', color=textColor if pval < 0.05 else 'dimgray')

        # 轴与标题风格
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
        ax.tick_params(axis='both', labelsize=10)
        title = A.ids_to_names([region])[0]
        ax.set_title(title, fontsize=12)

        # 仅在特定子图显示轴标签，仿造示例逻辑（i==8）
        if i == 8:
            ax.set_xlabel('WFA Diffuse Fluorescence (A.U.)', fontsize=11)
            ax.set_ylabel('PNN Energy (A.U.)', fontsize=11)
        else:
            ax.set_xlabel('')
            ax.set_ylabel('')

    # 统一去框
    for ax in axes:
        sns.despine(ax=ax)

    f.tight_layout()
    f.savefig(f"{output_dir}/correlation_grid.svg", bbox_inches='tight')
    plt.close(f)

# 6.4 带误差条的相关图（仿造 gt.metricsWithErrors）
def _nan_sem(series: pd.Series) -> float:
    vals = series.values
    vals = vals[~np.isnan(vals)]
    vals = vals[vals != 0]
    if len(vals) <= 1:
        return 0.0
    return np.nanstd(vals, ddof=1) / np.sqrt(len(vals))

if 'data_dict' in locals():
    # 计算每个区域的均值与 SEM（按切片聚合）
    x_mat = data_dict['diffuseFluo']
    y_mat = data_dict['energy']
    x_mean = x_mat.replace(0, np.nan).mean(axis=1)
    y_mean = y_mat.replace(0, np.nan).mean(axis=1)
    x_sem = x_mat.apply(_nan_sem, axis=1)
    y_sem = y_mat.apply(_nan_sem, axis=1)

    err_df = pd.DataFrame({
        'x': x_mean,
        'y': y_mean,
        'err_x': x_sem,
        'err_y': y_sem,
    })

    # 颜色映射与名称
    acrs_err = err_df.index.tolist()
    palette_err = sns.color_palette('tab10', n_colors=len(acrs_err))
    color_map_err = {acr: palette_err[i] for i, acr in enumerate(acrs_err)}

    plt.figure(figsize=(6.5, 5.2))
    ax_err = plt.gca()
    for acr in acrs_err:
        row = err_df.loc[acr]
        ax_err.errorbar(
            row['x'], row['y'],
            xerr=row['err_x'], yerr=row['err_y'],
            fmt='o', markersize=9,
            color=color_map_err[acr], ecolor=color_map_err[acr],
            elinewidth=1.2, capsize=3, alpha=0.9,
            markeredgecolor='k', markeredgewidth=0.4,
        )
        # 区域名称标注（仿造 gt.metricsWithErrors 的 annotations 效果）
        try:
            area_name = A.ids_to_names([acr])[0]
        except Exception:
            area_name = str(acr)
        # 在点的右上方轻微偏移标注，避免与误差条重叠
        ax_err.text(
            row['x'] + max(1e-3, 0.01 * (np.nanmax(x_mean) - np.nanmin(x_mean))),
            row['y'] + max(1e-3, 0.01 * (np.nanmax(y_mean) - np.nanmin(y_mean))),
            area_name,
            fontsize=10,
            color=color_map_err[acr]
        )

    # 1:1 参考线与等比例
    lims = [
        np.min([ax_err.get_xlim(), ax_err.get_ylim()]),
        np.max([ax_err.get_xlim(), ax_err.get_ylim()]),
    ]
    ax_err.plot(lims, lims, 'darkgray', alpha=0.6, zorder=0)
    ax_err.set_aspect('equal', adjustable='box')

    # 轴与标题
    ax_err.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
    ax_err.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
    ax_err.tick_params(axis='both', labelsize=12)
    ax_err.set_xlabel('WFA Diffuse Fluorescence (A.U.)', fontsize=14)
    ax_err.set_ylabel('PNN Energy (A.U.)', fontsize=14)
    ax_err.set_title('Correlation with Error Bars (per region mean ± SEM)', fontsize=15, fontweight='bold')
    sns.despine()

    plt.tight_layout()
    plt.savefig(f"{output_dir}/correlation_with_errors.svg", bbox_inches='tight')
    plt.close()


######### 7. 统计信息
print("\n" + "="*50)
print("统计信息:")

for metric in metrics:
    data = data_dict[metric]
    print(f"\n{metric}:")
    print(f"  数据范围: {data.min().min():.4f} - {data.max().max():.4f}")
    print(f"  平均值: {data.mean().mean():.4f}")
    print(f"  标准差: {data.std().std():.4f}")
    
    # 按切片统计
    print(f"  按切片统计:")
    for slice_id in data.columns:
        slice_data = data[slice_id]
        non_zero_data = slice_data[slice_data != 0]
        if len(non_zero_data) > 0:
            print(f"    切片 {slice_id}: 平均值={non_zero_data.mean():.4f}, 标准差={non_zero_data.std():.4f}")

print(f"\n所有图表已生成并保存到 {output_dir} 目录下")



