#!/usr/bin/env python3
"""
Environment Setup Script for PNN Analysis Project
Python 3.13 Environment Configuration
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.13 or compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 13:
        print("✅ Python version is compatible")
        return True
    else:
        print("⚠️  Warning: Python 3.13+ is recommended for optimal performance")
        return True  # Allow older versions to continue

def suggest_environment_setup():
    """Suggest environment setup commands"""
    print("\n💡 Environment Setup Suggestions:")
    print("To create the recommended environment 'env_cp313_pnnAnalysis':")
    print("conda create -n env_cp313_pnnAnalysis python=3.13")
    print("conda activate env_cp313_pnnAnalysis")
    print("pip install -r requirements.txt")

def install_requirements():
    """Install required packages from requirements.txt"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Installing required packages"
    )

def verify_installation():
    """Verify that all required packages are installed"""
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'seaborn', 
        'scipy', 'sklearn', 'lxml'
    ]
    
    print("🔍 Verifying package installation...")
    
    for package in required_packages:
        try:
            if package == 'sklearn':
                import sklearn
                print(f"✅ {package} (scikit-learn) imported successfully")
            else:
                __import__(package)
                print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            return False
    
    return True

def create_test_script():
    """Create a test script to verify the environment"""
    test_script = Path(__file__).parent / "test_environment.py"
    
    test_content = '''#!/usr/bin/env python3
"""
Test script to verify PNN analysis environment
"""

def test_imports():
    """Test all required imports"""
    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        import scipy.stats
        from sklearn.linear_model import HuberRegressor
        import xml.etree.ElementTree as ET
        import lxml
        
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    try:
        import pandas as pd
        import numpy as np
        
        # Test DataFrame creation
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        print(f"✅ DataFrame creation: {df.shape}")
        
        # Test numpy operations
        arr = np.array([1, 2, 3, 4, 5])
        print(f"✅ NumPy operations: mean={arr.mean()}")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing PNN Analysis Environment...")
    
    if test_imports() and test_basic_functionality():
        print("🎉 Environment setup successful!")
    else:
        print("❌ Environment setup failed!")
        sys.exit(1)
'''
    
    with open(test_script, 'w') as f:
        f.write(test_content)
    
    print(f"✅ Test script created: {test_script}")
    return test_script

def main():
    """Main setup function"""
    print("🚀 Setting up PNN Analysis Environment...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("❌ Python version check failed")
        return False
    
    # Install requirements
    if not install_requirements():
        print("❌ Package installation failed")
        return False
    
    # Verify installation
    if not verify_installation():
        print("❌ Package verification failed")
        return False
    
    # Create test script
    test_script = create_test_script()
    
    # Suggest environment setup
    suggest_environment_setup()
    
    print("=" * 50)
    print("🎉 Environment setup completed successfully!")
    print(f"📝 Run 'python {test_script}' to test the environment")
    print("📚 See README_CN.md or README.md for usage instructions")
    print("🔧 Recommended environment name: env_cp313_pnnAnalysis")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
