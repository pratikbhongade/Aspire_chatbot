import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests
import logging
import time

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)

# External stylesheets (Bootstrap for layout and Font Awesome for icons)
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
]

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Initial welcome message
initial_message = html.Div([
    html.Img(src='/assets/bot.png', className='avatar'),
    dcc.Markdown("Bot: Hi, How can I help you today?")
], className='bot-message')

# Common issues to display in the sidebar
common_issues = [
    {"code": "S0C4", "name": "Storage Violation"},
    {"code": "S0C7", "name": "Data Exception"},
    {"code": "S322", "name": "Time Limit Exceeded"}
]

# Layout of the Dash app
app.layout = html.Div([
    # Sidebar for common issues
    html.Div([
        html.H2("Common Issues", className='sidebar-h2'),
        html.Ul([
            html.Li(f"{issue['code']}: {issue['name']}", className='abend-item', id={'type': 'abend-item', 'index': issue['code']})
            for issue in common_issues
        ], className='common-issues-list')
    ], className='sidebar'),

    # Main container for chat
    html.Div([
        html.H1("Aspire ChatBot", style={'text-align': 'center', 'color': 'white'}),
        html.Div([
            html.Div(id='chat-container', className='chat-container', children=[initial_message]),
            html.Div([
                dcc.Input(id='input-message', type='text', placeholder='Enter your abend issue...', className='input-message', debounce=True),
                html.Button([
                    html.I(className='fas fa-paper-plane'),
                    " Send"
                ], id='send-button', n_clicks=0, className='send-button', style={'margin-right': '10px'}),
                html.Button([
                    html.I(className='fas fa-microphone'),  # Initial microphone icon
                    " Speak"
                ], id='speech-button', n_clicks=0, className='speech-button', style={'background-color': '#007bff', 'color': 'white', 'margin-right': '10px'}),
                html.Button("Refresh", id='refresh-button', n_clicks=0, className='refresh-button', style={'background-color': '#28a745', 'color': 'white'})
            ], className='input-container', style={'display': 'flex', 'gap': '10px'})  # Add space between buttons
        ], className='message-box')
    ], className='main-container'),

    # Interval component for polling speech recognition result
    dcc.Interval(id='speech-interval', interval=1000, n_intervals=0, disabled=True),  # Interval component (disabled initially)

    # Tooltips for common issues and buttons
    dbc.Tooltip("Click to send your message", target='send-button', placement='top'),
    dbc.Tooltip("Click to record your voice", target='speech-button', placement='top'),
    dbc.Tooltip("Click to refresh the conversation", target='refresh-button', placement='top'),  # Tooltip for refresh button
    *[
        dbc.Tooltip(f"Click to get solution for {issue['code']}", target={'type': 'abend-item', 'index': issue['code']}, placement='right')
        for issue in common_issues
    ]
], className='outer-container')


# Simulate a backend response for speech recognition (since we don't have live speech recognition here)
speech_recognition_result = {"recognized_text": None}

# Function to simulate speech recognition
def simulate_speech_recognition():
    global speech_recognition_result
    time.sleep(3)  # Simulate delay in speech recognition
    speech_recognition_result["recognized_text"] = "hello"  # Example recognized text


