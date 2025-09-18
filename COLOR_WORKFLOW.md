# Color Computation and Visualization Workflow (English)

## Overview

After the refactor, color computation and rendering are decoupled:

1. `figure_02_3renderRegionCal.py` — computes color mappings and writes them to CSV
2. `figure_02_3renderRegionPlot.py` — reads colors from CSV and renders SVG/heatmaps

## Workflow

### Step 1: Color computation (`figure_02_3renderRegionCal.py`)

```bash
# Scientific colormaps (default)
python figure_02_3renderRegionCal.py

# Diverging colormap
python figure_02_3renderRegionCal.py --colormap-style diverging

# Print-friendly grayscale
python figure_02_3renderRegionCal.py --print-friendly

# Export colorbars for publication
python figure_02_3renderRegionCal.py --save-colorbar
```

- Output: `src/analysisData/figure_02_spinal_all_slices.csv`
- CSV columns:
  - `metric`: density, diffuseFluo, energy, intensity
  - `scope`: `all_slices` (SVG) or `heatmap` (matrix)
  - `region`: region id
  - `group`: slice id (heatmap only)
  - `value`: raw value
  - `color`: hex color
  - `normalized_value`: normalized value (heatmap only)
  - `vmin`, `vmax`: value range (heatmap only)

### Step 2: Rendering (`figure_02_3renderRegionPlot.py`)

```bash
# Render all
python figure_02_3renderRegionPlot.py

# Only SVG
python figure_02_3renderRegionPlot.py --skip-heatmap

# Only heatmaps
python figure_02_3renderRegionPlot.py --skip-svg

# Custom paths
python figure_02_3renderRegionPlot.py \
  --csv-file /path/to/figure_02_spinal_all_slices.csv \
  --output-dir /path/to/output
```

## Consistency

- SVG: uses `scope = all_slices`, one color per region (mean across slices)
- Heatmap: uses `scope = heatmap`, per (group, region) cell
- All colors are computed in `figure_02_3renderRegionCal.py` and stored in CSV; the renderer never recomputes colors

## Colormap Sources and Guidelines

Color choices follow scientific and colorblind-friendly practices:

- ColorBrewer sequential palettes:
  - Reds (energy/intensity)
  - Blues (diffuse fluorescence)
  - Greens (density)
  - Purples (intensity)
- Viridis (perceptually uniform, colorblind-friendly)
- Diverging Red–Blue (for signed/baseline-relative metrics)
- Grayscale (print-friendly)

Implementation details:

- All mappings computed once in `figure_02_3renderRegionCal.py` and written to CSV
- `figure_02_3renderRegionPlot.py` reads the `color` field to ensure consistency between SVG and heatmaps
- CLI switching:
  - `--colormap-style scientific|diverging|grayscale|viridis`
  - `--print-friendly` forces grayscale
  - `--save-colorbar` exports publication-ready colorbars

Recommendations:

- Monotonic metrics (density/diffuseFluo/energy/intensity): prefer ColorBrewer sequential or viridis
- Signed/relative metrics: prefer diverging (Red–Blue)
- B/W printing: use `--print-friendly`
- Always export colorbars for interpretability and reproducibility

## Benefits

1. Consistent colors across SVG and heatmaps
2. Maintainable: color logic centralized; rendering is lightweight
3. Flexible: switch styles and outputs via CLI
4. Reproducible: CSV stores colors and `vmin/vmax`

## Troubleshooting

- Missing CSV: run `figure_02_3renderRegionCal.py` first
- Missing colors: verify input columns (group, region, metrics)
- Heatmap issues: ensure `scope = heatmap` rows exist in CSV
