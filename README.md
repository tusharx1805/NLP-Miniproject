# CareText - Private Clinical Text Intelligence

CareText is a secure, interactive NLP workspace designed to de-identify clinical medical texts and perform summarization and Q&A exclusively on the de-identified data. This architecture ensures that sensitive Protected Health Information (PHI) and personally identifiable information (PII) never reach the AI processing layers, safeguarding patient privacy.

## Features
1. **Interactive Clinical Note Workspace:** Paste medical records directly or upload `.txt` files with real-time character/word count.
2. **Robust PHI/PII Scrubbing:** Powered by **Microsoft Presidio + spaCy (`en_core_web_sm`)**, with custom pattern recognizers for:
   - Patient & Doctor names (using a smart lookback buffer)
   - Aadhaar Cards (12-digit Indian national identity numbers)
   - PAN Cards (10-digit Indian Permanent Account Numbers)
   - Medical Record Numbers (MRN) / Patient IDs
   - Patient Age & DOB
   - Hospital, clinic, and medical center identifiers
3. **Overlapping Entity Resolution:** A custom overlap filter that prioritizes higher-confidence and longer matches to prevent double-anonymization and preserve syntax.
4. **Clinical Summary Generation:** Generates text summaries using **FLAN-T5-small** executing *strictly* on de-identified notes.
5. **Interactive Q&A Console:** Clinicians can ask questions about the medical record (using pre-defined suggestions or custom input). The model processes only the de-identified version of the text.
6. **Zero Permanent Storage:** Patient text is processed entirely in-memory and never stored.

---

## Technical Stack
- **Frontend:** React, Vite, Lucide-React, Vanilla CSS (Premium Dark Mode Medical Dashboard)
- **Backend:** Python FastAPI, Uvicorn
- **NLP Engines:** spaCy, Microsoft Presidio (Analyzer & Anonymizer)
- **Generative AI Model:** Hugging Face Transformers (`google/flan-t5-small` running locally on CPU)

---

## Folder Structure
```
CareText/
├── backend/
│   ├── app/
│   │   ├── __init__.py      # Dynamic Windows DLL path resolution for spaCy/PyTorch
│   │   ├── main.py          # FastAPI app and endpoints
│   │   ├── deid.py          # Presidio & spaCy de-identification logic
│   │   ├── summarizer.py    # HF summarization pipeline
│   │   ├── qa.py            # FLAN-T5 question answering engine
│   │   └── model_loader.py  # Shared FLAN-T5 singleton loader
│   ├── tests/
│   │   └── test_main.py     # Pytest automated test suite
│   ├── requirements.txt     # Python dependencies
│   └── run.py               # Backend startup entrypoint
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # React workspace and state orchestration
│   │   ├── main.jsx         # App rendering
│   │   └── index.css        # Clinical dark-mode CSS styling
│   ├── index.html           # Main browser layout
│   └── package.json         # Node.js dependencies
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python (3.10+; tested on Python 3.14.7)

### 1. Backend Setup (FastAPI)
1. Navigate to the `backend/` directory.
2. Initialize virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - **Windows:** `.venv\Scripts\activate`
   - **macOS/Linux:** `source .venv/bin/activate`
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
5. Install the spaCy model:
   ```bash
   pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
   ```
6. Run the server:
   ```bash
   python run.py
   ```
   The API will start on `http://127.0.0.1:8000`.

### 2. Frontend Setup (React/Vite)
1. Navigate to the `frontend/` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## Running Tests
To execute the automated backend test suite, run the following command from the `backend/` directory:
```bash
.venv/Scripts/python.exe -m pytest tests
```
The test cases verify endpoint uptime, PHI scrubbing rules, summarization flow, and correct Q&A behaviors.
