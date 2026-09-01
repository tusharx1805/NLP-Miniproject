from app.model_loader import get_model_and_tokenizer

def generate_summary(deidentified_text: str) -> str:
    """
    Generates a medical summary using the FLAN-T5 model, acting strictly
    on de-identified text.
    """
    if not deidentified_text.strip():
        return "No text provided to summarize."
        
    try:
        model, tokenizer = get_model_and_tokenizer()
        
        # Formulate a clear prompt for FLAN-T5 text summarization
        prompt = (
            f"Provide a concise clinical summary of the following medical record:\n\n"
            f"{deidentified_text}\n\n"
            f"Clinical Summary:"
        )
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Run text generation
        outputs = model.generate(
            **inputs,
            max_new_tokens=120,
            min_length=20,
            num_beams=4,
            length_penalty=1.5,
            early_stopping=True
        )
        
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary.strip()
        
    except Exception as e:
        return f"Summarization failed: {str(e)}"
