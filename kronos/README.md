# Kronos Setup

[Kronos](https://github.com/shiyu-coder/Kronos) is a foundation model for financial candlestick (K-line) sequences, trained on data from 45+ global exchanges. It predicts OHLCV bars autoregressively.

## Quick setup

```bash
# From the repo root — clones Kronos and installs deps
bash kronos/setup.sh
```

## Web UI (recommended)

```bash
bash kronos/start_webui.sh
# Open http://localhost:7070
```

Upload a CSV file with columns `open, high, low, close` (and optionally `volume`, `timestamps`) and click **Predict**.

## Python quickstart

```bash
python kronos/quickstart.py
```

Generates synthetic OHLCV data, loads Kronos-small, and prints a 20-bar forecast.  
**First run downloads ~100 MB from HuggingFace Hub.**

## Available models

| Model | Params | Context | Notes |
|---|---|---|---|
| `NeoQuasar/Kronos-mini` | 4.1M | 2048 | Fastest |
| `NeoQuasar/Kronos-small` | 24.7M | 512 | Recommended starting point |
| `NeoQuasar/Kronos-base` | 102.3M | 512 | Best quality |

## Data format

Input CSV must have at minimum:

```
timestamps,open,high,low,close,volume
2024-01-01 09:00,100.0,101.5,99.2,100.8,500000
...
```

Kronos needs at least **400 rows** of historical context by default.

## Finetuning on your own data

See `.kronos-src/finetune/README.md` after running `setup.sh`.
