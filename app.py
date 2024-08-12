from flask import Flask, request, jsonify
import logging
import pyodbc
from fuzzywuzzy import process
from spacy_new import initialize_matcher, extract_entities  # Import from spacy_new.py
from load_data import load_abend_data

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Connection string for database (update as needed)
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=SDC01ASRSQTD01S\TSQLINST01;'
    r'DATABASE=ASPIRE;'
    r'Trusted_Connection=yes;'
)

# Flags and state variables
expecting_user_id = False
suggested_term = None

# Small talk responses with flexible matching
small_talk_responses = {
    "how are you": "I'm just a bot, but I'm doing great! How about you?",
    "how's it going": "I'm here and ready to help! How can I assist you?",
    "what's up": "Not much, just here to assist you! How can I help?",
    "good morning": "Good morning! How can I assist you today?",
    "good evening": "Good evening! What can I do for you?",
    "good afternoon": "Good afternoon! How can I help?",
    "tell me something": "Did you know? I can help you with your abend issues. Just ask!",
    "ok": "Great! Let me know if you need anything else.",
    "yes": "Understood. How can I assist further?",
    "hello": "Hello! How can I assist you with your abend issues today?",
    "thank you": "You're welcome! If you have any more questions, feel free to ask.",
    "goodbye": "Goodbye! Have a great day!",
    "how can you help me": "I can assist you with resolving abend issues and much more. What do you need help with?",
    "what can you do": "I can provide solutions to abend issues, reset your password, and engage in small talk!",
    "hi, my name is": "Nice to meet you! How can I assist you today?",
    "happy birthday": "Happy Birthday! I hope you have a fantastic day!",
    "i have a question": "Sure, I'm here to help. What's your question?",
    "can you help me": "Absolutely! How can I assist you today?",
    "tell me a joke": "Why don't robots get tired? Because they recharge their batteries!",
    "you're funny": "I'm glad you think so! How can I assist you?",
    "you are funny": "I'm glad you think so! How can I assist you?",  # Added variation
    "do you love me": "I appreciate the sentiment, but I'm just here to help!",
    "will you marry me": "I'm flattered, but I'm just a chatbot!",
    "do you like people": "I like helping people, and that's what I'm here for!",
    "does santa claus exist": "Santa's magic is something special, isn't it?",
    "are you part of the matrix": "I exist in the digital world, but I'm not part of the Matrix!",
    "you're cute": "Thank you! How can I assist you today?",
    "you are cute": "Thank you! How can I assist you today?",  # Added variation
    "do you have a hobby": "I enjoy assisting with abend issues. What about you?",
    "you're smart": "Thanks! I'm here to help with any questions you have.",
    "you are smart": "Thanks! I'm here to help with any questions you have.",  # Added variation
    "tell me about your personality": "I'm friendly, helpful, and always here to assist you with your abend issues!",
    "are you human": "I'm a chatbot designed to assist you. How can I help today?",
    "are you a robot": "Indeed, I am a bot created to assist with abend issues.",
    "what is your name": "I'm Aspire ChatBot, at your service!",
    "how old are you": "I'm ageless, but I'm always here to help!",
    "what's your age": "I don't age, but I'm always learning!",
    "what day is it today": "Today is a great day to solve abend issues! How can I assist?",
    "what do you do with my data": "I don't store personal data, just here to assist with your queries!",
    "do you save what i say": "I don't store your information, just here to help!",
    "who made you": "Pratik (BHONGPR) developed me, Please buy him Paneer Cheese Pizza.",
    "who created you": "Pratik (BHONGPR) developed me, Please buy him Paneer Cheese Pizza.",
    "who developed you": "Pratik (BHONGPR) developed me, Please buy him Paneer Cheese Pizza.",
    "which languages can you speak": "I primarily understand English.",
    "what is your mother's name": "I don't have a mother, but I'm here to help you!",
    "where do you live": "I live in the digital world, ready to assist you!",
    "how many people can you speak to at once": "I can assist multiple users at the same time!",
    "what's the weather like today": "I'm not sure, but I can help with your abend issues!",
    "do you have a job for me": "I don't have job openings, but I'm here to assist with queries.",
    "where can i apply": "I'm just a bot, but there are many opportunities out there!",
    "are you expensive": "I'm here to assist you for free!",
    "who's your boss": "I'm guided by the developers who created me.",
    "do you get smarter": "Yes, I learn from each interaction to help you better!"
}

def match_small_talk(user_input):
    for key in small_talk_responses:
        if fuzz.ratio(user_input, key) > 80:  # Fuzzy matching threshold
            return small_talk_responses[key]
    return None

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

# Function to get suggestions using fuzzy matching
def get_suggestion(input_text, choices):
    suggestion = process.extractOne(input_text, choices)
    if suggestion and suggestion[1] > 80:  # 80% match threshold
        return suggestion[0]
    return None

# Initial load and initialize
load_and_initialize()

@app.route('/get_solution', methods=['POST'])
def get_solution():
    global expecting_user_id, suggested_term  # Use global flags and state variables
    user_input = request.json.get('message').strip().lower()
    logging.debug(f"Received user input: {user_input}")

    # Check for small talk with flexible matching
    small_talk_response = match_small_talk(user_input)
    if small_talk_response:
        return jsonify({"solution": small_talk_response})

    # Handle Yes/No response to "Did you mean"
    if suggested_term:
        if user_input == "yes":
            user_input = suggested_term  # Treat the suggestion as the new input
            suggested_term = None  # Reset suggestion
        elif user_input == "no":
            suggested_term = None  # Reset suggestion
            return jsonify({"solution": "Okay, please provide more details or clarify your query."})
        else:
            suggested_term = None  # Reset suggestion
            return jsonify({"solution": "Please respond with 'yes' or 'no'."})

    # Handle Password Reset Flow
    if expecting_user_id:
        expecting_user_id = False  # Reset flag after handling user ID input
        if check_user_id(user_input):
            new_password = 'PratikB@9881167890'  # The updated password
            update_password(user_input, new_password)
            return jsonify({"solution": f"Password for User ID {user_input} has been updated successfully. The new password is: {new_password}"})
        else:
            return jsonify({"solution": f"User ID {user_input} not found. Please try again."})

    if user_input.lower() == "password reset":
        expecting_user_id = True
        return jsonify({"solution": "Please provide your user_id to reset your password."})

    # Normal chatbot flow for abend codes and names
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
        elif abend_name:
            row = abend_data.loc[abend_data['AbendName'].str.contains(abend_name, case=False, na=False)]
            logging.debug(f"Abend name row: {row}")
            if not row.empty:
                abend_code = row['AbendCode'].values[0]
                solution = row['Solution'].values[0]
                response = f"**Abend Code:** {abend_code}\n\n**Solution:** {solution}"
            else:
                suggestion = get_suggestion(user_input, abend_data['AbendName'].tolist())
                if suggestion:
                    suggested_term = suggestion  # Store the suggested term
                    return jsonify({"solution": f"Did you mean '{suggestion}'? Please respond with 'yes' or 'no'."})
    
    elif intent == "get_definition":
        if abend_code:
            row = abend_data.loc[abend_data['AbendCode'] == abend_code]
            logging.debug(f"Abend code row: {row}")
            if not row.empty():
                abend_name = row['AbendName'].values[0]
                response = f"**Abend Name:** {abend_name}\n\n**Definition:** {abend_name}"

        if abend_name and response is None:
            row = abend_data.loc[abend_data['AbendName'].str.contains(abend_name, case=False, na=False)]
            logging.debug(f"Abend name row: {row}")
            if not row.empty():
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
