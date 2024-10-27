import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import pandas as pd
import numpy as np
import requests
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from keras.models import load_model
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error


# API CALLS TO WEATHER


def get_weather_data(latitude, longitude, start_date, end_date):
    latitude = str(latitude)
    longitude = str(longitude)
    response = requests.get("https://archive-api.open-meteo.com/v1/era5?latitude=" + latitude + "&longitude=" + longitude + "&start_date=" + start_date + "&end_date=" + end_date + "&hourly=precipitation")
    #print(response.status_code)
    if response.status_code == 200:
        data = response.json()
        times = data["hourly"]["time"]
        temperatures = data["hourly"]["precipitation"]
        time_temperature_tuple = []
        for i in range(0, len(times)):
            time_temperature_tuple.append((times[i], temperatures[i]))
        return time_temperature_tuple
    else:
        return "Nah"
    

stations = {
    "High Bridge": [40.667931, -74.895576],
    "Annandale": [40.640911, -74.881126],
    "Lebanon": [40.641781, -74.835358],
    "White House": [40.6155126, -74.7707356],
    "North Branch": [40.6020469, -74.6773823],
    "Raritan": [40.567181, -74.634683],
    "Somerville": [40.5742696, -74.60988],
    "Bridgewater": [40.5598127, -74.5517146],
    "Bound Brook": [40.5684363, -74.5384889],
    "Dunellen": [40.5892696, -74.4718201],
    "Plainfield": [40.6337136, -74.4073737],
    "Netherwood": [40.6290506, -74.4033895],
    "Fanwood": [40.6409555, -74.383846],
    "Westfield": [40.6589912, -74.3473717],
    "Garwood": [40.6517692, -74.3229264],
    "Cranford": [40.6584358, -74.2995923],
    "Roselle Park": [40.6645469, -74.2643133],
    "Union": [40.698967, -74.266861],
    "Newark Penn Station": [40.732598, -74.174796],
    "Secaucus Junction": [40.788513, -74.058787],
    "Penn Station New York": [40.750079, -73.991348]
}

data = pd.read_csv('2019_10.csv')
data = data.dropna()
data = data[data['type'] == 'NJ Transit']
data = data[data['line'] == 'Raritan Valley']
data = data.drop(columns=['train_id', 'from', 'from_id', 'to_id', 'line', 'date', 'stop_sequence', 'actual_time', 'type', 'status'])


limit = 100


locs = []
for loc in data['to'].head(limit):
    locs.append(loc)

dates = []
for time in data['scheduled_time'].head(limit):
    dates.append(time[:10])

hours = []
for time in data['scheduled_time'].head(limit):
    hours.append(time[11:13])


precipitations = []

for i in range(0, limit):
    loc = locs[i]
    if loc in stations:
        lat = stations[loc][0]
        lon = stations[loc][1]
        hour = int(hours[i])
        date = dates[i]
        #print("Getting weather data for " + loc + " on " + time)
        prec = get_weather_data(lat, lon, date, date)
        prec = prec[hour]
        prec = prec[1]
        precipitations.append(prec)
        #print(prec)

print(precipitations)

data = data.drop(columns=['to', 'scheduled_time'])

data = data.head(limit)

data['precipitation'] = precipitations



# TRAINING
df = pd.DataFrame(data)
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(df)
sequence_length = 5
X, y = [], []

for i in range(sequence_length, len(data_scaled)):
    X.append(data_scaled[i-sequence_length:i])  
    y.append(data_scaled[i, 0])  

X, y = np.array(X), np.array(y)
train_size = int(0.8 * len(X))
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]
model = Sequential()
model.add(LSTM(50, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(Dense(1)) 
model.compile(optimizer='adam', loss='mse')
early_stopping = EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=100,
    batch_size=32,
    callbacks=[early_stopping],
    verbose=1
)

y_pred = model.predict(X_test)
y_test_rescaled = scaler.inverse_transform(np.concatenate([y_test.reshape(-1, 1), np.zeros((y_test.shape[0], 1))], axis=1))[:, 0]
y_pred_rescaled = scaler.inverse_transform(np.concatenate([y_pred, np.zeros((y_pred.shape[0], 1))], axis=1))[:, 0]
mse = mean_squared_error(y_test_rescaled, y_pred_rescaled)
print("Mean Squared Error on Test Data:", mse)

model.save('model.keras')




app = Flask(__name__)

CORS(app)

@app.route('/', methods = ['GET'])
def index():
    return jsonify({'message': 'hello'})

@app.route('/apiModel', methods = ['POST'])
def index2():
    return 'this is post'


@app.route('/apiModel/get', methods = ['POST', 'GET'])

def predict():

    if request.method == 'POST':
        p = request.args.get('prec', type = float)
    
        loadedModel = keras.models.load_model('model.keras')

        new_precipitation_data = [p]

        new_precipitation_scaled = scaler.transform(np.column_stack((np.zeros(len(new_precipitation_data)), new_precipitation_data)))
        new_input_sequences = []
        last_sequence = data_scaled[-sequence_length:].reshape((1, sequence_length, data_scaled.shape[1]))

        for precip in new_precipitation_scaled:
            next_sequence = np.append(last_sequence[:, 1:, :], precip.reshape(1, 1, -1), axis=1)
            new_input_sequences.append(next_sequence)

        new_input_sequences = np.array(new_input_sequences)
        new_input_sequences = new_input_sequences.reshape((1, 5, 2))  
        print("New input sequences shape:", new_input_sequences.shape)  
        new_predictions = loadedModel.predict(new_input_sequences)
        new_predictions_rescaled = scaler.inverse_transform(np.concatenate([new_predictions, np.zeros((new_predictions.shape[0], 1))], axis=1))[:, 0]

        for precip, pred in zip(new_precipitation_data, new_predictions_rescaled):
            #print(f"Precipitation: {precip}, Predicted Delay: {pred}")
            return jsonify({'precipitation': precip, 'predicted_delay': pred})
    else:
        
        return 'Bruh'

    


if __name__ == '__main__':
    print('Server is running')
    app.run(debug=True)