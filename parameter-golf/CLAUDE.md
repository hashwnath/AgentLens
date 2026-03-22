# CLAUDE.md — Parameter Golf Challenge Context

## Project Overview
This is my entry for OpenAI's Parameter Golf challenge. Goal: minimize val_bpb (bits per byte) on FineWeb validation set with a model that fits in 16MB (weights + code) and trains in <10min on 8xH100s.

Repo: https://github.com/openai/parameter-golf (forked)
Dataset: FineWeb with 1024-token BPE vocabulary
Baseline: 1.2244 bpb (9L, 512dim, 1024vocab, tied embeddings)
Current SOTA: ~1.143 bpb
My target: Beat current SOTA or at minimum get a competitive non-record submission

## Environment
- Remote: RunPod 8xH100 SXM (for final submission runs)
- Local iteration: 1xH100 or Apple Silicon MLX for smoke tests
- Python + PyTorch, CUDA
- Key deps: torch, sentencepiece, huggingface_hub, datasets, tqdm

## File Structure
- `train_gpt.py` — main training script (this is what counts toward 16MB code size)
- `train_gpt_mlx.py` — Apple Silicon local testing script
- `data/` — dataset download and caching scripts
- `records/` — submission records folder

## Core Constraints
- 16MB = 16,000,000 bytes TOTAL (decimal, not MiB)
- Artifact = code bytes + compressed model bytes
- 10 minute wallclock on 8xH100 SXM
- No network calls during evaluation
- No accessing training data during eval (unless bits are "paid for" in 16MB)
- Validation data cannot be accessed during training
- Must beat SOTA by >= 0.005 nats with p < 0.01 statistical significance

## Current Architecture (Baseline)
- GPT-style transformer with U-Net skip connections
- 9 layers, 512 embedding dim
- 8 attention heads with 4 KV heads (GQA)
- 2x MLP expansion (relu^2 activation)
- 1024 vocab BPE tokenizer
- Tied input/output embeddings
- RMSNorm, RoPE, logit softcapping at 30.0
- Muon optimizer for matrix params, Adam for embeddings/scalars
- int8 quantization + zlib compression for serialization

## Proven Winning Techniques to Implement
Prioritized by impact (implement in this order):

### Phase 1: Quick Wins
1. **Increase to 10-11 layers** — more depth, offset by better quantization
2. **int6 QAT** — quantization-aware training with straight-through estimators
   - Train in fp16/bf16, quantize to int6 during forward pass
   - STE: gradient passes through quantization as identity
   - Pack 6-bit values efficiently for storage
3. **zstd-22 compression** — replace zlib with zstd at level 22 for better compression
4. **3x MLP ratio** — change MLP hidden dim to 3x embedding dim instead of 4x
5. **FP16 tied embeddings** — keep embeddings in fp16 (they compress well)

### Phase 2: Architecture Improvements
6. **BigramHash(N)** — hash-based bigram features
   - Hash consecutive token pairs into N buckets
   - Add learned embedding per bucket to token representation
   - N=4096 to 10240 based on budget
7. **SmearGate** — gating mechanism to blend adjacent token embeddings
8. **Sliding window evaluation** — at eval time, use stride=64 sliding window

### Phase 3: Training Optimization
9. **Muon optimizer tuning** — already in baseline, tune weight decay and momentum
10. **Orthogonal initialization** — spectral init for embeddings
11. **Stochastic Weight Averaging (SWA)** — average last N% of checkpoints

### Phase 4: Advanced (if time permits)
12. **Mixed precision quantization** — int5 for MLP weights, int6 for attention
13. **Test-time training (TTT)** with LoRA
14. **Depth recurrence** — share weights across layers
15. **Novel tokenizer exploration** — larger vocab if it helps compression

## How to Run Experiments

### Local smoke test (Mac/MLX):
```bash
RUN_ID=test_v1 \
ITERATIONS=200 \
TRAIN_BATCH_TOKENS=8192 \
VAL_LOSS_EVERY=0 \
VAL_BATCH_SIZE=8192 \
python3 train_gpt_mlx.py
```

### Single GPU test (RunPod 1xH100):
```bash
RUN_ID=experiment_v1 \
DATA_PATH=./data/datasets/fineweb10B_sp1024/ \
TOKENIZER_PATH=./data/tokenizers/fineweb_1024_bpe.model \
VOCAB_SIZE=1024 \
torchrun --standalone --nproc_per_node=1 train_gpt.py
```

### Full 8xH100 submission run:
```bash
RUN_ID=submission_v1 \
DATA_PATH=./data/datasets/fineweb10B_sp1024/ \
TOKENIZER_PATH=./data/tokenizers/fineweb_1024_bpe.model \
VOCAB_SIZE=1024 \
torchrun --standalone --nproc_per_node=8 train_gpt.py
```

## Experiment Tracking

After each run, log in `experiments.md`:
- RUN_ID, description of changes
- val_loss, val_bpb
- compressed model size in bytes
- total artifact size (code + model)
- training time
- any notes on what worked/didn't

## Code Style
- Keep train_gpt.py self-contained (it counts toward 16MB)
- Minimize comments in submission code (save bytes)
- External libraries (torch, etc.) don't count toward size limit
- Custom CUDA kernels are fine if they help
