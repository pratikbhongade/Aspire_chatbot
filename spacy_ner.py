import spacy
from spacy.matcher import Matcher
from spacy.pipeline import EntityRuler

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
    matcher.add("ABEND_CODE", [[{"TEXT": code}] for code in abend_data["AbendCode"].unique()])
    matcher.add("ABEND_NAME", [[{"TEXT": {"REGEX": name}}] for name in abend_data["AbendName"].unique()])


def extract_entities(text, abend_data):
    doc = nlp(text)
    entities = {"greeting": None, "abend_code": None, "abend_name": None, "intent": "unknown"}

    for ent in doc.ents:
        if ent.label_ == "GREETING":
            entities["greeting"] = ent.text
        elif ent.label_ == "ABEND_CODE":
            entities["abend_code"] = ent.text
        elif ent.label_ == "ABEND_NAME":
            entities["abend_name"] = ent.text

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        if nlp.vocab.strings[match_id] == "ABEND_CODE":
            entities["abend_code"] = span.text
        elif nlp.vocab.strings[match_id] == "ABEND_NAME":
            entities["abend_name"] = span.text

    return entities
