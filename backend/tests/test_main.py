import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure Windows DLL search paths are configured before importing app
try:
    venv_scripts = os.path.abspath(os.path.dirname(sys.executable))
    venv_root = os.path.dirname(venv_scripts)
    if os.path.exists(venv_scripts):
        os.add_dll_directory(venv_scripts)
    if os.path.exists(venv_root):
        os.add_dll_directory(venv_root)
except Exception:
    pass

from app.main import app

client = TestClient(app)

def test_api_status():
    """
    Test status endpoint is online or degraded (never crashing)
    """
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["online", "degraded"]

def test_api_process_deidentification():
    """
    Test de-identification and clinical summary generation.
    Verifies that name, Aadhaar, PAN, MRN, phone, DOB, age, address, and hospital
    names are replaced by anonymization tags.
    """
    original_text = (
        "Patient John Doe (age 45 years old), Aadhaar: 1234-5678-9012, PAN: ABCDE1234F, "
        "visited Dr. Alice Smith at City General Hospital on 2026-08-11. "
        "Contact: 9876543210. Email: patient@mail.com. MRN: MRN-98765."
    )
    
    response = client.post("/api/process", json={"text": original_text})
    assert response.status_code == 200
    data = response.json()
    
    deid_text = data["deidentified_text"]
    
    # Assert tag replacements
    assert "[PATIENT_NAME]" in deid_text
    assert "[DOCTOR_NAME]" in deid_text
    assert "[AADHAAR]" in deid_text
    assert "[PAN]" in deid_text
    assert "[HOSPITAL]" in deid_text
    assert "[AGE]" in deid_text
    assert "[PHONE]" in deid_text
    assert "[EMAIL]" in deid_text
    assert "[MRN]" in deid_text
    assert "[DATE]" in deid_text
    
    # Assert that raw sensitive parameters are completely scrubbed
    assert "John Doe" not in deid_text
    assert "Alice Smith" not in deid_text
    assert "1234-5678-9012" not in deid_text
    assert "ABCDE1234F" not in deid_text
    assert "9876543210" not in deid_text
    assert "patient@mail.com" not in deid_text
    assert "MRN-98765" not in deid_text
    
    # Assert summary is generated
    assert "summary" in data
    assert len(data["summary"]) > 0

def test_api_ask_valid():
    """
    Test Q&A on de-identified text references
    """
    deidentified_text = (
        "Patient [PATIENT_NAME] is a [AGE] male with symptoms of persistent cough. "
        "Diagnosed with acute bronchitis. Prescribed Albuterol inhaler."
    )
    
    response = client.post("/api/ask", json={
        "text": deidentified_text,
        "question": "What was the diagnosis?"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "bronchitis" in data["answer"].lower()

def test_api_ask_unavailable():
    """
    Test Q&A fallback when answers are not explicitly available.
    """
    deidentified_text = (
        "Patient [PATIENT_NAME] is a [AGE] male with symptoms of persistent cough. "
        "Diagnosed with acute bronchitis. Prescribed Albuterol inhaler."
    )
    
    response = client.post("/api/ask", json={
        "text": deidentified_text,
        "question": "What was the patient's Aadhaar card number?"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The information is not available in the provided medical record."
