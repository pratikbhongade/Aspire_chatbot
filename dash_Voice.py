import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests

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
                    html.I(className='fas fa-microphone'),
                    " Speak"
                ], id='speech-button', n_clicks=0, className='speech-button', style={'background-color': '#007bff', 'color': 'white', 'margin-right': '10px'}),
                html.Button("Refresh", id='refresh-button', n_clicks=0, className='refresh-button', style={'background-color': '#28a745', 'color': 'white'})
            ], className='input-container', style={'display': 'flex', 'gap': '10px'})  # Add space between buttons
        ], className='message-box')
    ], className='main-container'),

    # Tooltips for common issues and buttons
    dbc.Tooltip("Click to send your message", target='send-button', placement='top'),
    dbc.Tooltip("Click to record your voice", target='speech-button', placement='top'),
    dbc.Tooltip("Click to refresh the conversation", target='refresh-button', placement='top'),  # Tooltip for refresh button
    *[
        dbc.Tooltip(f"Click to get solution for {issue['code']}", target={'type': 'abend-item', 'index': issue['code']}, placement='right')
        for issue in common_issues
    ]
], className='outer-container')

# Callback to update the chat based on user input, speech-to-text, or refresh button click
@app.callback(
    [Output('chat-container', 'children'),
     Output('input-message', 'value'),
     Output('speech-button', 'style')],
    [Input('send-button', 'n_clicks'),
     Input('input-message', 'n_submit'),
     Input('speech-button', 'n_clicks'),
     Input('refresh-button', 'n_clicks'),  # Updated refresh button
     Input({'type': 'abend-item', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('input-message', 'value'), State('chat-container', 'children')]
)
def update_chat(send_clicks, enter_clicks, speech_clicks, refresh_clicks, abend_clicks, value, chat_children):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Default style for speech button
    default_speech_button_style = {'background-color': '#007bff', 'color': 'white', 'margin-right': '10px'}
    active_speech_button_style = {'background-color': '#dc3545', 'color': 'white', 'margin-right': '10px'}

    # Refresh the chat and reset password flow
    if triggered_id == 'refresh-button':
        requests.post('http://127.0.0.1:5000/reset_password_flow')  # Call backend to reset password flow
        return [initial_message], '', default_speech_button_style  # Reset to initial message and clear input

    if triggered_id == 'speech-button':
        # Change speech button color when microphone gets active
        speech_button_style = active_speech_button_style

        # Call backend for speech-to-text conversion
        response = requests.post('http://127.0.0.1:5000/speech_to_text')
        speech_data = response.json()

        print(f"Speech-to-text response: {speech_data}")

        if "recognized_text" in speech_data:
            recognized_text = speech_data['recognized_text']

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

            # Restore original color after speech recognition completes
            return chat_children, '', default_speech_button_style

        else:
            chat_children.append(html.Div([
                html.Img(src='/assets/bot.png', className='avatar'),
                dcc.Markdown("Bot: Sorry, I couldn't detect any speech. Please try again.")
            ], className='bot-message'))

            # Restore original color if no speech is detected
            return chat_children, '', default_speech_button_style

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

            return chat_children, '', default_speech_button_style  # Return updated chat history, clear input

    elif 'index' in triggered_id:
        abend_code = triggered_id.split('"')[3]
        value = abend_code
        user_message = html.Div([
            html.Img(src='/assets/user.png', className='avatar'),
            html.Div(f"You selected: {value}")
        ], className='user-message')
        chat_children.append(user_message)
        response = requests.post('http://127.0.0.1:5000/get_solution', json={'message': value})
        bot_response = html.Div([
            html.Img(src='/assets/bot.png', className='avatar'),
            dcc.Markdown(f"Bot: {response.json().get('solution')}")
        ], className='bot-message')
        chat_children.append(bot_response)
        return chat_children, '', default_speech_button_style

    return chat_children, '', default_speech_button_style

# Main entry point for running the app
if __name__ == '__main__':
    app.run_server(debug=True)
