from flask import Flask, request, jsonify, session
from flask_session import Session
from spacy_ner import extract_entities, initialize_matcher
from load_data import load_abend_data
import pandas as pd
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


# Function to load and initialize abend data
def load_and_initialize():
    global abend_data
    abend_data = load_abend_data('abend_data.xlsx')
    initialize_matcher(abend_data)


# Initial load and initialize
load_and_initialize()


def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']


@app.route('/get_solution', methods=['POST'])
def get_solution():
    user_input = request.json.get('message')
    user_id = get_user_id()

    entities = extract_entities(user_input, abend_data)

    if entities["greeting"]:
        greeting_response = {
            "hello": "Hello! How can I assist you with your abend issues today?",
            "hi": "Hi there! How can I help you with your abend issues?",
            "hey": "Hey! What abend issue can I help you with?",
            "good morning": "Good morning! How can I assist you today?",
            "good afternoon": "Good afternoon! How can I assist you today?",
            "good evening": "Good evening! How can I assist you today?",
            "how are you": "I'm just a bot, but I'm here to help! How can I assist you?",
            "how is it going": "It's going great! How can I assist you today?",
            "howdy": "Howdy! What abend issue can I help you with?",
        }
        response = greeting_response.get(entities["greeting"].lower(), "Hello! How can I assist you today?")
        return jsonify({"solution": response})

    abend_code = entities["abend_code"]
    abend_name = entities["abend_name"]
    intent = entities["intent"]
    response = None

    if intent == "get_solution" or intent == "unknown":
        if abend_code:
            row = abend_data.loc[abend_data['AbendCode'] == abend_code]
            if not row.empty:
                abend_name = row['AbendName'].values[0]
                solution = row['Solution'].values[0]
                response = f"**Abend Name:** {abend_name}\n\n**Solution:** {solution}"

        if abend_name and response is None:
            row = abend_data.loc[abend_data['AbendName'].str.contains(abend_name, case=False, na=False)]
            if not row.empty:
                abend_code = row['AbendCode'].values[0]
                solution = row['Solution'].values[0]
                response = f"**Abend Code:** {abend_code}\n\n**Solution:** {solution}"

    elif intent == "get_definition":
        if abend_code:
            row = abend_data.loc[abend_data['AbendCode'] == abend_code]
            if not row.empty:
                abend_name = row['AbendName'].values[0]
                response = f"**Abend Name:** {abend_name}\n\n**Definition:** {abend_name}"

        if abend_name and response is None:
            row = abend_data.loc[abend_data['AbendName'].str.contains(abend_name, case=False, na=False)]
            if not row.empty:
                abend_code = row['AbendCode'].values[0]
                response = f"**Abend Code:** {abend_code}\n\n**Definition:** {abend_name}"

    if response:
        return jsonify({"solution": response})
    else:
        fallback_response = "I'm not sure about that. Can you please provide more details or ask a different question?"
        return jsonify({"solution": fallback_response})


@app.route('/refresh_data', methods=['POST'])
def refresh_data():
    load_and_initialize()
    return jsonify({"status": "Data refreshed successfully"})


if __name__ == '__main__':
    app.run(debug=True)
