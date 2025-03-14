import sys
print("Python executable:", sys.executable)
try:
    import pandas as pd
    print("pandas version:", pd.__version__)
except ImportError:
    print("pandas NOT installed")