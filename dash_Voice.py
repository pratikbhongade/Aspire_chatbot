import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests
import time

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

# Common issues to display in the sidebar, including "Password Reset"
common_issues = [
    {"code": "S0C4", "name": "Storage Violation"},
    {"code": "S0C7", "name": "Data Exception"},
    {"code": "S322", "name": "Time Limit Exceeded"},
    {"code": "Password Reset", "name": "Reset Password"}  # Added Password Reset
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
                dcc.Input(id='input-message', type='text', placeholder='Message Aspire', className='input-message', debounce=True),
                html.Button([
                    html.I(className='fas fa-paper-plane'),
                    " Send"
                ], id='send-button', n_clicks=0, className='send-button', style={'margin-right': '10px'}),
                html.Button([
                    html.I(className='fas fa-microphone'),
                    " Speak"
                ], id='speech-button', n_clicks=0, className='speech-button', style={'margin-right': '10px'}),
                html.Button("Refresh", id='reset-button', n_clicks=0, className='reset-button')
            ], className='input-container', style={'display': 'flex', 'align-items': 'center'})
        ], className='message-box')
    ], className='main-container'),

    dcc.Interval(id='typing-interval', interval=2000, n_intervals=0, max_intervals=1, disabled=True),  # Interval for typing simulation

    # Tooltips for common issues and buttons
    dbc.Tooltip("Click to send your message", target='send-button', placement='top'),
    dbc.Tooltip("Click to record your voice", target='speech-button', placement='top'),
    dbc.Tooltip("Click to refresh the conversation", target='reset-button', placement='top'),
    *[
        dbc.Tooltip(f"Click to get solution for {issue['code']}", target={'type': 'abend-item', 'index': issue['code']}, placement='right')
        for issue in common_issues
    ]
], className='outer-container')

# Single callback to update chat and handle typing indicator
@app.callback(
    Output('chat-container', 'children'),
    [Input('send-button', 'n_clicks'),
     Input('input-message', 'n_submit'),
     Input('speech-button', 'n_clicks'),
     Input('reset-button', 'n_clicks'),
     Input('typing-interval', 'n_intervals'),
     Input({'type': 'abend-item', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('input-message', 'value'), State('chat-container', 'children')]
)
def update_chat(send_clicks, enter_clicks, speech_clicks, reset_clicks, typing_intervals, abend_clicks, value, chat_children):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Reset button clicked: reset the chat
    if triggered_id == 'reset-button':
        requests.post('http://127.0.0.1:5000/reset_password_flow')  # Call backend to reset password flow
        return [initial_message]  # Reset to initial message and clear input

    # Speech button clicked
    if triggered_id == 'speech-button':
        response = requests.post('http://127.0.0.1:5000/speech_to_text')
        speech_data = response.json()

        if "recognized_text" in speech_data:
            recognized_text = speech_data['recognized_text']
            user_message = html.Div([
                html.Img(src='/assets/user.png', className='avatar'),
                html.Div(f"You: {recognized_text}")
            ], className='user-message')
            chat_children.append(user_message)

            bot_typing_message = html.Div([
                html.Img(src='/assets/bot.png', className='avatar'),
                dcc.Markdown(f"Bot: ...")
            ], className='bot-message typing-indicator')
            chat_children.append(bot_typing_message)

            return chat_children  # No input value update

    # Handle common issues or user input
    if triggered_id in ['send-button', 'input-message'] or 'index' in triggered_id:
        if value or 'index' in triggered_id:
            if 'index' in triggered_id:
                abend_code = triggered_id.split('"')[3]
                if abend_code == "Password Reset":
                    value = "password reset"
                else:
                    value = abend_code

            user_message = html.Div([
                html.Img(src='/assets/user.png', className='avatar'),
                html.Div(f"You: {value}")
            ], className='user-message')
            chat_children.append(user_message)

            # Show typing indicator and wait 2 seconds
            bot_typing_message = html.Div([
                html.Img(src='/assets/bot.png', className='avatar'),
                dcc.Markdown(f"Bot: ...")
            ], className='bot-message typing-indicator')  # Bot typing indicator
            chat_children.append(bot_typing_message)

            # Simulate delay for bot response
            if typing_intervals == 0:
                return chat_children  # Return chat children without bot response
            else:
                # Remove typing indicator and show response
                chat_children = chat_children[:-1]

                # Get bot response from backend
                response = requests.post('http://127.0.0.1:5000/get_solution', json={'message': value})
                bot_response_data = response.json()

                bot_response_message = html.Div([
                    html.Img(src='/assets/bot.png', className='avatar'),
                    dcc.Markdown(f"Bot: {bot_response_data.get('solution')}")
                ], className='bot-message')
                chat_children.append(bot_response_message)

                return chat_children

    return chat_children

# Main entry point for running the app
if __name__ == '__main__':
    app.run_server(debug=True)
