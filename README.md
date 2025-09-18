# Spinal Cord PNN Data Analysis and Visualization Project

## Project Overview

This project analyzes the distribution characteristics of PNN (Perineuronal Nets) in the spinal cord, including density, energy, intensity, and diffuse fluorescence metrics, and generates corresponding heatmaps, bar plots, correlation analyses, and SVG regional coloring maps.

## Directory Structure

```
/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/
├── code/                           # Python scripts directory
│   ├── figure_02_1prepareDataForBrainRender.py    # Data preprocessing script
│   ├── figure_02_1x_addNoise.py                   # Noise data generation script (for testing)
│   ├── figure_02_2mainVisualizations_new.py       # Main visualization script
│   ├── figure_02_3renderRegionCal.py              # Regional statistics calculation script
│   ├── figure_02_3renderRegionPlot.py             # Regional heatmap generation script
│   └── figure_02_3renderSVG.py                    # SVG regional coloring script
├── src/                            # Data directory
│   ├── originData/                 # Raw data
│   │   ├── *.csv                   # Raw experimental data files
│   │   └── spinalCord_6regions.svg # Spinal cord regional SVG template
│   ├── analysisData/               # Analysis data
│   │   ├── dataFrameForBrainRender.csv
│   │   ├── dataFrameForBrainRender_addNoise.csv
│   │   └── figure_02_spinal_all_slices.csv
│   └── output/                     # Output results
│       ├── *.svg                   # Visualization charts
│       └── regionPlot/             # Regional coloring maps
└── _legacy/                        # Legacy version files
```

## Script Functionality

### 1. figure_02_1prepareDataForBrainRender.py
**Function**: Data preprocessing and integration
- Reads raw experimental data (dots and diffFluo files)
- Calculates PNN density, energy, intensity, and diffuse fluorescence metrics
- Performs whole-brain normalization
- Outputs standardized analysis data table

**Input**: Raw CSV files in `src/originData/` directory
**Output**: `dataFrameForBrainRender.csv`

### 2. figure_02_1x_addNoise.py
**Function**: Noise data generation (for preliminary testing)
- Adds Gaussian noise to existing data
- Generates additional data groups for testing
- Supports custom noise parameters

**Input**: `dataFrameForBrainRender.csv`
**Output**: `dataFrameForBrainRender_addNoise.csv`

### 3. figure_02_2mainVisualizations_new.py
**Function**: Main visualization analysis
- Generates heatmaps (density, energy, intensity, diffuse fluorescence)
- Generates bar plots
- Correlation analysis (PNN energy vs WFA diffuse fluorescence)
- Error bar correlation plots

**Input**: Preprocessed CSV data
**Output**: Various SVG format visualization charts

### 4. figure_02_3renderRegionCal.py
**Function**: Regional statistics calculation
- Calculates mean values for each region and metric
- Generates color mapping
- Exports statistical results CSV

**Input**: Analysis data CSV
**Output**: `figure_02_spinal_all_slices.csv`

### 5. figure_02_3renderRegionPlot.py
**Function**: Regional heatmap generation
- Generates heatmaps based on statistical results
- Creates SVG regional coloring maps for each metric
- Generates color bar charts

**Input**: Statistical results CSV and SVG template
**Output**: Regional coloring maps and heatmaps

### 6. figure_02_3renderSVG.py
**Function**: SVG regional coloring rendering
- Directly modifies SVG files
- Preserves original shapes and curves
- Applies color mapping to different regions

**Input**: SVG template and color mapping
**Output**: Colored SVG files

## Complete Workflow

### Step 1: Environment Setup
```bash
# Create Python 3.13 environment
conda create -n pnn_analysis python=3.13
conda activate pnn_analysis

# Install dependencies
pip install pandas numpy matplotlib seaborn scipy scikit-learn xml
```

### Step 2: Data Preprocessing
```bash
cd /data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/code
python figure_02_1prepareDataForBrainRender.py
```

