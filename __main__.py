"""
__main__.py

Purpose:
--------
Entry point for the application.
Wraps src/main.py to allow execution from root directory.
"""
import sys
import os

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.main import main
except ImportError:
    # If running as python __main__.py from root, src should be importable
    from src.main import main

if __name__ == "__main__":
    main()
