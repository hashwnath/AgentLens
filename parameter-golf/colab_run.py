"""
Copy-paste this into a Google Colab notebook cell (with GPU runtime).
It will: clone the repo, download data, and run training.

Instructions:
1. Go to https://colab.research.google.com
2. Runtime > Change runtime type > T4 GPU
3. Paste this entire script into a cell and run it
"""

# ── Cell 1: Setup ──────────────────────────────────────────────────────────────
import subprocess, os

# Clone repo (replace with your fork URL if needed)
if not os.path.exists("AgentLens"):
    subprocess.run(["git", "clone", "-b", "claude/parameter-golf-techniques-h93S0",
                     "https://github.com/hashwnath/AgentLens.git"], check=True)
os.chdir("AgentLens/parameter-golf")

# Install deps
subprocess.run(["pip", "install", "-q", "torch", "sentencepiece", "huggingface_hub", "zstandard"], check=True)

# Download data (~80 training shards, ~1 val shard)
subprocess.run(["python3", "data/cached_challenge_fineweb.py", "--variant", "sp1024"], check=True)

# ── Cell 2: Train (single T4 GPU) ─────────────────────────────────────────────
env = os.environ.copy()
env.update({
    "RUN_ID":              "colab_v1",
    "DATA_PATH":           "./data/datasets/fineweb10B_sp1024",
    "TOKENIZER_PATH":      "./data/tokenizers/fineweb_1024_bpe.model",
    "VOCAB_SIZE":          "1024",
    # Architecture
    "NUM_LAYERS":          "10",
    "MODEL_DIM":           "512",
    "MLP_MULT":            "3",
    "NUM_HEADS":           "8",
    "NUM_KV_HEADS":        "4",
    # Training
    "TRAIN_SEQ_LEN":       "1024",
    "TRAIN_BATCH_TOKENS":  "65536",   # smaller for T4's 16GB VRAM
    "ITERATIONS":          "4000",    # shorter run for testing; full run = default
    "VAL_LOSS_EVERY":      "100",
    # Techniques
    "QAT_ENABLED":         "1",       # int6 QAT with STE
    "PRUNE_FRAC":          "0.03",    # magnitude pruning
    "USE_BIGRAM_HASH":     "1",
    "BIGRAM_VOCAB_SIZE":   "10240",
    "BIGRAM_DIM":          "128",
    "USE_SMEARGATE":       "1",
})

# Single GPU training with torchrun
result = subprocess.run(
    ["torchrun", "--standalone", "--nproc_per_node=1", "train_gpt.py"],
    env=env,
)
print(f"\nTraining finished with exit code {result.returncode}")