# Unified callback to handle UI updates, chat, and speech recognition
@app.callback(
    [Output('chat-container', 'children'),
     Output('input-message', 'value'),
     Output('speech-button', 'style'),
     Output('speech-button', 'children'),
     Output('speech-interval', 'disabled')],
    [Input('send-button', 'n_clicks'),
     Input('input-message', 'n_submit'),
     Input('speech-button', 'n_clicks'),
     Input('refresh-button', 'n_clicks'),
     Input({'type': 'abend-item', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input('speech-interval', 'n_intervals')],
    [State('input-message', 'value'), State('chat-container', 'children')]
)
def update_chat(send_clicks, enter_clicks, speech_clicks, refresh_clicks, abend_clicks, n_intervals, value, chat_children):
    global speech_recognition_result

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    logging.debug(f"Triggered ID: {triggered_id}")

    # Default style and icon for the speech button
    speech_button_style = {'background-color': '#007bff', 'color': 'white', 'margin-right': '10px'}
    speech_button_icon = [html.I(className='fas fa-microphone'), " Speak"]

    # Refresh the chat and reset password flow
    if triggered_id == 'refresh-button':
        logging.debug("Refresh button clicked. Resetting chatbot.")
        requests.post('http://127.0.0.1:5000/reset_password_flow')  # Call backend to reset password flow
        return [initial_message], '', speech_button_style, speech_button_icon, True  # Reset to initial message and clear input

    # Handle Speech Recognition: Button click starts speech recognition process
    if triggered_id == 'speech-button':
        logging.debug("Speech button clicked. Starting speech recognition.")

        # Change speech button color and icon when clicked
        speech_button_style = {'background-color': '#dc3545', 'color': 'white', 'margin-right': '10px'}
        speech_button_icon = [html.I(className='fas fa-record-vinyl'), " Listening..."]  # Change to recording icon

        # Simulate starting the speech recognition in the background
        simulate_speech_recognition()  # Simulate speech recognition process

        # Enable polling with Interval component to check when speech recognition completes
        return chat_children, value, speech_button_style, speech_button_icon, False  # Enable the Interval component

    # Polling for speech recognition results using Interval
    if triggered_id == 'speech-interval':
        logging.debug(f"Polling for speech recognition result: {speech_recognition_result}")
        
        if speech_recognition_result["recognized_text"]:  # Check if speech recognition is done
            recognized_text = speech_recognition_result["recognized_text"]

            # Reset the result after processing
            speech_recognition_result["recognized_text"] = None

            # Simulate the user entering the recognized text as if they typed it
            user_message = html.Div([
                html.Img(src='/assets/user.png', className='avatar'),
                html.Div(f"You: {recognized_text}")
            ], className='user-message')
            chat_children.append(user_message)

            # Send recognized text to backend for processing
            bot_response = requests.post('http://127.0.0.1:5000/get_solution', json={'message': recognized_text})
            bot_response_data = bot_response.json()

            bot_response_message = html.Div([
                html.Img(src='/assets/bot.png', className='avatar'),
                dcc.Markdown(f"Bot: {bot_response_data.get('solution')}")
            ], className='bot-message')
            chat_children.append(bot_response_message)

            # Reset button style and icon after speech is processed
            speech_button_style = {'background-color': '#007bff', 'color': 'white', 'margin-right': '10px'}
            speech_button_icon = [html.I(className='fas fa-microphone'), " Speak"]

            logging.debug("Speech recognition complete. Resetting button to default state.")

            # Disable polling (Interval component)
            return chat_children, '', speech_button_style, speech_button_icon, True  # Disable the Interval component

    # Handle message sending through typing or clicking Send
    if triggered_id in ['send-button', 'input-message']:
        if value:
            user_message = html.Div([
                html.Img(src='/assets/user.png', className='avatar'),
                html.Div(f"You: {value}")
            ], className='user-message')
            chat_children.append(user_message)
            response = requests.post('http://127.0.0.1:5000/get_solution', json={'message': value})
            bot_response_data = response.json()

            bot_response = html.Div([
                html.Img(src='/assets/bot.png', className='avatar'),
                dcc.Markdown(f"Bot: {bot_response_data.get('solution')}")
            ], className='bot-message')
            chat_children.append(bot_response)

            logging.debug(f"Chat updated with user input: {value}")

            return chat_children, '', speech_button_style, speech_button_icon, True  # Return updated chat history, clear input

    return chat_children, '', speech_button_style, speech_button_icon, True  # Disable Interval by default

# Main entry point for running the app
if __name__ == '__main__':
    app.run_server(debug=True)
