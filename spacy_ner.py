import spacy
from spacy.matcher import Matcher
from spacy.pipeline import EntityRuler
import logging

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

# Add custom patterns for greetings
greeting_patterns = [
    {"label": "GREETING", "pattern": [{"LOWER": "hello"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "hi"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "hey"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "good"}, {"LOWER": "morning"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "good"}, {"LOWER": "afternoon"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "good"}, {"LOWER": "evening"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "how"}, {"LOWER": "are"}, {"LOWER": "you"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "how"}, {"LOWER": "is"}, {"LOWER": "it"}, {"LOWER": "going"}]},
    {"label": "GREETING", "pattern": [{"LOWER": "howdy"}]},
]

# Create and add the EntityRuler to the pipeline
ruler = nlp.add_pipe("entity_ruler", before="ner")
ruler.add_patterns(greeting_patterns)

def initialize_matcher(abend_data):
    global matcher
    matcher = Matcher(nlp.vocab)
    for code in abend_data["AbendCode"].unique():
        matcher.add("ABEND_CODE", [[{"TEXT": code}]])
    for name in abend_data["AbendName"].unique():
        matcher.add("ABEND_NAME", [[{"LOWER": token} for token in name.lower().split()]])
    logging.debug("Matcher initialized with abend codes and names.")
    logging.debug(f"Abend codes: {[code for code in abend_data['AbendCode'].unique()]}")
    logging.debug(f"Abend names: {[name.lower() for name in abend_data['AbendName'].unique()]}")

def extract_entities(text, abend_data):
    doc = nlp(text.lower())
    entities = {"greeting": None, "abend_code": None, "abend_name": None, "intent": "unknown"}

    logging.debug(f"Processing text: {text}")
    
    for ent in doc.ents:
        logging.debug(f"Detected entity: {ent.text} with label: {ent.label_}")
        if ent.label_ == "GREETING":
            entities["greeting"] = ent.text
        elif ent.label_ == "ABEND_CODE":
            entities["abend_code"] = ent.text
        elif ent.label_ == "ABEND_NAME":
            entities["abend_name"] = ent.text

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        logging.debug(f"Match found: {nlp.vocab.strings[match_id]} - {span.text}")
        if nlp.vocab.strings[match_id] == "ABEND_CODE":
            entities["abend_code"] = span.text.upper()
        elif nlp.vocab.strings[match_id] == "ABEND_NAME":
            entities["abend_name"] = span.text

    logging.debug(f"Extracted entities from text: {entities}")
    return entities
