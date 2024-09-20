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

# Initialize the Dash app with callback exception suppression
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

# Initial welcome message
initial_message = html.Div([
    html.Img(src='/assets/bot.png', className='avatar'),
    dcc.Markdown("Bot: Hi, How can I help you today?")
], className='bot-message')

# Layout of the Dash app
app.layout = html.Div([
    # Main container for chat
    html.Div([
        html.H1("Aspire ChatBot", style={'text-align': 'center', 'color': 'white'}),
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
            html.Button("Refresh", id='reset-button', n_clicks=0, className='reset-button'),
        ], className='input-container', style={'display': 'flex', 'align-items': 'center'}),
        html.Div(id='quick-reply-buttons', className='quick-reply-container')  # Container for dynamic quick reply buttons
    ], className='main-container'),
])

# Callback to update the chat and handle quick reply buttons
@app.callback(
    [Output('chat-container', 'children'),
     Output('input-message', 'value'),
     Output('quick-reply-buttons', 'children')],
    [Input('send-button', 'n_clicks'),
     Input('input-message', 'n_submit'),
     Input('speech-button', 'n_clicks'),
     Input('reset-button', 'n_clicks'),
     Input({'type': 'quick-reply-button', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('input-message', 'value'), State('chat-container', 'children')]
)
def update_chat(send_clicks, enter_clicks, speech_clicks, reset_clicks, quick_reply_clicks, value, chat_children):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Refresh the chat when refresh button is clicked
    if triggered_id == 'reset-button':
        # Reset chat and input field
        return [initial_message], '', None

    if triggered_id.startswith('quick-reply-button'):
        # Handle quick reply buttons
        button_value = triggered_id.split('"')[3]
        user_message = html.Div([
            html.Img(src='/assets/user.png', className='avatar'),
            html.Div(f"You: {button_value}")
        ], className='user-message')
        chat_children.append(user_message)

        # Send button value as a response to the bot
        bot_response = requests.post('http://127.0.0.1:5000/get_solution', json={'message': button_value})
        bot_response_data = bot_response.json()

        bot_response_message = html.Div([
            html.Img(src='/assets/bot.png', className='avatar'),
            dcc.Markdown(f"Bot: {bot_response_data.get('solution')}")
        ], className='bot-message')
        chat_children.append(bot_response_message)

        return chat_children, '', None  # Clear quick reply buttons after clicking

    if triggered_id in ['send-button', 'input-message']:
        if value:
            user_message = html.Div([
                html.Img(src='/assets/user.png', className='avatar'),
                html.Div(f"You: {value}")
            ], className='user-message')
            chat_children.append(user_message)

            # Send message to backend
            response = requests.post('http://127.0.0.1:5000/get_solution', json={'message': value})
            bot_response_data = response.json()

            bot_response_message = html.Div([
                html.Img(src='/assets/bot.png', className='avatar'),
                dcc.Markdown(f"Bot: {bot_response_data.get('solution')}")
            ], className='bot-message')
            chat_children.append(bot_response_message)

            # Example: Trigger quick reply buttons for Yes/No questions
            if 'yes/no' in bot_response_data.get('solution', '').lower():
                quick_reply_buttons = html.Div([
                    html.Button("Yes", id={'type': 'quick-reply-button', 'index': 'Yes'}, className='quick-reply-btn'),
                    html.Button("No", id={'type': 'quick-reply-button', 'index': 'No'}, className='quick-reply-btn'),
                ], className='quick-reply-buttons')

                return chat_children, '', quick_reply_buttons

            return chat_children, '', None  # Clear input and quick reply buttons

    return chat_children, '', None  # Default return with no quick reply buttons

# Main entry point for running the app
if __name__ == '__main__':
    app.run_server(debug=True)
