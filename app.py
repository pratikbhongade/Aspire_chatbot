import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests

external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Initial welcome message with bot avatar
initial_message = html.Div([
    html.Img(src='/assets/bot.png', className='avatar'),
    dcc.Markdown("Bot: Hi, How can I help you today?")
], className='bot-message')

# Common issues
common_issues = [
    {"code": "S0C4", "name": "Storage Violation"},
    {"code": "S0C7", "name": "Data Exception"},
    {"code": "S322", "name": "Time Limit Exceeded"}
]

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
    dbc.Tooltip("Click to refresh the data", target='refresh-data-button', placement='top'),
    # Adding tooltips for each common issue
    *[
        dbc.Tooltip(f"Click to get solution for {issue['code']}", target={'type': 'abend-item', 'index': issue['code']}, placement='right') 
        for issue in common_issues
    ]
], className='outer-container')

@app.callback(
    [Output('chat-container', 'children'),
     Output('input-message', 'value')],
    [Input('send-button', 'n_clicks'), 
     Input('input-message', 'n_submit'), 
     Input('refresh-data-button', 'n_clicks'),
     Input({'type': 'abend-item', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('input-message', 'value'), State('chat-container', 'children')]
)
def update_chat(send_clicks, n_submit, refresh_clicks, abend_clicks, value, chat_children):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'send-button' or triggered_id == 'input-message':
        if value:
            user_message = html.Div([
                html.Img(src='/assets/user.png', className='avatar'),
                html.Div(f"You: {value}")
            ], className='user-message')
            chat_children.append(user_message)
            response = requests.post('http://127.0.0.1:5000/get_solution', json={'message': value})
            bot_response = html.Div([
                html.Img(src='/assets/bot.png', className='avatar'),
                dcc.Markdown(f"Bot: {response.json().get('solution')}")
            ], className='bot-message')
            chat_children.append(bot_response)
            return chat_children, ''

    elif triggered_id == 'refresh-data-button':
        response = requests.post('http://127.0.0.1:5000/refresh_data')
        refresh_message = html.Div([
            html.Img(src='/assets/bot.png', className='avatar'),
            dcc.Markdown(f"Bot: {response.json().get('status')}")
        ], className='bot-message')
        chat_children.append(refresh_message)
        return chat_children, ''

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
        return chat_children, ''

    return chat_children, ''

if __name__ == '__main__':
    app.run_server(debug=True)
