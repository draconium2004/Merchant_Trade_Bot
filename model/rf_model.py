# models/rf_model.py
import joblib
import numpy as np
from feature_engineering import make_features

_MODEL_PATH = 'models/rf_model.pkl'
_BUY_THR = 0.7
_SELL_THR = 0.3

def load_model():
    """Lazy‐load the RF classifier from disk."""
    return joblib.load(_MODEL_PATH)

_rf = load_model()

def generate_signal(df_ohlcv):
    """
    Input: df_ohlcv = latest N bars of OHLCV (must cover at least 50 bars for MA50).
    Returns: dict with { 'signal': 1|0|-1, 'prob_up': float }
    """
    df_feat = make_features(df_ohlcv)
    # take only the last row’s features
    X_live = df_feat[['return','ma20','ma50','rsi','volume']].iloc[[-1]]
    prob_up = _rf.predict_proba(X_live)[0,1]
    if prob_up > _BUY_THR:
        sig = 1   # buy
    elif prob_up < _SELL_THR:
        sig = -1  # sell/short
    else:
        sig = 0   # hold
    return {'signal': sig, 'prob_up': prob_up}