# 🚀 Agent-lightning Integration Guide

This guide explains how AgentLens integrates with Microsoft's **Agent-lightning** framework for continuous optimization and performance improvement.

## What is Agent-lightning?

Agent-lightning is an open-source trainer that enables optimization of AI agents using reinforcement learning with minimal code modifications. It allows you to:

- **Optimize agent performance** through RL algorithms
- **Improve prompt templates** automatically
- **Track quality metrics** across rollouts
- **Fine-tune agent behavior** without rewrites

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentLens Pipeline                        │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐         │
│  │ Code   │→→→│  MCP   │→→→│  Slop  │→→→│Report  │         │
│  │Scanner │   │Fetcher │   │Detector│   │Compiler│         │
│  └────────┘   └────────┘   └────────┘   └────────┘         │
│       ↓            ↓            ↓            ↓              │
│  ┌──────────────────────────────────────────────┐          │
│  │        Agent-lightning Instrumentation        │          │
│  │  • agl.emit_message() - Log events           │          │
│  │  • agl.emit_object() - Structured data       │          │
│  │  • agl.emit_reward() - Quality scores        │          │
│  └──────────────────────────────────────────────┘          │
│                         ↓                                   │
│  ┌──────────────────────────────────────────────┐          │
│  │          LightningStore (Training)            │          │
│  │  • Collect rollout traces                    │          │
│  │  • Calculate rewards                         │          │
│  │  • Optimize prompts & behavior               │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Automatic Quality Scoring

Every analysis generates a quality score (0.0 - 1.0) based on:

- **Completeness** - Report contains all required sections
- **Issue Detection** - Number of critical findings, warnings, strengths
- **Code Examples** - Actionable code snippets provided
- **Best Practices** - Compliance checks performed

### 2. Instrumentation Points

The integration adds lightweight tracking at key points:

```python
# Start of analysis
agl.emit_message("🚀 Starting analysis...")
agl.emit_object({"repo_url": url, "mode": "agent-lightning"})

# During agent execution
agl.emit_message("🔍 CodeScanner agent starting...")
agl.emit_object({"agent": "CodeScanner", "output_length": len(result)})

# Completion with reward
quality_score = calculate_quality(report)
agl.emit_reward(quality_score)
```

### 3. Zero-Code Fallback

If Agent-lightning is not installed, AgentLens runs normally:

```python
try:
    import agentlightning as agl
    AGENT_LIGHTNING_ENABLED = True
except ImportError:
    AGENT_LIGHTNING_ENABLED = False
```

## Installation

### 1. Install Agent-lightning

```bash
pip install agentlightning
```

Or add to your virtual environment:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import agentlightning; print('✅ Agent-lightning ready!')"
```

## Usage

### Run Benchmark

Compare performance with and without optimization:

```bash
python train_agent.py --mode benchmark
```

This will:
1. Run baseline analysis (standard mode)
2. Run optimized analysis (Agent-lightning mode)
3. Compare quality scores and execution time

### Run Training Loop

Train the multi-agent system across multiple repositories:

```bash
python train_agent.py --mode train --epochs 5
```

Training repositories include:
- LangChain
- AutoGen
- Anthropic SDK
- OpenAI Python SDK

### View Training Metrics

Agent-lightning automatically tracks:

```
📊 EPOCH 1/3
─────────────────────────────────────────
🔍 Analyzing: https://github.com/langchain-ai/langchain
   ✅ Quality Score: 0.847

🔍 Analyzing: https://github.com/microsoft/autogen
   ✅ Quality Score: 0.791

📈 Epoch 1 Average Reward: 0.819
```

## Quality Metrics Explained

The `_calculate_report_quality()` function scores reports based on:

| Metric | Points | Description |
|--------|--------|-------------|
| **Completion** | 0.2 | Report is at least 100 characters |
| **Critical Issues** | 0.2 | Number of 🔴 critical findings |
| **Warnings** | 0.2 | Number of 🟡 warnings |
| **Strengths** | 0.1 | Number of 🟢 positive findings |
| **Required Sections** | 0.3 | Executive Summary, Critical Findings, etc. |
| **Code Examples** | 0.1 | Presence of ``` code blocks |

**Maximum Score:** 1.0

## Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
GITHUB_TOKEN=ghp_...  # Optional
ENABLE_TRACING=true    # OpenTelemetry traces
```

### Training Repositories

Edit `train_agent.py` to customize:

```python
TRAINING_REPOS = [
    "https://github.com/your-org/agent-repo-1",
    "https://github.com/your-org/agent-repo-2",
]
```

## Advanced: Custom Rewards

You can customize the reward function for your use case:

```python
def _calculate_report_quality(self, report: str) -> float:
    score = 0.0

    # Custom scoring logic
    if "SQL injection" in report:
        score += 0.3  # High value for security findings

    if report.count("```python") > 3:
        score += 0.2  # Reward Python code examples

    return min(1.0, score)
```

## Monitoring

### OpenTelemetry Integration

AgentLens includes built-in OpenTelemetry tracing that works alongside Agent-lightning:

```bash
# Run DevUI to visualize traces
python devui.py
```

Then open: http://localhost:8080

You'll see:
- Agent handoff flows
- Tool calls to MCP servers
- Agent-lightning emit events
- Reward signals

### Agent-lightning Dashboard

Agent-lightning provides a LightningStore that tracks:
- Rollout history
- Reward trends over epochs
- Prompt template versions
- Model improvements

## Troubleshooting

### Agent-lightning not found

```bash
pip install agentlightning
# OR for pre-release
pip install --upgrade --pre --index-url https://test.pypi.org/simple/ agentlightning
```

### ImportError on agl.rollout

Make sure you're using the `@agl.rollout` decorator only on top-level functions:

```python
@agl.rollout
async def analyze_repository_rollout(self, repo_url: str) -> float:
    # Your code here
    return reward_score
```

### Rewards always 0.0

Check that:
1. Reports are being generated successfully
2. `_calculate_report_quality()` is being called
3. Quality metrics match your report format

## Performance Tips

1. **Start with benchmarks** - Run `--mode benchmark` before training
2. **Use smaller repos** - Train on focused, specialized agent codebases
3. **Monitor quality trends** - Track avg reward across epochs
4. **Iterate on rewards** - Tune scoring to match your quality goals

## Next Steps

- 📖 Read the [Agent-lightning docs](https://microsoft.github.io/agent-lightning/)
- 🧪 Experiment with custom reward functions
- 🎯 Train on your own agent repositories
- 📊 Monitor improvements in DevUI

## Resources

- [Agent-lightning GitHub](https://github.com/microsoft/agent-lightning)
- [Microsoft Research Blog](https://www.microsoft.com/en-us/research/blog/agent-lightning-adding-reinforcement-learning-to-ai-agents-without-code-rewrites/)
- [AgentLens Documentation](README.md)

---

**Built with:** Microsoft Agent Framework + Agent-lightning + OpenAI
