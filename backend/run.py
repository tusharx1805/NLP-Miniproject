import os
import sys

# Ensure Windows DLL search paths are configured before importing uvicorn or app
try:
    venv_scripts = os.path.abspath(os.path.dirname(sys.executable))
    venv_root = os.path.dirname(venv_scripts)
    if os.path.exists(venv_scripts):
        os.add_dll_directory(venv_scripts)
    if os.path.exists(venv_root):
        os.add_dll_directory(venv_root)
except Exception:
    pass

import uvicorn

if __name__ == "__main__":
    # Start uvicorn server on localhost:8000
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
