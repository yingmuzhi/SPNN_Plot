import pandas as pd
import os
import numpy as np
import argparse

# 参数解析
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare data for brain render with per-acronym group mids")
    parser.add_argument(
        "--src-folder",
        default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/originData",
        help="Folder containing origin data CSV files (default: %(default)s)",
    )
    parser.add_argument(
        "--output-folder",
        default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData",
        help="Folder to write analysis outputs (default: %(default)s)",
    )
    parser.add_argument(
        "--output-filename",
        default="dataFrameForBrainRender.csv",
        help="Output CSV filename (default: %(default)s)",
    )
    return parser.parse_args()


args = parse_args()

# 设置数据路径
src_folder = args.src_folder
output_folder = args.output_folder

# 确保输出文件夹存在
os.makedirs(output_folder, exist_ok=True)

print("开始处理数据...")

# 获取所有数据文件
files = os.listdir(src_folder)
print(f"找到 {len(files)} 个数据文件")

# 分离不同类型的文件
dots_wfa_files = [f for f in files if '_dots_wfa_' in f]
diffFluo_wfa_files = [f for f in files if '_diffFluo_wfa_' in f]
dots_pv_files = [f for f in files if '_dots_pv_' in f]
diffFluo_pv_files = [f for f in files if '_diffFluo_pv_' in f]

print(f"WFA dots文件: {len(dots_wfa_files)}")
print(f"WFA diffFluo文件: {len(diffFluo_wfa_files)}")
print(f"PV dots文件: {len(dots_pv_files)}")
print(f"PV diffFluo文件: {len(diffFluo_pv_files)}")

# 处理WFA数据
def process_channel_data(dots_files, diff_files, channel_name):
    """处理特定通道的数据"""
    all_data = []
    
    for dots_file in dots_files:
        # 从文件名提取区域ID
        region_id = dots_file.split('manualRegion')[1].split('_')[0]
        
        dots_path = os.path.join(src_folder, dots_file)
        diff_path = os.path.join(src_folder, [f for f in diff_files if f'manualRegion{region_id}' in f][0])
        
        print(f"处理 {channel_name} 区域 {region_id}...")
        
        # 读取dots数据
        dots = pd.read_csv(dots_path)
        # 读取diffFluo数据
        diff = pd.read_csv(diff_path)
        
        # 1. 聚合细胞信息
        group = dots.groupby('regionID').agg(
            numCells=('cellID', 'count'),
            fluoCellSum=('fluoMean', 'sum'),
            fluoCellMean=('fluoMean', 'mean')
        )
        
        # 2. 合并弥散荧光信息
        diff = diff.set_index('regionID')
        df = diff.join(group, how='left').fillna(0)
        
        # 3. 计算各项指标
        df['density'] = df['numCells'] / df['areaMm2']
        df['diffuseFluo'] = df['diffFluo'] / df['areaPx']
        df['intensity'] = df['fluoCellMean']  # 使用平均荧光强度
        df['energy'] = df['fluoCellSum'] / df['areaMm2']
        
        # 添加区域信息
        df['regionID'] = int(region_id)
        df['region'] = region_id
        
        all_data.append(df)
    
    return pd.concat(all_data, ignore_index=True)

# 处理WFA数据
print("\n处理WFA数据...")
wfa_data = process_channel_data(dots_wfa_files, diffFluo_wfa_files, 'WFA')

# 处理PV数据（可选，不用于最终指标，但保留统计信息）
print("\n处理PV数据...")
pv_data = process_channel_data(dots_pv_files, diffFluo_pv_files, 'PV') if len(dots_pv_files) > 0 else pd.DataFrame()

# 为每个区域(region)计算出现顺序，从1开始作为 group（组数）
# 使用 cumcount 保留重复区域的先后次序
wfa_data = wfa_data.copy()
wfa_data['group'] = wfa_data.groupby('region').cumcount() + 1

print("\n按区域分组统计 group：")
counts = wfa_data.groupby('region')['group'].max().to_dict()
for acr, cnt in counts.items():
    print(f"区域 {acr}: 共有 {cnt} 组（group 1..{cnt}）")

# 合成最终 DataFrame（使用 WFA 指标）
print("\n合并数据...")
final_df = wfa_data[['group', 'density', 'diffuseFluo', 'energy', 'intensity', 'region']].copy()

# 全脑归一化（基于 WFA，总和方式）
print("\n进行全脑归一化...")
# 重新计算全脑归一化因子（基于总和，不是平均值）
# 需要重新读取原始数据来计算全脑总和
total_diffFluo = 0
total_energy = 0
total_areaPx = 0
total_areaMm2 = 0
total_fluoCellSum = 0

for dots_file in dots_wfa_files:
    region_id = dots_file.split('manualRegion')[1].split('_')[0]
    dots_path = os.path.join(src_folder, dots_file)
    diff_path = os.path.join(src_folder, [f for f in diffFluo_wfa_files if f'manualRegion{region_id}' in f][0])
    
    dots = pd.read_csv(dots_path)
    diff = pd.read_csv(diff_path)
    
    # 累加全脑数据
    total_diffFluo += diff['diffFluo'].iloc[0]
    total_areaPx += diff['areaPx'].iloc[0]
    total_areaMm2 += diff['areaMm2'].iloc[0]
    total_fluoCellSum += dots['fluoMean'].sum()

# 计算全脑归一化因子
brain_diffFluo = total_diffFluo / total_areaPx if total_areaPx != 0 else 1.0
brain_energy = total_fluoCellSum / total_areaMm2 if total_areaMm2 != 0 else 1.0

print(f"全脑归一化因子 - diffuseFluo: {brain_diffFluo:.6f}, energy: {brain_energy:.6f}")

final_df['diffuseFluo'] = final_df['diffuseFluo'] / brain_diffFluo
final_df['energy'] = final_df['energy'] / brain_energy

# 保存结果
output_path = os.path.join(output_folder, args.output_filename)
final_df.to_csv(output_path, index=False)

print(f"\n数据处理完成！")
print(f"输出文件: {output_path}")
print(f"处理了 {len(final_df)} 个脑区行（含重复区域各组）")
print("\n数据预览:")
print(final_df.head())

print("\n统计信息:")
print(final_df.describe())
