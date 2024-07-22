from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load Excel data
def load_data():
    return pd.read_excel('abend_data.xlsx')

data = load_data()

@app.route('/get_solution', methods=['POST'])
def get_solution():
    message = request.json.get('message').strip().upper()
    print(f"Received message: {message}")  # Debug log
    if message in data['Abend Code'].values:
        row = data[data['Abend Code'] == message].iloc[0]
    elif message in data['Abend Name'].str.upper().values:
        row = data[data['Abend Name'].str.upper() == message].iloc[0]
    else:
        return jsonify({'solution': 'No solution found for the provided abend code or name.'})
    solution = f"Abend Name: {row['Abend Name']}<br>Solution: {row['Solution']}"
    print(f"Returning solution: {solution}")  # Debug log
    return jsonify({'solution': solution})

@app.route('/refresh_data', methods=['POST'])
def refresh_data():
    global data
    data = load_data()
    return jsonify({'status': 'Data refreshed successfully.'})

if __name__ == '__main__':
    app.run(debug=True)
