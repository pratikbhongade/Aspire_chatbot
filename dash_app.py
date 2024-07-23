import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests
from app import app as flask_app

# External stylesheets for better styling
external_stylesheets = [dbc.themes.BOOTSTRAP]

# Initialize the Dash app with the Flask server
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=flask_app)

# Initial welcome message with bot avatar
initial_message = html.Div([
    html.Img(src='/static/images/bot.png', className='avatar'),
    dcc.Markdown("Bot: Hi, How can I help you today?")
], className='bot-message')

# Common issues
common_issues = [
    {"code": "S0C4", "name": "Storage Violation"},
    {"code": "S0C7", "name": "Data Exception"},
    {"code": "S322", "name": "Time Limit Exceeded"},
    {"code": "S806", "name": "Program Not Found"},
    {"code": "S013", "name": "Data Set Open Error"}
]

# Layout of the Dash app
app.layout = html.Div([
    html.Div([
        html.H2("Common Issues", style={'text-align': 'center', 'color': 'white'}),
        html.Ul([
            html.Li(f"{issue['code']}: {issue['name']}", className='abend-item', id={'type': 'abend-item', 'index': issue['code']}) 
            for issue in common_issues
        ], style={'list-style-type': 'none', 'padding': 0})
    ], className='sidebar'),

    html.Div([
        html.H1("Aspire ChatBot", style={'text-align': 'center', 'color': 'white', 'margin-top': '20px'}),
        html.Div([
            html.Div(id='chat-container', className='chat-container', children=[initial_message]),
            html.Div([
                dcc.Input(id='input-message', type='text', placeholder='Enter your abend issue...', style={'flex': '1', 'border-radius': '10px'}),
                html.Button([
                    html.I(className='fas fa-paper-plane'),
                    " Send"
                ], id='send-button', n_clicks=0, style={'border-radius': '10px'}),
                html.Button([
                    html.I(className='fas fa-sync-alt'),
                    " Refresh Data"
                ], id='refresh-data-button', n_clicks=0, style={'border-radius': '10px', 'marginLeft': '10px'}),
            ], className='input-container')
        ], className='message-box')
    ], className='main-container'),
    # Tooltips
    dbc.Tooltip("Click to send your message", target='send-button', placement='top'),
    dbc.Tooltip("Click to refresh data", target='refresh-data-button', placement='top')
], className='outer-container')

# Callback for sending messages
@app.callback(
    Output('chat-container', 'children'),
    [Input('send-button', 'n_clicks'), Input({'type': 'abend-item', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('input-message', 'value'), State('chat-container', 'children')]
)
def update_chat(n_clicks, issue_clicks, user_message, chat_history):
    if not n_clicks and not any(issue_clicks):
        raise dash.exceptions.PreventUpdate

    if n_clicks:
        if user_message:
            chat_history.append(html.Div([
                html.Img(src='/static/images/user.png', className='avatar'),
                dcc.Markdown(f"User: {user_message}")
            ], className='user-message'))
            response = requests.post('http://localhost:8080/get_solution', json={'message': user_message}).json()
            chat_history.append(html.Div([
                html.Img(src='/static/images/bot.png', className='avatar'),
                dcc.Markdown(f"Bot: {response['solution']}")
            ], className='bot-message'))
            return chat_history

    if any(issue_clicks):
        ctx = dash.callback_context
        issue_code = ctx.triggered[0]['prop_id'].split('.')[0].split('index')[1][2:-2]
        for issue in common_issues:
            if issue['code'] == issue_code:
                response = requests.post('http://localhost:8080/get_solution', json={'message': issue_code}).json()
                chat_history.append(html.Div([
                    html.Img(src='/static/images/user.png', className='avatar'),
                    dcc.Markdown(f"User: {issue_code}: {issue['name']}")
                ], className='user-message'))
                chat_history.append(html.Div([
                    html.Img(src='/static/images/bot.png', className='avatar'),
                    dcc.Markdown(f"Bot: {response['solution']}")
                ], className='bot-message'))
                return chat_history

    return chat_history

# Callback for refreshing data
@app.callback(
    Output('chat-container', 'children'),
    Input('refresh-data-button', 'n_clicks'),
    State('chat-container', 'children')
)
def refresh_data(n_clicks, chat_history):
    if n_clicks:
        response = requests.post('http://localhost:8080/refresh_data').json()
        chat_history.append(html.Div([
            html.Img(src='/static/images/bot.png', className='avatar'),
            dcc.Markdown(f"Bot: {response['status']}")
        ], className='bot-message'))
        return chat_history
    raise dash.exceptions.PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
