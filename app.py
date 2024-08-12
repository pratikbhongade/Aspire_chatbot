from flask import Flask, request, jsonify
from spacy_ner import extract_entities, initialize_matcher
from load_data import load_abend_data
import logging
import pyodbc

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the connection string for the database
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=SDC01ASRSQTD01S\TSQLINST01;'
    r'DATABASE=ASPIRE;'
    r'Trusted_Connection=yes;'
)

# Function to check if user_id exists in SecurityUser table
def check_user_id(user_id):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        query = "SELECT * FROM SecurityUser WHERE user_id = ?"
        cursor.execute(query, user_id)
        result = cursor.fetchone()
        
        if result:
            return True
        else:
            return False
    
    except Exception as e:
        logging.error(f"Error checking user_id: {e}")
        return False
    
    finally:
        if 'connection' in locals():
            connection.close()

# Function to update the password for a given user_id
def update_password(user_id, new_password):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        query = "UPDATE SecurityUser SET password = ? WHERE user_id = ?"
        cursor.execute(query, (new_password, user_id))
        connection.commit()
        
        logging.info(f"Password for User ID {user_id} has been updated.")
    
    except Exception as e:
        logging.error(f"Error updating password: {e}")
    
    finally:
        if 'connection' in locals():
            connection.close()

# Function to load and initialize abend data
def load_and_initialize():
    global abend_data
    abend_data = load_abend_data('abend_data.xlsx')
    initialize_matcher(abend_data)
    logging.debug("Abend data loaded and matcher initialized.")

# Initial load and initialize
load_and_initialize()

@app.route('/get_solution', methods=['POST'])
def get_solution():
    user_input = request.json.get('message')
    logging.debug(f"Received user input: {user_input}")

    entities = extract_entities(user_input, abend_data)
    logging.debug(f"Extracted entities: {entities}")

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
            "thanks": "You're welcome! If you have any more questions, feel free to ask.",
            "thank you": "You're welcome! Let me know if there's anything else I can help with.",
            "bye": "Goodbye! Have a great day!",
        }
        response = greeting_response.get(entities["greeting"].lower(), "Hello! How can I assist you today?")
        return jsonify({"solution": response})

    if "password reset" in user_input.lower():
        return jsonify({"solution": "Please provide your user_id to reset your password.", "action": "request_user_id"})

    user_id = entities.get("user_id")
    if user_id:
        if check_user_id(user_id):
            new_password = '$2a$10$n4XPILjNXBKlcS5FkhxPE.vCYW5KH1GDKAnoaea8LsFkfpuInrbm2'  # Example hashed password
            update_password(user_id, new_password)
            return jsonify({"solution": f"Password for User ID {user_id} has been updated successfully."})
        else:
            return jsonify({"solution": f"User ID {user_id} not found. Please try again."})

    abend_code = entities["abend_code"]
    abend_name = entities["abend_name"]
    intent = entities["intent"]
    response = None

    if intent == "get_solution" or intent == "unknown":
        if abend_code:
            row = abend_data.loc[abend_data['AbendCode'] == abend_code]
            logging.debug(f"Abend code row: {row}")
            if not row.empty:
                abend_name = row['AbendName'].values[0]
                solution = row['Solution'].values[0]
                response = f"**Abend Name:** {abend_name}\n\n**Solution:** {solution}"

        if abend_name and response is None:
            row = abend_data.loc[abend_data['AbendName'].str.contains(abend_name, case=False, na=False)]
            logging.debug(f"Abend name row: {row}")
            if not row.empty:
                abend_code = row['AbendCode'].values[0]
                solution = row['Solution'].values[0]
                response = f"**Abend Code:** {abend_code}\n\n**Solution:** {solution}"

    elif intent == "get_definition":
        if abend_code:
            row = abend_data.loc[abend_data['AbendCode'] == abend_code]
            logging.debug(f"Abend code row: {row}")
            if not row.empty:
                abend_name = row['AbendName'].values[0]
                response = f"**Abend Name:** {abend_name}\n\n**Definition:** {abend_name}"

        if abend_name and response is None:
            row = abend_data.loc[abend_data['AbendName'].str.contains(abend_name, case=False, na=False)]
            logging.debug(f"Abend name row: {row}")
            if not row.empty:
                abend_code = row['AbendCode'].values[0]
                response = f"**Abend Code:** {abend_code}\n\n**Definition:** {abend_name}"

    if response:
        logging.debug(f"Response: {response}")
        return jsonify({"solution": response})
    else:
        fallback_response = "I'm not sure about that. Can you please provide more details or ask a different question?"
        logging.debug("Fallback response.")
        return jsonify({"solution": fallback_response})

@app.route('/refresh_data', methods=['POST'])
def refresh_data():
    load_and_initialize()
    return jsonify({"status": "Data refreshed successfully"})

if __name__ == '__main__':
    app.run(debug=True)
