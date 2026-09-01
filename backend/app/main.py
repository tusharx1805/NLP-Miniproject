import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.deid import deidentify_text
from app.summarizer import generate_summary
from app.qa import answer_question
from app.model_loader import get_model_and_tokenizer

# Lifespan manager to pre-load FLAN-T5 model on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_model_and_tokenizer()
        print("CareText backend initialized: FLAN-T5 and spaCy models loaded.")
    except Exception as e:
        print(f"Error loading models on startup: {str(e)}")
    yield

app = FastAPI(
    title="CareText Backend",
    description="Private Clinical Text Intelligence API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev integration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input Request Models
class ProcessRequest(BaseModel):
    text: str

class AskRequest(BaseModel):
    text: str
    question: str

@app.get("/api/status")
def get_status():
    """
    Returns the status of the CareText API and models.
    """
    try:
        # Check if model loads successfully
        get_model_and_tokenizer()
        return {
            "status": "online",
            "model": "google/flan-t5-small",
            "spacy_model": "en_core_web_sm",
            "message": "CareText Clinical Intelligence Engine is fully operational."
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": f"Engine failed to load models: {str(e)}"
        }

@app.post("/api/process")
async def process_record(req: ProcessRequest):
    """
    De-identifies a medical record and generates a clinical summary based
    ONLY on the de-identified version of the text.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Medical text cannot be empty.")
        
    start_time = time.time()
    
    try:
        # Step 1: De-identify text (removes names, Aadhaar, PAN, MRN, etc.)
        deid_result = deidentify_text(req.text)
        deidentified_text = deid_result["deidentified_text"]
        entities = deid_result["entities"]
        
        # Step 2: Summarize text using ONLY the de-identified version
        summary = generate_summary(deidentified_text)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "original_text": req.text,
            "deidentified_text": deidentified_text,
            "entities": entities,
            "summary": summary,
            "processing_time_ms": processing_time_ms,
            "privacy_status": "Secure (De-identified)"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Clinical text processing failed: {str(e)}"
        )

@app.post("/api/ask")
async def ask_question_endpoint(req: AskRequest):
    """
    Answers a clinical question based STRICTLY on the de-identified version
    of the medical text.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Clinical reference text cannot be empty.")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    try:
        # Q&A model executes using ONLY de-identified text
        answer = answer_question(req.text, req.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Clinical Q&A inference failed: {str(e)}"
        )
