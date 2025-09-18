#!/usr/bin/env python3
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
