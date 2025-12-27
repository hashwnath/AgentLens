# 🔍 AgentLens - AI Agent Code Reviewer

An AI-powered code reviewer that analyzes AI agent codebases on public GitHub repositories.

**Powered by:** Microsoft Agent Framework + OpenAI + MCP Servers

![AgentLens Demo](docs/demo.png)

## ✨ Features

- **🔴 Slop Detection** - Identifies anti-patterns and code smells in agent code
- **🔒 Security Analysis** - Flags exposed keys, missing error handling
- **💰 Token Consumption** - Analyzes cost optimization opportunities  
- **✅ Best Practices** - Checks compliance with LangChain, OpenAI, Anthropic standards
- **📚 MCP-Powered** - Fetches live documentation from MS Learn and LangChain MCP servers
- **🔄 Multi-Agent Pipeline** - 6 specialized agents working in sequence
- **📊 OpenTelemetry Tracing** - Built-in observability with DevUI support

## 🏗️ Architecture

```
┌─────────────┐     WebSocket      ┌─────────────────────────────────────┐
│  Browser UI │◄──────────────────►│         FastAPI Backend             │
└─────────────┘                    └─────────────────────────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
             ┌────────────┐                 ┌─────────────┐                 ┌─────────────┐
             │ GitHub API │                 │ OpenAI API  │                 │ MCP Servers │
             │            │                 │   (GPT-4o)  │                 │ • MS Learn  │
             └────────────┘                 └─────────────┘                 │ • LangChain │
                                                    │                       └─────────────┘
                                                    ▼
                              ┌──────────────────────────────────────────────────┐
                              │        Microsoft Agent Framework                  │
                              │  ┌──────────────────────────────────────────────┐│
                              │  │           6-Agent Pipeline                   ││
                              │  │  CodeScanner → MCPFetcher → BestPractices   ││
                              │  │  → SlopDetector → Optimizer → Reporter      ││
                              │  └──────────────────────────────────────────────┘│
                              └──────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AgentLens.git
cd AgentLens
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_MODEL` - Model to use (default: gpt-4o)
- `GITHUB_TOKEN` - (Optional) GitHub token for higher rate limits

### 4. Run the server

```bash
uvicorn main:app --reload --port 8000
```

### 5. Open in browser

Navigate to http://localhost:8000

## 🔧 DevUI - Agent Debugging

Run the DevUI for agent tracing and debugging:

```bash
python devui.py
```

Open http://localhost:8080 to see:
- Visual agent tracing
- Conversation flow between agents
- OpenTelemetry spans
- Tool calls and responses

## 📁 Project Structure

```
AgentLens/
├── main.py              # FastAPI server with WebSocket
├── analyzer.py          # Multi-agent analysis pipeline
├── github_client.py     # GitHub API client
├── devui.py             # DevUI for agent debugging
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── static/
    ├── index.html       # Frontend UI
    ├── styles.css       # Styling
    └── app.js           # Frontend logic
```

## 🤖 Agent Pipeline

| Agent | Role |
|-------|------|
| **CodeScanner** | Identifies frameworks, architecture, LLM calls |
| **MCPFetcher** | Fetches live docs from MCP servers |
| **BestPracticesChecker** | Scores compliance with standards |
| **SlopDetector** | Finds anti-patterns and issues |
| **Optimizer** | Suggests improvements and fixes |
| **ReportCompiler** | Generates final markdown report |

## 📊 Sample Report Output

```markdown
# AgentLens Analysis Report

## Executive Summary
- **Overall Score:** 72/100
- **Critical Issues:** 3
- **Warnings:** 7

## 🔴 Critical Findings
1. Exposed API key in config.py (line 15)
2. No retry logic for LLM calls
3. Missing error handling in agent.py

## 🟡 Warnings
...

## ✅ Strengths
...

## Recommendations
1. Add prompt caching for Anthropic calls
2. Replace custom search with MCP server
3. Implement structured outputs
```

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.11+
- **Agent Framework:** Microsoft Agent Framework (unified AutoGen + Semantic Kernel)
- **LLM:** OpenAI GPT-4o
- **MCP Servers:** MS Learn, LangChain Docs
- **Tracing:** OpenTelemetry
- **Frontend:** Vanilla HTML/CSS/JS

## 📝 License

MIT License

## 🙏 Acknowledgments

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [OpenAI](https://openai.com)
- [MCP Protocol](https://modelcontextprotocol.io)
