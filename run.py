#!/usr/bin/env python3
"""
Runner script for the GitHub Repo Analyzer API
"""
import uvicorn
import sys
import os

# Add the src directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    uvicorn.run("src.router.main:app", host="0.0.0.0", port=8000, reload=True) 