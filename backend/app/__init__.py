# Initialize Windows DLL Search Paths for Python 3.8+ compatibility
import os
import sys

# Get virtual environment paths relative to this file
# This package is in backend/app/__init__.py, virtual env is usually at backend/.venv
# Let's locate the .venv root and Scripts directory.
try:
    venv_scripts = os.path.abspath(os.path.dirname(sys.executable))
    venv_root = os.path.dirname(venv_scripts)
    
    if os.path.exists(venv_scripts):
        os.add_dll_directory(venv_scripts)
    if os.path.exists(venv_root):
        os.add_dll_directory(venv_root)
except Exception:
    pass
