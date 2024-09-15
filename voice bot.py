from flask import Flask, request, jsonify
import logging
import pyodbc
from fuzzywuzzy import fuzz, process
from spacy_ner import initialize_matcher, extract_entities
from load_data import load_abend_data
import bcrypt
import secrets
import string
import win32com.client as win32
from speech_recognition import recognize_speech  # Import the speech recognition functionality

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
expecting_otp = False
user_id_for_reset = None
otp_store = {}
suggested_term = None

# Small talk responses
small_talk_responses = {
    "how are you": "I'm just a bot, but I'm doing great! How about you?",
    "how's it going": "I'm here and ready to help! How can I assist you?",
    "ok": "Okay! Let me know if there's anything else you need.",
    "fine": "Great! What else can I do for you?",
    "perfect": "I'm glad to hear that! How can I assist you further?",
    "cool": "Cool! Feel free to ask if you need more help.",
    "good": "Good to know! How can I assist you further?",
    "yes": "Understood. How can I assist further?",
    "hello": "Hello! How can I assist you with your abend issues today?",
    "thank you": "You're welcome! Feel free to ask anything else.",
    "thanks": "You're welcome! Feel free to ask anything else.",
    "goodbye": "Goodbye! Have a great day!",
    "can you help me": "Absolutely! How can I assist you today?",
    "tell me a joke": "Why don't robots get tired? Because they recharge their batteries!",
    "you're funny": "I'm glad you think so! How can I assist you?",
    "do you love me": "I appreciate the sentiment, but I'm just here to help!",
    "will you marry me": "I'm flattered, but I'm just a chatbot!",
    "do you like people": "I like helping people, and that's what I'm here for!",
    "does santa claus exist": "Santa's magic is something special, isn't it?",
    "are you part of the matrix": "I exist in the digital world, but I'm not part of the Matrix!",
    "you're cute": "Thank you! How can I assist you today?",
    "do you have a hobby": "I enjoy assisting with abend issues. What about you?",
    "you're smart": "Thanks! I'm here to help with any questions you have.",
    "tell me about your personality": "I'm friendly, helpful, and always here to assist you with your abend issues!",
    "are you human": "I'm a chatbot designed to assist you. How can I help today?",
    "what is your name": "I'm Aspire ChatBot, at your service!",
    "how old are you": "I'm ageless, but I'm always here to help!",
    "what day is it today": "Today is a great day to solve abend issues! How can I assist?",
    "what do you do with my data": "I don't store personal data, just here to assist with your queries!",
    "do you save what i say": "I don't store your information, just here to help!",
    "who made you": "Pratik (BHONGPR) developed me. Please buy him Paneer Cheese Pizza.",
    "who created you": "Pratik (BHONGPR) developed me. Please buy him Paneer Cheese Pizza.",
    "who developed you": "Pratik (BHONGPR) developed me. Please buy him Paneer Cheese Pizza.",
    "what's the weather like today": "I'm not sure, but I can help with your abend issues!"
}

password_reset_variations = [
    "password reset", "aspire password reset", "password help", "reset aspire password",
    "help with password", "reset my password", "i need a password reset"
]

def match_small_talk(user_input):
    for key in small_talk_responses:
        if fuzz.ratio(user_input, key) > 80:  # Fuzzy matching threshold
            return small_talk_responses[key]
    return None

def match_password_reset(user_input):
    for variation in password_reset_variations:
        if fuzz.ratio(user_input, variation) > 80:
            return True
    return False

# Generate a random password
def generate_random_password(length=15):
    characters = string.ascii_letters + string.digits + string.punctuation
    random_password = ''.join(secrets.choice(characters) for _ in range(length))
    return random_password

