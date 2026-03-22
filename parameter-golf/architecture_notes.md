# Architecture Notes — Parameter Golf Baseline

## Model Architecture

### GPT with U-Net Skip Connections
- **Layers**: 9 total (4 encoder + 5 decoder with skip connections)
- **Embedding dim**: 512
- **Attention heads**: 8 query heads, 4 KV heads (GQA with 2:1 ratio)
- **MLP expansion**: 2x (hidden dim = 1024)
- **MLP activation**: relu^2 (ReLU followed by squaring)
- **Vocab size**: 1024 (BPE via SentencePiece)
- **Sequence length**: 1024 tokens
- **Tied embeddings**: Yes (tok_emb shared with lm_head)
- **Normalization**: RMSNorm (pre-norm style)
- **Position encoding**: RoPE (base=10000)
- **Logit softcapping**: tanh-based at 30.0

### U-Net Skip Structure
- First `num_layers//2` blocks are "encoder" — outputs stored as skip connections
- Remaining blocks are "decoder" — skip connections added back (weighted by learnable `skip_weights`)
- Each block also has `resid_mix` parameter that blends current residual with initial embedding (x0)

### Block Structure
Each block:
1. RMSNorm -> Attention -> scale by `attn_scale` -> residual add
2. RMSNorm -> MLP -> scale by `mlp_scale` -> residual add
3. Before attention: mix current `x` with initial `x0` via learnable `resid_mix`

### Parameter Count Breakdown
- tok_emb: 1024 * 512 = 524,288 params
- Per block (9 blocks):
  - c_q: 512 * 512 = 262,144
  - c_k: 512 * 256 = 131,072
  - c_v: 512 * 256 = 131,072
  - proj: 512 * 512 = 262,144
  - fc (MLP): 512 * 1024 = 524,288
  - proj (MLP): 1024 * 512 = 524,288
  - q_gain: 8
  - attn_scale: 512
  - mlp_scale: 512
  - resid_mix: 2 * 512 = 1,024
  - Block total: ~1,836,064
- skip_weights: 4 * 512 = 2,048
- Total: ~524,288 + 9*1,836,064 + 2,048 = ~17.05M params

## Training Loop

### Optimizer Setup
- **Muon optimizer** for 2D matrix params in transformer blocks (matrix_lr=0.04, momentum=0.95)
  - Newton-Schulz orthogonalization (5 steps)
  - Momentum warmup from 0.85 to 0.95 over 500 steps
- **Adam** for embeddings (tied_embed_lr=0.05, betas=(0.9, 0.95))
- **Adam** for scalar/vector params (scalar_lr=0.04)

### Schedule
- **Warmup**: 20 steps (compile warmup, then restore initial weights)
- **Training**: Up to 20,000 iterations or 600s wallclock
- **Warmdown**: Cosine-like LR decay in last 1200 steps (or by wallclock proportion)
- **Batch**: 524,288 tokens per step, grad accumulation = 8 // world_size

### Data
- FineWeb 10B subset, preprocessed into binary shards
- Sequential streaming (no shuffling, wraps around)
- Distributed: each rank gets disjoint chunk per step

## Evaluation Pipeline
- Validation on full fineweb_val split
- Computes both val_loss (cross-entropy in nats) and val_bpb (bits per byte)
- BPB accounts for tokenizer compression ratio (bytes per token varies)
- Uses SentencePiece lookup tables for byte counting

## Compression Pipeline
- **Quantization**: int8 per-row for 2D tensors, per-tensor for vectors
  - Clip at 99.99984th percentile before quantizing
  - Scales stored as fp16
  - Small tensors (<65536 elements) kept as fp16 passthrough
  - Control tensors (scales, gains, etc.) kept as fp32
- **Compression**: zlib level 9 on the torch.save'd quantized state dict
- **Artifact size**: compressed_model_bytes + code_bytes must be < 16,000,000

## Key Observations for Improvement
1. **MLP ratio is only 2x** — lower than typical 4x, but leaderboard winners use 3x
2. **int8 quantization** — leaderboard uses int6/int5, saving ~25-37% on weight storage
3. **zlib compression** — zstd-22 gives significantly better ratios
4. **9 layers** — winners use 10-11 layers (enabled by better quantization)
5. **No BigramHash or SmearGate** — cheap techniques that add bigram context
6. **Standard evaluation** — sliding window eval significantly improves bpb at no training cost
7. **No SWA** — weight averaging is free and consistently helps
