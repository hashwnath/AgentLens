"""
AgentLens - Multi-Agent Code Reviewer
======================================
FastAPI backend with live progress streaming.
"""

import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from analyzer import AgentAnalyzer

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🔍 AgentLens - Multi-Agent Code Reviewer")
    print("   Powered by Microsoft Agent Framework + OpenAI\n")
    
    if not OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not configured.")
    else:
        print(f"✅ OpenAI API configured (model: {OPENAI_MODEL})")
    
    if GITHUB_TOKEN:
        print("✅ GitHub token configured (higher rate limits)")
    else:
        print("ℹ️  No GitHub token (may hit rate limits)")
    
    print("\n🚀 Server ready at http://localhost:8000\n")
    yield
    print("\n👋 AgentLens shutting down...")


app = FastAPI(title="AgentLens", lifespan=lifespan)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>AgentLens</h1>")


@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """WebSocket endpoint with live agent progress streaming."""
    await websocket.accept()
    
    try:
        if not OPENAI_API_KEY:
            await websocket.send_json({"type": "error", "message": "OPENAI_API_KEY not configured"})
            await websocket.close()
            return
        
        data = await websocket.receive_json()
        repo_url = data.get("repo_url", "")
        
        if not repo_url:
            await websocket.send_json({"type": "error", "message": "No repository URL provided"})
            await websocket.close()
            return
        
        # Progress callback for live streaming
        async def send_progress(event_type: str, data: any):
            try:
                if event_type == "step":
                    # Structured step descriptions
                    await websocket.send_json({
                        "type": "step",
                        "step_number": data.get("step_number"),
                        "agent_name": data.get("agent_name"),
                        "status": data.get("status"),
                        "description": data.get("description"),
                        "detail": data.get("detail")
                    })
                elif event_type == "stage":
                    await websocket.send_json({
                        "type": "stage",
                        "name": data.get("name"),
                        "status": data.get("status"),
                        "detail": data.get("detail", "")
                    })
                elif event_type == "agent_step":
                    await websocket.send_json({
                        "type": "agent_step",
                        "agent": data.get("agent"),
                        "status": data.get("status"),
                        "detail": data.get("detail", ""),
                        "output": data.get("output")
                    })
                elif event_type == "mcp_tool":
                    await websocket.send_json({
                        "type": "mcp_tool",
                        "server": data.get("server"),
                        "tool": data.get("tool"),
                        "query": data.get("query"),
                        "result": data.get("result"),
                        "status": data.get("status")
                    })
            except Exception:
                pass
        
        analyzer = AgentAnalyzer(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            github_token=GITHUB_TOKEN
        )
        
        report = await analyzer.analyze_repo(repo_url, progress_callback=send_progress)
        
        await websocket.send_json({
            "type": "complete",
            "report": report
        })
        
    except WebSocketDisconnect:
        pass
    except ValueError as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": f"Analysis failed: {str(e)}"})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "github_configured": bool(GITHUB_TOKEN)
    }