# Generate a bcrypt hash from a plain text password
def generate_encrypted_password(plain_text_password):
    salt = bcrypt.gensalt(rounds=10, prefix=b"2a")
    hashed_password = bcrypt.hashpw(plain_text_password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Generate a random OTP
def generate_otp():
    return ''.join(secrets.choice(string.digits) for _ in range(6))

# Check if user_id exists in SecurityUser table
def check_user_id(user_id):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        query = "SELECT * FROM SecurityUser WHERE user_id = ?"
        cursor.execute(query, user_id)
        result = cursor.fetchone()
        return bool(result)
    except Exception as e:
        logging.error(f"Error checking user_id: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

# Update password for a given user_id
def update_password(user_id, encrypted_password):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        query = "UPDATE SecurityUser SET password = ?, deactivation_date = NULL WHERE user_id = ?"
        cursor.execute(query, (encrypted_password, user_id))
        connection.commit()
        logging.info(f"Password for User ID {user_id} has been updated.")
    except Exception as e:
        logging.error(f"Error updating password: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

# Send email via Outlook
def send_email(to_address, subject="Aspire Password Confirmation", body="", email_type="password_reset"):
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = to_address
        mail.Subject = subject

        if email_type == "otp":
            mail.HTMLBody = f"""
            <html>
            <body>
                <h2>Aspire Password Reset OTP</h2>
                <p>Dear User,</p>
                <p>Please use the following OTP to reset your password:</p>
                <h3>{body}</h3>
                <p><b>Note:</b> This OTP is valid for a short period. Please use it promptly.</p>
                <p>If you did not request this OTP, please contact your administrator immediately.</p>
                <p>Thank you for using Aspire services.</p>
                <p>Best regards,<br>The Aspire Team</p>
            </body>
            </html>
            """
        else:
            mail.HTMLBody = f"""
            <html>
            <body>
                <h2>Password Reset Confirmation</h2>
                <p>Dear User,</p>
                <p>Your password has been successfully reset. Please find your new login details below:</p>
                <table style="border: 1px solid black; border-collapse: collapse;">
                    <tr>
                        <td style="border: 1px solid black; padding: 8px;"><b>Username:</b></td>
                        <td style="border: 1px solid black; padding: 8px;">{to_address.split('@')[0]}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid black; padding: 8px;"><b>New Password:</b></td>
                        <td style="border: 1px solid black; padding: 8px;">{body}</td>
                    </tr>
                </table>
                <p><b>Important:</b> Please change this temporary password immediately after you login.</p>
                <p>If you encounter any issues, contact support.</p>
                <p>Best regards,<br>The Aspire Team</p>
            </body>
            </html>
            """
        mail.SentOnBehalfOfName = "pratik_bhongade@keybank.com"
        mail.Send()
        logging.info(f"Email sent to {to_address}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Load and initialize abend data
def load_and_initialize():
    global abend_data
    abend_data = load_abend_data('abend_data.xlsx')
    initialize_matcher(abend_data)
    logging.debug("Abend data loaded and matcher initialized.")

# Get suggestions using fuzzy matching
def get_suggestion(input_text, choices):
    suggestion = process.extractOne(input_text, choices)
    if suggestion[1] > 80:  # Set a threshold for close matches
        return suggestion[0]
    return None

# Get solution from entities
def get_solution_from_entities(user_input):
    entities = extract_entities(user_input, abend_data)
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
        elif abend_name:
            row = abend_data.loc[abend_data['AbendName'].str.contains(abend_name, case=False, na=False)]
            if not row.empty:
                abend_code = row['AbendCode'].values[0]
                solution = row['Solution'].values[0]
                response = f"**Abend Code:** {abend_code}\n\n**Solution:** {solution}"

    if response:
        logging.debug(f"Response: {response}")
        return jsonify({"solution": response})
    else:
        fallback_response = "I'm not sure about that. Can you please provide more details?"
        logging.debug("Fallback response.")
        return jsonify({"solution": fallback_response})

# Initial load and initialize
load_and_initialize()

@app.route('/get_solution', methods=['POST'])
def get_solution():
    global expecting_user_id, expecting_otp, user_id_for_reset, otp_store, suggested_term
    user_input = request.json.get('message').strip().lower()
    logging.debug(f"Received user input: {user_input}")

    # Handle Yes/No response to "Did you mean"
    if suggested_term:
        if user_input == "yes":
            response = get_solution_from_entities(suggested_term)
            suggested_term = None
            return response
        elif user_input == "no":
            suggested_term = None
            return jsonify({"solution": "Okay, please provide more details."})
        else:
            return jsonify({"solution": "Please respond with 'yes' or 'no'."})

    # Handle OTP verification
    if expecting_otp and user_id_for_reset:
        if user_input == otp_store.get(user_id_for_reset):
            random_password = generate_random_password()
            encrypted_password = generate_encrypted_password(random_password)
            user_email = f"{user_id_for_reset}@keybank.com"
            update_password(user_id_for_reset, encrypted_password)
            send_email(user_email, body=random_password, email_type="password_reset")
            otp_store.pop(user_id_for_reset)
            expecting_otp = False
            user_id_for_reset = None
            return jsonify({"solution": f"Password for User ID ***{user_id_for_reset}*** has been updated successfully. The new password has been sent to your email."})
        else:
            return jsonify({"solution": "Invalid OTP. Please try again."})

    if expecting_user_id:
        if check_user_id(user_input):
            otp = generate_otp()
            user_email = f"{user_input}@keybank.com"
            send_email(user_email, subject="Aspire Password Reset OTP", body=f"Your OTP is: {otp}", email_type="otp")
            otp_store[user_input] = otp
            expecting_user_id = False
            expecting_otp = True
            user_id_for_reset = user_input
            return jsonify({"solution": "An OTP has been sent to your email. Please enter it to reset your password."})
        else:
            return jsonify({"solution": f"User ID {user_input} not found."})

    # Check for small talk
    small_talk_response = match_small_talk(user_input)
    if small_talk_response:
        return jsonify({"solution": small_talk_response})

    # Check for password reset
    if match_password_reset(user_input):
        expecting_user_id = True
        return jsonify({"solution": "Please provide your Racf ID to reset your password."})

    # Handle normal chatbot flow for abend codes
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
            "thanks": "You're welcome! If you have more questions, feel free to ask.",
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
        elif not abend_code:
            suggestion = get_suggestion(user_input, abend_data['AbendCode'].tolist() + abend_data['AbendName'].tolist())
            if suggestion:
                suggested_term = suggestion
                return jsonify({"solution": f"Did you mean '{suggestion}'? Please respond with 'yes' or 'no'."})
    
    if response:
        return jsonify({"solution": response})
    else:
        fallback_response = "I'm not sure about that. Can you please provide more details?"
        return jsonify({"solution": fallback_response})

# Speech-to-text route
@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    try:
        recognized_text = recognize_speech()
        logging.debug(f"Recognized Text: {recognized_text}")
        if recognized_text:
            return jsonify({"recognized_text": recognized_text})
        else:
            logging.debug("No speech detected")
            return jsonify({"error": "No speech detected or unclear speech."})
    except Exception as e:
        logging.error(f"Speech recognition error: {e}")
        return jsonify({"error": "Error during speech recognition."})

if __name__ == '__main__':
    app.run(debug=True)
