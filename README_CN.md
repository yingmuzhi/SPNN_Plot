# 脊髓PNN数据分析与可视化项目

## 致谢

感谢 **Leonardo Lupori** 的宝贵帮助，没有他的支持就没有这份文档。

## 项目概述

本项目用于分析脊髓中PNN（Perineuronal Nets）的分布特征，包括密度、能量、强度和弥散荧光等指标，并生成相应的热力图、柱状图、相关性分析和SVG分区着色图。

## 目录结构

```
/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/
├── code/                           # Python脚本目录
│   ├── figure_02_1prepareDataForBrainRender.py    # 数据预处理脚本
│   ├── figure_02_1x_addNoise.py                   # 噪声数据生成脚本（测试用）
│   ├── figure_02_2mainVisualizations_new.py       # 主要可视化脚本
│   ├── figure_02_3renderRegionCal.py              # 区域统计计算脚本
│   ├── figure_02_3renderRegionPlot.py             # 区域热力图生成脚本
│   └── figure_02_3renderSVG.py                    # SVG分区着色脚本
├── src/                            # 数据目录
│   ├── originData/                 # 原始数据
│   │   ├── *.csv                   # 原始实验数据文件
│   │   └── spinalCord_6regions.svg # 脊髓分区SVG模板
│   ├── analysisData/               # 分析数据
│   │   ├── dataFrameForBrainRender.csv
│   │   ├── dataFrameForBrainRender_addNoise.csv
│   │   └── figure_02_spinal_all_slices.csv
│   └── output/                     # 输出结果
│       ├── *.svg                   # 可视化图表
│       └── regionPlot/             # 区域着色图
└── _legacy/                        # 历史版本文件
```

## 脚本功能说明

### 1. figure_02_1prepareDataForBrainRender.py
**功能**: 数据预处理和整合
- 读取原始实验数据（dots和diffFluo文件）
- 计算PNN密度、能量、强度和弥散荧光指标
- 进行全脑归一化处理
- 输出标准化的分析数据表

**输入**: `src/originData/` 目录下的原始CSV文件
**输出**: `dataFrameForBrainRender.csv`

### 2. figure_02_1x_addNoise.py
**功能**: 噪声数据生成（前期测试使用）
- 为现有数据添加高斯噪声
- 生成额外的数据组用于测试
- 支持自定义噪声参数

**输入**: `dataFrameForBrainRender.csv`
**输出**: `dataFrameForBrainRender_addNoise.csv`

### 3. figure_02_2mainVisualizations_new.py
**功能**: 主要可视化分析
- 生成热力图（密度、能量、强度、弥散荧光）
- 生成柱状图
- 相关性分析（PNN能量 vs WFA弥散荧光）
- 误差条相关性图

**输入**: 预处理后的CSV数据
**输出**: 多种SVG格式的可视化图表

### 4. figure_02_3renderRegionCal.py
**功能**: 区域统计计算
- 计算各区域各指标的均值
- 生成颜色映射
- 导出统计结果CSV

**输入**: 分析数据CSV
**输出**: `figure_02_spinal_all_slices.csv`

### 5. figure_02_3renderRegionPlot.py
**功能**: 区域热力图生成
- 基于统计结果生成热力图
- 为每个指标生成SVG分区着色图
- 生成色条图

**输入**: 统计结果CSV和SVG模板
**输出**: 区域着色图和热力图

### 6. figure_02_3renderSVG.py
**功能**: SVG分区着色渲染
- 直接修改SVG文件
- 保持原始形状和曲线
- 应用颜色映射到不同区域

**输入**: SVG模板和颜色映射
**输出**: 着色后的SVG文件

## 完整工作流程

### 步骤1: 环境配置
```bash
# 运行环境配置脚本
python /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/setup_environment.py

# 验证环境配置
python /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/test_environment.py
```

**注意**: 所有必需的依赖包都在 `requirements.txt` 中定义，环境配置脚本会自动安装。

### 步骤2: 数据预处理
```bash
cd /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/code
python figure_02_1prepareDataForBrainRender.py
```

### 步骤3: 生成测试数据（可选）
```bash
python figure_02_1x_addNoise.py
```

### 步骤4: 主要可视化分析
```bash
python figure_02_2mainVisualizations_new.py
```

### 步骤5: 区域统计计算
```bash
python figure_02_3renderRegionCal.py
```

### 步骤6: 生成区域热力图
```bash
python figure_02_3renderRegionPlot.py
```

### 步骤7: SVG分区着色
```bash
python figure_02_3renderSVG.py
```

## 环境配置要求

### Python 3.13 环境配置

#### 1. 自动化环境配置
```bash
# 运行环境配置脚本（推荐方式）
python /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/setup_environment.py
```

#### 2. 手动环境配置（可选）
```bash
# 创建环境名：env_cp313_pnnAnalysis
conda create -n env_cp313_pnnAnalysis python=3.13
conda activate env_cp313_pnnAnalysis

# 安装精确版本的依赖包
pip install -r /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/requirements.txt
```

**注意**: 使用精确版本号（==）确保环境的一致性和可重现性。

#### 3. 验证环境配置
```bash
# 运行环境验证脚本
python /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/test_environment.py
```

**注意**: 所有依赖包都在 `requirements.txt` 中定义，使用精确版本号（==）确保环境的一致性和可重现性。环境配置脚本会自动处理安装过程。

### 核心依赖包版本
- **pandas**: 2.3.2
- **numpy**: 2.3.3
- **scipy**: 1.16.2
- **matplotlib**: 3.10.6
- **seaborn**: 0.13.2
- **scikit-learn**: 1.7.2
- **lxml**: 6.0.1

## 参数配置

### 主要参数说明

#### figure_02_1prepareDataForBrainRender.py
- `--src-folder`: 原始数据目录
- `--output-folder`: 输出目录
- `--output-filename`: 输出文件名

#### figure_02_1x_addNoise.py
- `--input-file`: 输入CSV文件
- `--output-file`: 输出CSV文件
- `--num-extra-groups`: 额外组数
- `--noise-std`: 噪声标准差

#### figure_02_2mainVisualizations_new.py
- `--input-csv`: 输入CSV文件
- `--output-dir`: 输出目录
- `--cmap-*`: 颜色映射设置
- `--vmin-*`, `--vmax-*`: 数值范围设置

## 输出文件说明

### 数据文件
- `dataFrameForBrainRender.csv`: 标准化分析数据
- `dataFrameForBrainRender_addNoise.csv`: 带噪声的测试数据
- `figure_02_spinal_all_slices.csv`: 区域统计结果

### 可视化文件
- `*Heatmap_new.svg`: 热力图
- `*Barplot_new.svg`: 柱状图
- `correlation_*.svg`: 相关性图
- `colored_regions_*.svg`: 区域着色图

## 故障排除

### 常见问题

1. **导入错误**: 确保所有依赖包已正确安装
2. **文件路径错误**: 检查输入文件路径是否正确
3. **内存不足**: 对于大数据集，考虑分批处理
4. **SVG渲染问题**: 确保SVG模板文件存在且格式正确

### 调试建议

1. 使用 `--help` 参数查看所有可用选项
2. 检查输入文件格式和列名
3. 验证输出目录权限
4. 查看控制台输出的错误信息

## 联系信息

如有问题，请检查：
1. Python版本是否为3.13
2. 所有依赖包是否已安装
3. 输入文件路径是否正确
4. 输出目录是否有写入权限
