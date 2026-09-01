import re
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Define Custom Patterns and Recognizers
aadhaar_pattern = Pattern(
    name="aadhaar_pattern",
    regex=r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b",
    score=0.9
)
aadhaar_recognizer = PatternRecognizer(
    supported_entity="AADHAAR",
    patterns=[aadhaar_pattern]
)

pan_pattern = Pattern(
    name="pan_pattern",
    regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    score=0.9
)
pan_recognizer = PatternRecognizer(
    supported_entity="PAN",
    patterns=[pan_pattern],
    global_regex_flags=re.MULTILINE
)

mrn_pattern = Pattern(
    name="mrn_pattern",
    regex=r"\b(?:MRN|MR|PID|Patient\s*ID|Record\s*ID)[:\s-]*([A-Z0-9-]+)\b",
    score=0.85
)
mrn_recognizer = PatternRecognizer(
    supported_entity="MRN",
    patterns=[mrn_pattern]
)

# High score of 0.95 to prioritize over built-in DATE_TIME (usually 0.85)
age_pattern = Pattern(
    name="age_pattern",
    regex=r"\b\d{1,3}\s*(?:years?\s*(?:old)?|yo|y/o|years?\s*of\s*age)\b",
    score=0.95
)
age_recognizer = PatternRecognizer(
    supported_entity="AGE",
    patterns=[age_pattern]
)

hospital_pattern = Pattern(
    name="hospital_pattern",
    regex=r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Hospital|Clinic|Medical\s+Center|Sanatorium|Infirmary))\b",
    score=0.8
)
hospital_recognizer = PatternRecognizer(
    supported_entity="HOSPITAL",
    patterns=[hospital_pattern],
    global_regex_flags=re.MULTILINE
)

# Initialize NLP Engine with en_core_web_sm
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
}
provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

# Initialize Analyzer and add custom recognizers
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
analyzer.registry.add_recognizer(aadhaar_recognizer)
analyzer.registry.add_recognizer(pan_recognizer)
analyzer.registry.add_recognizer(mrn_recognizer)
analyzer.registry.add_recognizer(age_recognizer)
analyzer.registry.add_recognizer(hospital_recognizer)

# Initialize Anonymizer
anonymizer = AnonymizerEngine()

# Operators configuration for anonymization
anonymizer_operators = {
    "PATIENT_NAME": OperatorConfig("replace", {"new_value": "[PATIENT_NAME]"}),
    "DOCTOR_NAME": OperatorConfig("replace", {"new_value": "[DOCTOR_NAME]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE]"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "[ADDRESS]"}),
    "AADHAAR": OperatorConfig("replace", {"new_value": "[AADHAAR]"}),
    "PAN": OperatorConfig("replace", {"new_value": "[PAN]"}),
    "MRN": OperatorConfig("replace", {"new_value": "[MRN]"}),
    "AGE": OperatorConfig("replace", {"new_value": "[AGE]"}),
    "HOSPITAL": OperatorConfig("replace", {"new_value": "[HOSPITAL]"}),
    "ORGANIZATION": OperatorConfig("replace", {"new_value": "[HOSPITAL]"}),
    "UK_NHS": OperatorConfig("replace", {"new_value": "[PHONE]"}),  # Map NHS numbers (10 digits) to PHONE or PATIENT_ID
    "US_SSN": OperatorConfig("replace", {"new_value": "[PATIENT_ID]"}),
}

IGNORE_NAMES = {"aadhaar", "pan", "mrn", "pid", "patient", "doctor", "hospital", "clinic", "date"}

def remove_overlaps(analyzer_results):
    """
    Sorts analyzer results by start index, and resolves overlaps by keeping
    the entity with the higher score, or the longer entity in case of ties.
    """
    if not analyzer_results:
        return []
        
    sorted_results = sorted(analyzer_results, key=lambda x: (x.start, -(x.end - x.start)))
    keep_results = []
    
    for res in sorted_results:
        if not keep_results:
            keep_results.append(res)
            continue
            
        prev = keep_results[-1]
        
        # If no overlap, just append
        if res.start >= prev.end:
            keep_results.append(res)
        else:
            # Overlap! Compare scores
            if res.score > prev.score:
                keep_results[-1] = res
            elif res.score == prev.score:
                # Keep the longer one
                prev_len = prev.end - prev.start
                res_len = res.end - res.start
                if res_len > prev_len:
                    keep_results[-1] = res
                    
    return keep_results

def deidentify_text(text: str):
    """
    Analyzes medical text for PHI/PII, distinguishes between patients and doctors,
    resolves overlaps, and replaces sensitive info with clean labels.
    """
    if not text.strip():
        return {
            "deidentified_text": "",
            "entities": []
        }
        
    # Analyze text
    results = analyzer.analyze(text=text, language="en")
    
    # Process results to separate DOCTOR_NAME vs PATIENT_NAME and filter out ignore list
    processed_results = []
    for res in results:
        entity_type = res.entity_type
        entity_val = text[res.start:res.end].strip()
        
        # Check against deny list of common terms misclassified as PERSON
        if entity_type in ["PERSON", "ORGANIZATION"] and entity_val.lower() in IGNORE_NAMES:
            continue
            
        # Check context for PERSON entities
        if entity_type == "PERSON":
            lookback = text[max(0, res.start - 15):res.start].lower()
            if any(title in lookback for title in ["dr", "doctor", "physician", "surgeon"]):
                entity_type = "DOCTOR_NAME"
            else:
                entity_type = "PATIENT_NAME"
                
        res.entity_type = entity_type
        processed_results.append(res)
        
    # Resolve overlapping entities
    final_results = remove_overlaps(processed_results)
    
    # Capture final entity details for UI
    detected_entities = []
    for res in final_results:
        entity_val = text[res.start:res.end]
        detected_entities.append({
            "entity_type": res.entity_type,
            "text": entity_val,
            "start": res.start,
            "end": res.end,
            "confidence": res.score
        })
        
    # Anonymize text using the overlap-resolved results
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=final_results,
        operators=anonymizer_operators
    )
    
    return {
        "deidentified_text": anonymized_result.text,
        "entities": detected_entities
    }
