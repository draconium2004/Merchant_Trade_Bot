# models/rf_model.py
import numpy as np
import pandas as pd
import pickle

def generate_signal(symbol):
    # Dummy logic — replace with real model loading + prediction
    # You can use joblib or pickle to load a trained model
    signal = np.random.choice(['BUY', 'SELL', None], p=[0.4, 0.4, 0.2])
    if signal is None:
        return None
    return {
        'symbol': symbol,
        'side': signal,
        'price': 1.0923,
        'sl': 1.0880,
        'tp': 1.0985,
        'confidence': round(np.random.uniform(70, 95), 2)
    }
