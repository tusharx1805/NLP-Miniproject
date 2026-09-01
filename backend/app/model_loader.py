import os
import sys

# Ensure Windows DLL search paths are configured before importing transformers
try:
    venv_scripts = os.path.abspath(os.path.dirname(sys.executable))
    venv_root = os.path.dirname(venv_scripts)
    if os.path.exists(venv_scripts):
        os.add_dll_directory(venv_scripts)
    if os.path.exists(venv_root):
        os.add_dll_directory(venv_root)
except Exception:
    pass

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

_model = None
_tokenizer = None
MODEL_NAME = "google/flan-t5-small"

def get_model_and_tokenizer():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        # Load the tokenizer and Seq2Seq model for FLAN-T5
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _model, _tokenizer