### Step 3: Generate Test Data (Optional)
```bash
python figure_02_1x_addNoise.py
```

### Step 4: Main Visualization Analysis
```bash
python figure_02_2mainVisualizations_new.py
```

### Step 5: Regional Statistics Calculation
```bash
python figure_02_3renderRegionCal.py
```

### Step 6: Generate Regional Heatmaps
```bash
python figure_02_3renderRegionPlot.py
```

### Step 7: SVG Regional Coloring
```bash
python figure_02_3renderSVG.py
```

## Environment Configuration Requirements

### Python 3.13 Environment Setup

#### 1. Create Virtual Environment
```bash
# Using conda
conda create -n pnn_analysis python=3.13
conda activate pnn_analysis

# Or using venv
python3.13 -m venv pnn_analysis_env
source pnn_analysis_env/bin/activate  # Linux/Mac
# pnn_analysis_env\Scripts\activate    # Windows
```

#### 2. Install Dependencies
```bash
# Basic scientific computing packages
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install scipy>=1.10.0

# Visualization packages
pip install matplotlib>=3.7.0
pip install seaborn>=0.12.0

# Machine learning packages
pip install scikit-learn>=1.3.0

# XML processing
pip install lxml>=4.9.0

# Optional: Jupyter support
pip install jupyter notebook
```

#### 3. Verify Installation
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats
from sklearn.linear_model import HuberRegressor
import xml.etree.ElementTree as ET

print("All dependencies installed successfully!")
```

## Parameter Configuration

### Main Parameter Descriptions

#### figure_02_1prepareDataForBrainRender.py
- `--src-folder`: Raw data directory
- `--output-folder`: Output directory
- `--output-filename`: Output filename

#### figure_02_1x_addNoise.py
- `--input-file`: Input CSV file
- `--output-file`: Output CSV file
- `--num-extra-groups`: Number of extra groups
- `--noise-std`: Noise standard deviation

#### figure_02_2mainVisualizations_new.py
- `--input-csv`: Input CSV file
- `--output-dir`: Output directory
- `--cmap-*`: Color mapping settings
- `--vmin-*`, `--vmax-*`: Value range settings

## Output File Descriptions

### Data Files
- `dataFrameForBrainRender.csv`: Standardized analysis data
- `dataFrameForBrainRender_addNoise.csv`: Test data with noise
- `figure_02_spinal_all_slices.csv`: Regional statistical results

### Visualization Files
- `*Heatmap_new.svg`: Heatmaps
- `*Barplot_new.svg`: Bar plots
- `correlation_*.svg`: Correlation plots
- `colored_regions_*.svg`: Regional coloring maps

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are correctly installed
2. **File Path Errors**: Check if input file paths are correct
3. **Memory Issues**: For large datasets, consider batch processing
4. **SVG Rendering Issues**: Ensure SVG template files exist and are in correct format

### Debugging Suggestions

1. Use `--help` parameter to view all available options
2. Check input file format and column names
3. Verify output directory permissions
4. Review console output error messages

## Contact Information

If you encounter issues, please check:
1. Python version is 3.13
2. All dependencies are installed
3. Input file paths are correct
4. Output directory has write permissions

## Data Processing Pipeline

The complete data processing pipeline follows this sequence:

1. **Raw Data Collection**: Experimental data from spinal cord regions
2. **Data Preprocessing**: Normalization and metric calculation
3. **Quality Control**: Noise addition for testing (optional)
4. **Statistical Analysis**: Regional statistics and color mapping
5. **Visualization**: Heatmaps, bar plots, and correlation analysis
6. **Regional Mapping**: SVG-based regional coloring

## Key Metrics Analyzed

- **Density**: PNN cell density per unit area
- **Energy**: Total PNN fluorescence energy
- **Intensity**: Average PNN fluorescence intensity
- **Diffuse Fluorescence**: Background fluorescence levels

## Output Quality

All visualizations are generated in high-quality SVG format suitable for publication, with customizable color schemes and statistical annotations.
