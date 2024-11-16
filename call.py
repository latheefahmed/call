from flask import Flask, jsonify, send_from_directory, abort
import pandas as pd
from twilio.rest import Client
import os

app = Flask(__name__)

# Twilio configuration
account_sid = 'ACa79ed342809147dfff710c535b55f514'
auth_token = '71214d1d089a070591d019b6044e2d5c'
twilio_phone_number = '+12258004560'
twilio_bin_url = 'https://handler.twilio.com/twiml/EHfbb44bc41bc956a69884bc2eca44db1c'
client = Client(account_sid, auth_token)

# Load dataset
data_path = 'Statement8_Dataset.csv'
if os.path.exists(data_path):
    data = pd.read_csv(data_path)
else:
    print(f"CSV file not found at {data_path}. Please check the file path.")
    data = None

@app.route('/')
def index():
    """
    Serve the index.html file.
    """
    file_path = os.path.join(os.getcwd(), 'index.html')
    if os.path.exists(file_path):
        return send_from_directory(os.getcwd(), 'index.html')
    else:
        abort(404, description="Index file not found.")

@app.route('/send-calls', methods=['POST'])
def send_calls():
    """
    Notify and call for entries with missing fields.
    """
    if data is None:
        return jsonify(["Data not loaded. Check the CSV path."])

    results = []

    # Iterate through the dataset row by row
    for _, row in data.iterrows():
        ration_card_number = row['RationCardNumber']
        member_name = row['MemberName']
        phone_number = row['PhoneNumber']

        # Check for missing fields
        missing_fields = row[row.isnull() | (row == 'nil')].index.tolist()

        if missing_fields:
            # Log the missing field details
            results.append(f"Missing fields for {member_name} ({ration_card_number}): {', '.join(missing_fields)}")

            # Find a valid phone number for the same RationCardNumber
            valid_number_row = data[
                (data['RationCardNumber'] == ration_card_number) &
                (data['PhoneNumber'].notnull()) &
                (data['PhoneNumber'] != 'nil')
            ]

            if not valid_number_row.empty:
                valid_phone_number = valid_number_row.iloc[0]['PhoneNumber']

                try:
                    # Make a call using Twilio
                    call = client.calls.create(
                        to=valid_phone_number,
                        from_=twilio_phone_number,
                        url=twilio_bin_url
                    )
                    results.append(f"Call initiated to {member_name} ({valid_phone_number}). Call SID: {call.sid}")
                except Exception as e:
                    results.append(f"Failed to call {member_name} ({valid_phone_number}): {str(e)}")
            else:
                # No valid number found for the RationCardNumber
                results.append(f"No valid phone number found for {ration_card_number}. Skipping call.")
        else:
            results.append(f"No missing fields for {member_name}. No action needed.")

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
