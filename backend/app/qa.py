from app.model_loader import get_model_and_tokenizer

def is_answer_in_text(answer: str, text: str) -> bool:
    """
    Checks if the core content words of the generated answer are actually
    present in the de-identified reference text. This prevents hallucinations
    from small models.
    """
    # Clean and split into words
    words = [w.strip(".,;:?!'\"()[]").lower() for w in answer.split()]
    
    # Common function words that don't need to be in the text
    stop_words = {
        "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", 
        "of", "in", "at", "to", "on", "with", "by", "for", "it", "they", 
        "he", "she", "patient", "record", "medical", "doctor", "dr"
    }
    
    content_words = [w for w in words if w and w not in stop_words]
    
    if not content_words:
        return answer.lower().strip() in text.lower()
        
    text_lower = text.lower()
    return all(w in text_lower for w in content_words)

def check_tag_intent_match(answer: str, question: str) -> bool:
    """
    Validates if a returned de-identification placeholder tag corresponds semantically
    to the query being asked. Prevents cross-tag hallucinations in small models.
    Uses whole-word set matching to avoid substring clashes.
    """
    # Clean and split question into a set of words
    q_words = {w.strip(".,;:?!'\"()[] ") for w in question.lower().split()}
    ans_upper = answer.upper().strip(".,;:?!'\"()[] ")
    
    tag_keywords = {
        "HOSPITAL": {"hospital", "clinic", "medical", "center", "where", "place", "institution", "visited", "at", "organization", "facility"},
        "PATIENT_NAME": {"patient", "name", "who", "person", "subject", "client"},
        "DOCTOR_NAME": {"doctor", "dr", "physician", "surgeon", "who", "provider", "clinician"},
        "AADHAAR": {"aadhaar", "card", "id", "number", "national", "uid"},
        "PAN": {"pan", "card", "id", "number", "tax"},
        "MRN": {"mrn", "record", "id", "number", "patient id", "pid"},
        "AGE": {"age", "old", "years", "yo", "y/o"},
        "DATE": {"date", "when", "year", "month", "day", "visited", "on", "time"},
        "PHONE": {"phone", "contact", "mobile", "number", "call", "telephone"},
        "EMAIL": {"email", "mail"},
        "ADDRESS": {"address", "location", "live", "where", "residence", "home"}
    }
    
    if ans_upper in tag_keywords:
        allowed_keywords = tag_keywords[ans_upper]
        # Returns True if the set of question words has an intersection with allowed keywords
        return not q_words.isdisjoint(allowed_keywords)
        
    return True

def answer_question(deidentified_text: str, question: str) -> str:
    """
    Answers a clinical question based STRICTLY on the de-identified medical text
    using the FLAN-T5 model.
    """
    if not deidentified_text.strip():
        return "The information is not available in the provided medical record."
        
    if not question.strip():
        return "Please ask a valid question."
        
    try:
        model, tokenizer = get_model_and_tokenizer()
        
        # Build prompt precisely as requested
        prompt = (
            "Answer the question using only the medical record below.\n\n"
            "If the answer is not explicitly available, respond:\n"
            "'The information is not available in the provided medical record.'\n\n"
            "Do not invent clinical facts.\n"
            "Do not provide new medical advice.\n\n"
            f"Medical record:\n{deidentified_text}\n\n"
            f"Question:\n{question}\n"
        )
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        
        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            num_beams=4,
            early_stopping=True
        )
        
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        
        # Post-process response for small model compatibility (FLAN-T5-small)
        ans_lower = answer.lower().strip()
        negative_indicators = {
            "0", "none", "no", "n/a", "null", "unknown", "unspecified", 
            "not mentioned", "not stated", "not found", "not given", "not listed"
        }
        
        # Check standard negative indicators
        if (
            not answer or
            ans_lower in negative_indicators or
            "not available" in ans_lower or
            "not mentioned" in ans_lower or
            "information is not" in ans_lower or
            "not explicitly available" in ans_lower or
            len(answer) <= 3
        ):
            return "The information is not available in the provided medical record."
            
        # Verify the answer does not contain hallucinated facts (i.e. all content words are in text)
        if not is_answer_in_text(answer, deidentified_text):
            return "The information is not available in the provided medical record."
            
        # Verify that placeholder tags correspond to the question intent
        if not check_tag_intent_match(answer, question):
            return "The information is not available in the provided medical record."
            
        return answer
        
    except Exception as e:
        return f"QA failure: {str(e)}"
