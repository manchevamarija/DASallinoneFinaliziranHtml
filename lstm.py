import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout


def load_data(symbol="BTC-USD", start="2020-01-01", end="2025-12-01"):
    df = yf.download(symbol, start=start, end=end)
    df = df[["Close"]]
    df.dropna(inplace=True)
    return df


def prepare_data(df, lookback=30):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(df)

    X, y = [], []
    for i in range(lookback, len(scaled)):
        X.append(scaled[i-lookback:i, 0])
        y.append(scaled[i, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))  # [samples, timesteps, features]

    split = int(len(X) * 0.7)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    return X_train, y_train, X_test, y_test, scaler


def build_lstm_model(input_shape):
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model


def train_and_predict(symbol="BTC-USD", lookback=30, epochs=20, batch_size=32):
    df = load_data(symbol)
    X_train, y_train, X_test, y_test, scaler = prepare_data(df, lookback)

    model = build_lstm_model((X_train.shape[1], 1))
    history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epochs, batch_size=batch_size, verbose=1)

    preds = model.predict(X_test)
    preds_rescaled = scaler.inverse_transform(preds.reshape(-1, 1))
    y_test_rescaled = scaler.inverse_transform(y_test.reshape(-1, 1))

    rmse = np.sqrt(mean_squared_error(y_test_rescaled, preds_rescaled))
    mape = mean_absolute_percentage_error(y_test_rescaled, preds_rescaled)
    r2 = r2_score(y_test_rescaled, preds_rescaled)

    print(f"RMSE: {rmse:.2f}")
    print(f"MAPE: {mape:.2%}")
    print(f"R²: {r2:.4f}")

    plt.figure(figsize=(10, 5))
    plt.plot(y_test_rescaled, label="True price")
    plt.plot(preds_rescaled, label="Predicted price")
    plt.title(f"LSTM predict {symbol}")
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    train_and_predict("BTC-USD")