#!/usr/bin/env python3
"""
Complete PNN Analysis Workflow Script
Runs the entire analysis pipeline from data preprocessing to visualization
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
import time

class PNNAnalysisWorkflow:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.code_dir = self.base_dir / "code"
        self.src_dir = self.base_dir / "src"
        self.output_dir = self.src_dir / "output"
        
    def run_script(self, script_name, description, args=None):
        """Run a Python script with error handling"""
        script_path = self.code_dir / script_name
        
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return False
        
        print(f"🔄 {description}...")
        print(f"📁 Running: {script_name}")
        
        try:
            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ {description} completed successfully")
            
            # Print any important output
            if result.stdout:
                print("📝 Output:", result.stdout.decode().strip())
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check if code directory exists
        if not self.code_dir.exists():
            print(f"❌ Code directory not found: {self.code_dir}")
            return False
        
        # Check if source data exists
        origin_data_dir = self.src_dir / "originData"
        if not origin_data_dir.exists():
            print(f"❌ Origin data directory not found: {origin_data_dir}")
            return False
        
        # Check for CSV files in origin data
        csv_files = list(origin_data_dir.glob("*.csv"))
        if not csv_files:
            print(f"❌ No CSV files found in {origin_data_dir}")
            return False
        
        print(f"✅ Found {len(csv_files)} CSV files in origin data")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        return True
    
    def step1_data_preprocessing(self):
        """Step 1: Data preprocessing"""
        return self.run_script(
            "figure_02_1prepareDataForBrainRender.py",
            "Data preprocessing and integration"
        )
    
    def step2_noise_generation(self, skip_noise=False):
        """Step 2: Noise data generation (optional)"""
        if skip_noise:
            print("⏭️  Skipping noise generation (as requested)")
            return True
        
        return self.run_script(
            "figure_02_1x_addNoise.py",
            "Noise data generation for testing"
        )
    
    def step3_main_visualization(self):
        """Step 3: Main visualization analysis"""
        return self.run_script(
            "figure_02_2mainVisualizations_new.py",
            "Main visualization analysis"
        )
    
    def step4_regional_statistics(self):
        """Step 4: Regional statistics calculation"""
        return self.run_script(
            "figure_02_3renderRegionCal.py",
            "Regional statistics calculation"
        )
    
    def step5_regional_heatmaps(self):
        """Step 5: Regional heatmap generation"""
        return self.run_script(
            "figure_02_3renderRegionPlot.py",
            "Regional heatmap generation"
        )
    
    def step6_svg_coloring(self):
        """Step 6: SVG regional coloring"""
        return self.run_script(
            "figure_02_3renderSVG.py",
            "SVG regional coloring"
        )
    
    def run_complete_workflow(self, skip_noise=False, verbose=False):
        """Run the complete analysis workflow"""
        print("🚀 Starting Complete PNN Analysis Workflow")
        print("=" * 60)
        
        start_time = time.time()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites check failed")
            return False
        
        # Step 1: Data preprocessing
        if not self.step1_data_preprocessing():
            print("❌ Data preprocessing failed")
            return False
        
        # Step 2: Noise generation (optional)
        if not self.step2_noise_generation(skip_noise):
            print("❌ Noise generation failed")
            return False
        
        # Step 3: Main visualization
        if not self.step3_main_visualization():
            print("❌ Main visualization failed")
            return False
        
        # Step 4: Regional statistics
        if not self.step4_regional_statistics():
            print("❌ Regional statistics failed")
            return False
        
        # Step 5: Regional heatmaps
        if not self.step5_regional_heatmaps():
            print("❌ Regional heatmaps failed")
            return False
        
        # Step 6: SVG coloring
        if not self.step6_svg_coloring():
            print("❌ SVG coloring failed")
            return False
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 60)
        print("🎉 Complete PNN Analysis Workflow Finished Successfully!")
        print(f"⏱️  Total time: {duration:.2f} seconds")
        print(f"📁 Results saved in: {self.output_dir}")
        
        # List output files
        output_files = list(self.output_dir.rglob("*.svg"))
        if output_files:
            print(f"📊 Generated {len(output_files)} visualization files")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Complete PNN Analysis Workflow")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Base directory path (default: script directory)"
    )
    parser.add_argument(
        "--skip-noise",
        action="store_true",
        help="Skip noise generation step"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Create workflow instance
    workflow = PNNAnalysisWorkflow(args.base_dir)
    
    # Run complete workflow
    success = workflow.run_complete_workflow(
        skip_noise=args.skip_noise,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
