"""
Kronos quickstart — load the small model and run a prediction on synthetic OHLCV data.

Usage (from repo root):
    python kronos/quickstart.py

First run downloads ~100 MB from HuggingFace Hub (NeoQuasar/Kronos-small).
Subsequent runs use the local cache (~/.cache/huggingface).

The script generates 520 rows of synthetic candlestick data, uses the first 400
as context, and predicts the next 20 bars.
"""

import sys
import os
import numpy as np
import pandas as pd

KRONOS_SRC = os.path.join(os.path.dirname(__file__), "..", ".kronos-src")
if not os.path.isdir(KRONOS_SRC):
    sys.exit(
        "Kronos source not found. Run:  bash kronos/setup.sh\n"
        f"Expected path: {os.path.abspath(KRONOS_SRC)}"
    )
sys.path.insert(0, os.path.abspath(KRONOS_SRC))

try:
    from model import Kronos, KronosTokenizer, KronosPredictor
except ImportError as e:
    sys.exit(f"Could not import Kronos model: {e}\nRun: pip install -r .kronos-src/requirements.txt")

# --- synthetic OHLCV data -----------------------------------------------------
rng = np.random.default_rng(42)
n = 520
close = 100 * np.cumprod(1 + rng.normal(0, 0.01, n))
spread = close * rng.uniform(0.002, 0.008, n)
timestamps = pd.date_range("2024-01-01", periods=n, freq="1h")

df = pd.DataFrame({
    "timestamps": timestamps,
    "open":   close - spread / 2,
    "high":   close + spread,
    "low":    close - spread,
    "close":  close,
    "volume": rng.integers(100_000, 1_000_000, n).astype(float),
})

# --- load model ---------------------------------------------------------------
LOOKBACK = 400
PRED_LEN  = 20

print("Loading Kronos-small from HuggingFace Hub (first run downloads ~100 MB)...")
try:
    tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    model     = Kronos.from_pretrained("NeoQuasar/Kronos-small")
except Exception as e:
    sys.exit(
        f"Model load failed: {e}\n\n"
        "Make sure you have internet access and that HuggingFace Hub is reachable.\n"
        "Models are hosted at: https://huggingface.co/NeoQuasar"
    )

predictor = KronosPredictor(model, tokenizer, max_context=512)

# --- predict ------------------------------------------------------------------
x_df        = df.iloc[:LOOKBACK][["open", "high", "low", "close", "volume"]]
x_timestamp = df.iloc[:LOOKBACK]["timestamps"]
y_timestamp = df.iloc[LOOKBACK : LOOKBACK + PRED_LEN]["timestamps"]

print(f"Running prediction: {LOOKBACK} context bars → {PRED_LEN} forecast bars")
pred = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=PRED_LEN,
    T=1.0,
    top_p=0.9,
    sample_count=1,
    verbose=True,
)

print("\nPredicted OHLCV (first 5 rows):")
print(pred.head().to_string())
print(f"\nFull prediction saved to pred_df — shape: {pred.shape}")
