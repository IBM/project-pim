from flask import Flask, request, jsonify
import joblib
import logging
import math
import numpy as np
import pandas as pd
import tensorflow as tf
import time

app = Flask(__name__)

seq_length = 7 # Six past transactions followed by current transaction
batch_size = 1

model = tf.keras.models.load_model("/opt/models/model.h5")


def timeEncoder(X):
    X_hm = X['Time'].str.split(':', expand=True)
    d = pd.to_datetime(dict(year=X['Year'],month=X['Month'],day=X['Day'],hour=X_hm[0],minute=X_hm[1])).astype(int)
    return pd.DataFrame(d)

def amtEncoder(X):
    amt = X.apply(lambda x: x[1:]).astype(float).map(lambda amt: max(1,amt)).map(math.log)
    return pd.DataFrame(amt)

def decimalEncoder(X,length=5):
    dnew = pd.DataFrame()
    for i in range(length):
        dnew[i] = np.mod(X,10)
        X = np.floor_divide(X,10)
    return dnew

def fraudEncoder(X):
    return np.where(X == 'Yes', 1, 0).astype(int)

def gen_predict_batch(tdf, mapper):
    new_df = mapper.transform(tdf).drop(['Is Fraud?'],axis=1)
    xbatch = new_df.to_numpy().reshape(batch_size, seq_length, -1)
    xbatch_t = np.transpose(xbatch, axes=(1,0,2))
    return xbatch_t

def predict_user_card_combination(tdf, mapper, model, user, card):
    batch_predictions = []
    # Loop to collect the rows for the specified user-card combination in batches of 7
    for i in range(0, len(tdf), seq_length):
        batch_data = tdf.iloc[i:i+seq_length]  # Get a batch of 7 user-card combinations
        xbatch_t = np.asarray(gen_predict_batch(batch_data, mapper))

        # Make predictions for this batch
        predictions = model.predict(xbatch_t)

        # get the result for the current transaction
        result = float(predictions[seq_length - 1][0][0])
        batch_predictions.append(result)

    logging.info("Number of predictions for 7 transaction sequences: ", len(batch_predictions))
    return batch_predictions

def process_db2_to_pandas(listDicts):
    tdf = pd.DataFrame(listDicts)
    tdf['merchant_name'] = tdf['merchant_name'].astype(str)
    tdf["merchant_city"].replace('ONLINE', ' ONLINE', regex=True, inplace=True)
    tdf["merchant_state"].fillna(np.nan, inplace=True)
    tdf['zip_code'].fillna(np.nan, inplace=True)
    tdf['is_errors'].fillna('missing_value', inplace=True)
    tdf.sort_values(by=['user_id','card'], inplace=True)
    tdf.reset_index(inplace=True, drop=True)

    tdf.rename(columns={"user_id": "User",
                        "card": "Card",
                        "year": "Year",
                        "month": "Month",
                        "day": "Day",
                        "time": "Time",
                        "amount": "Amount",
                        "use_chip": "Use Chip",
                        "merchant_name": "Merchant Name",
                        "merchant_city": "Merchant City",
                        "merchant_state": "Merchant State",
                        "zip_code": "Zip",
                        "mcc": "MCC",
                        "is_errors": "Errors?",
                        "is_fraud": "Is Fraud?"}, inplace=True)
    return tdf

def add_row_to_dataframe(dataframe, user, card, year, month, day, time, amount, use_chip, merchant_name, merchant_city, merchant_state, zip_code, mcc):
    new_row = {
        'User': user,
        'Card': card,
        'Year': year,
        'Month': month,
        'Day': day,
        'Time': time,
        'Amount': amount,
        'Use Chip': use_chip,
        'Merchant Name': merchant_name,
        'Merchant City': merchant_city,
        'Merchant State': merchant_state,
        'Zip': zip_code,
        'MCC': mcc
    }

    dataframe = pd.concat([dataframe, pd.DataFrame([new_row])], ignore_index=True)
    return dataframe

mapper = joblib.load(open("/opt/models/fitted_mapper.pkl", 'rb'))

# Define the Flask endpoint
@app.route('/predict', methods=['POST'])
def predict_fraud():
    # Get 7 transactions (current + 6 previous) from IBMi side
    data = request.get_json()
    current_transaction = data.get('current_transaction')
    previous_transactions = data.get('previous_transactions')
    
    logging.info(f"current transaction: {current_transaction}")
    logging.info(f"previous transaction: {previous_transactions}")

    user_id = int(current_transaction.get('user_id'))
    card = int(current_transaction.get('card'))
    year = int(current_transaction.get('year'))
    month = int(current_transaction.get('month'))
    day = int(current_transaction.get('day'))
    time_t = current_transaction.get('time')
    amount = current_transaction.get('amount')
    use_chip = current_transaction.get('use_chip')
    merchant_name = current_transaction.get('merchant_name')
    merchant_city = current_transaction.get('merchant_city')
    merchant_state = current_transaction.get('merchant_state')
    zip_code = float(current_transaction.get('zip_code'))
    mcc = int(current_transaction.get('mcc'))
    
    # Create dataframe with the 7 transactions
    tdf = process_db2_to_pandas(previous_transactions)
    tdf = add_row_to_dataframe(tdf, user_id, card, year, month, day, time_t,
                               amount, use_chip, merchant_name, merchant_city,
                               merchant_state, zip_code, mcc)
    
    # Prediction function call
    start_time = time.time()
    prediction_result = predict_user_card_combination(tdf, mapper, model, user_id, card)
    end_time = time.time()
    logging.info(f"Predictions for User {user_id} and Card {card}: {prediction_result}")
    logging.info("Inference Time:", end_time - start_time)

    # Determine if the current transaction is fraud
    if float(prediction_result[0]) > 0.5:
        is_fraud = 'Yes'
    else:
        is_fraud = 'No'
    
    return jsonify({'fraud_prediction': is_fraud})
    
@app.route('/ok', methods=['GET'])
def check_fraud_prediction_app():
    return jsonify({'fraud_prediction': 'ok'})    

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0", threaded=True)
