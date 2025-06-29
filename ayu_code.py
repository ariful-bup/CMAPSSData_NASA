# -*- coding: utf-8 -*-
"""ARIF_CODE.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1yUF85NwQW4wTFgJZS4yUe064k-zrLsT0
"""

from google.colab import drive
drive.mount('/content/drive')

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# import os.chdir()

# Define column names (engine ID, cycle, operational settings, sensor readings)
col_names = ['engine_id', 'cycle', 'setting1', 'setting2', 'setting3'] + [f'sensor_{i}' for i in range(1, 22)]

# Load dataset
file_path = '/content/drive/MyDrive/CMaps/train_FD001.txt'
data = pd.read_csv(file_path, sep='\s+', header=None, names=col_names)

max_cycle = data.groupby('engine_id')['cycle'].max().reset_index()
max_cycle.columns = ['engine_id', 'max_cycle']
data = pd.merge(data, max_cycle, on='engine_id')
data['RUL'] = data['max_cycle'] - data['cycle']
data.drop(columns=['max_cycle'], inplace=True)

col_names

# Select feature columns and target variable
feature_cols = col_names[2:]  # Exclude engine_id and cycle
scaler = MinMaxScaler()
data[feature_cols] = scaler.fit_transform(data[feature_cols])  # Normalize features

# """
  # Converts time series data into sequences for LSTM.
  # Example:
  # If window_size=3 and the data is [1,2,3,4,5], the sequences and targets will be:
  # Input Sequences:  [[1,2,3], [2,3,4], [3,4,5]]
  # Targets:           [4, 5, 6]
  # """
def create_sequences(df, window_size, feature_cols):

    sequences = []
    labels = []
    data_array = df[feature_cols].values
    target_array = df['RUL'].values

    for i in range(len(df) - window_size + 1):
        sequences.append(data_array[i:i+window_size])
        labels.append(target_array[i+window_size-1])  # RUL at last time step

    return np.array(sequences), np.array(labels)

# Create sequences grouped by engine

def create_sequences_by_engine(data, window_size, feature_cols):
    seq_list, label_list = [], []
    for engine in data['engine_id'].unique():
        df_engine = data[data['engine_id'] == engine]
        if len(df_engine) >= window_size:
            seq, lab = create_sequences(df_engine, window_size, feature_cols)
            seq_list.append(seq)
            label_list.append(lab)
    return np.concatenate(seq_list), np.concatenate(label_list)

# Define window size for LSTM input
window_size = 30
X_seq, y_seq = create_sequences_by_engine(data, window_size, feature_cols)

# Split data into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(X_seq, y_seq, test_size=0.2, random_state=42)

# Define LSTM model
UNITS = 128
DROPOUT_RATE = 0.2
LEARNING_RATE = 0.001

model = Sequential()
model.add(LSTM(units=UNITS, activation='tanh', input_shape=(window_size, len(feature_cols))))
model.add(Dropout(rate=DROPOUT_RATE))
model.add(Dense(1))  # Output layer (predicting RUL)

model.summary()

# Define a well-balanced LSTM model
model = Sequential()

# First LSTM layer with balanced neurons
model.add(LSTM(units=128, activation='tanh', return_sequences=True, input_shape=(window_size, len(feature_cols))))
model.add(Dropout(rate=0.3))  # Higher dropout to prevent early overfitting

# Second LSTM layer with gradual reduction in neurons
model.add(LSTM(units=128, activation='tanh', return_sequences=True))
model.add(Dropout(rate=0.2))

# Third LSTM layer (final)
model.add(LSTM(units=64, activation='tanh'))
model.add(Dropout(rate=0.2))

# Output layer (predicting RUL)
model.add(Dense(1))

#

model.summary()

# Compile model
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE), loss='mse')

# Train model
epochs = 20
batch_size = 32
model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_val, y_val))

# Evaluate model
loss = model.evaluate(X_val, y_val)
print(f"Validation Loss (MSE): {loss}")

# Make predictions
y_pred = model.predict(X_val)

y_pred

from sklearn.metrics import mean_absolute_error, mean_squared_error
# Compute metrics
mae_score = mean_absolute_error(y_val, y_pred)
mse_score = mean_squared_error(y_val, y_pred)
print(f"Final MAE: {mae_score}")
print(f"Final MSE: {mse_score}")

