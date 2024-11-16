from flask import Flask, request, jsonify, send_from_directory, abort, Response
import pandas as pd
from twilio.rest import Client
import os

app = Flask(__name__)

# Twilio configuration
account_sid = 'AC3f6ca30a540291e85b37197fc265d511'
auth_token = 'd3e3e6212bf69c11a2fc48c693daa6c3'
twilio_phone_number = '+12512202112'
client = Client(account_sid, auth_token)

# Twilio Bin URL
twilio_bin_url = 'https://handler.twilio.com/twiml/EH331b110fb7c872147663d7532f9dc068'

# Load data
data_path = 'Statement8_Dataset.csv'
if os.path.exists(data_path):
    data = pd.read_csv(data_path)
else:
    print(f"CSV file not found at {data_path}. Please check the file path.")

@app.route('/')
def index():
    file_path = os.path.join(os.getcwd(), 'index.html')
    if os.path.exists(file_path):
        return send_from_directory(os.getcwd(), 'index.html')
    else:
        abort(404, description="Index file not found.")

@app.route('/send-calls', methods=['POST'])
def send_calls_to_male_heads():
    if data is None:
        return jsonify(["Data not loaded. Check CSV path."])

    results = []
    grouped_data = data.groupby('RationCardNumber')

    for ration_card_number, group in grouped_data:
        cardholder_row = group[group['RelationToCardHolder'] == 'Self']

        if not cardholder_row.empty:
            cardholder_gender = cardholder_row['Gender'].values[0].strip().lower()
            number_of_family_members = cardholder_row['NumberOfFamilyMembers'].values[0]
            phone_number = cardholder_row['PhoneNumber'].values[0]
            head_name = cardholder_row['MemberName'].values[0]

            if cardholder_gender == 'male' and number_of_family_members > 1:
                has_spouse = not group[(group['RelationToCardHolder'] == 'Spouse') & 
                                       (group['Gender'].str.lower() == 'female')].empty

                if has_spouse:
                    try:
                        # Initiate the call with Twilio Bin URL for the custom message
                        call = client.calls.create(
                            to=phone_number,
                            from_=twilio_phone_number,
                            url=twilio_bin_url
                        )
                        results.append(f"Call initiated to {head_name} at {phone_number}")
                    except Exception as e:
                        results.append(f"Failed to call {head_name} at {phone_number}: {str(e)}")
                else:
                    results.append(f"No call made to {head_name} (no spouse available).")
            elif cardholder_gender == 'male' and number_of_family_members == 1:
                results.append(f"No call made to {head_name} (only 1 family member).")
            else:
                results.append(f"No action needed for {head_name} (Already updated).")

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
