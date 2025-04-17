# train_rf.py
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from feature_engineering import make_features

# 1. Load your historical OHLCV CSV (or however you store it)
df = pd.read_csv('data/historical_ohlcv.csv', index_col='timestamp', parse_dates=True)

# 2. Feature engineering & labeling
df_feat = make_features(df)
df_feat['label'] = (df_feat['close'].shift(-1) > df_feat['close']).astype(int)
df_feat = df_feat.dropna()

X = df_feat[['return','ma20','ma50','rsi','volume']]
y = df_feat['label']

# 3. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# 4. Fit RF
rf = RandomForestClassifier(n_estimators=200, min_samples_leaf=5, random_state=42)
rf.fit(X_train, y_train)

# 5. Evaluate (optional)
print("Test accuracy:", rf.score(X_test, y_test))

# 6. Save model
joblib.dump(rf, 'models/rf_model.pkl')
print("Model saved to models/rf_model.pkl")