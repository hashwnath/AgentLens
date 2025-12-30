"""
Agent Analyzer - Microsoft Agent Framework Multi-Agent Pipeline
================================================================
True multi-agent architecture with OpenTelemetry tracing and Agent-lightning optimization.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import Optional, Callable, Awaitable

from agent_framework import ChatAgent, HandoffBuilder
from agent_framework.openai import OpenAIChatClient
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Agent Lightning for optimization
try:
    import agentlightning as agl
    AGENT_LIGHTNING_ENABLED = True
except ImportError:
    AGENT_LIGHTNING_ENABLED = False
    print("⚠️  Agent Lightning not installed. Running without optimization.")

# OpenTelemetry for tracing
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

# Configure OpenTelemetry tracing
resource = Resource.create({"service.name": "agentlens-analyzer"})
provider = TracerProvider(resource=resource)

# Export traces to console (visible in terminal)
if os.getenv("ENABLE_TRACING", "true").lower() == "true":
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

trace.set_tracer_provider(provider)
tracer = trace.get_tracer("agentlens.analyzer")

from github_client import GitHubClient, RepoInfo


# MCP Server endpoints
MS_LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"
LANGCHAIN_MCP_URL = "https://docs.langchain.com/mcp"


class MCPDocsFetcher:
    """Fetches documentation from MCP servers with progress reporting."""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
    
    async def _send_mcp_progress(self, server: str, tool: str, query: str, result: str = None, status: str = "calling"):
        if self.progress_callback:
            await self.progress_callback("mcp_tool", {
                "server": server,
                "tool": tool,
                "query": query,
                "result": result[:500] if result else None,
                "status": status
            })
    
    async def search_ms_learn(self, query: str) -> str:
        await self._send_mcp_progress("MS Learn", "search", query, status="calling")
        try:
            async with streamablehttp_client(MS_LEARN_MCP_URL) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    search_tool = next((t.name for t in tools.tools if "search" in t.name.lower()), None)
                    if not search_tool:
                        return f"No search tool found"
                    result = await session.call_tool(search_tool, {"query": query})
                    text = str(result.content[0].text if hasattr(result.content[0], 'text') else result.content)
                    await self._send_mcp_progress("MS Learn", search_tool, query, text, "complete")
                    return text
        except Exception as e:
            error = f"MS Learn MCP error: {str(e)}"
            await self._send_mcp_progress("MS Learn", "search", query, error, "error")
            return error
    
    async def search_langchain_docs(self, query: str) -> str:
        await self._send_mcp_progress("LangChain", "SearchDocsByLangChain", query, status="calling")
        try:
            async with streamablehttp_client(LANGCHAIN_MCP_URL) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("SearchDocsByLangChain", {"query": query})
                    text = str(result.content[0].text if hasattr(result.content[0], 'text') else result.content)
                    await self._send_mcp_progress("LangChain", "SearchDocsByLangChain", query, text, "complete")
                    return text
        except Exception as e:
            error = f"LangChain MCP error: {str(e)}"
            await self._send_mcp_progress("LangChain", "SearchDocsByLangChain", query, error, "error")
            return error


class AgentAnalyzer:
    """Multi-agent code analyzer using Microsoft Agent Framework with true agent handoffs."""
    
    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4o",
        github_token: Optional[str] = None
    ):
        self.openai_api_key = openai_api_key
        self.model = model
        self.github = GitHubClient(token=github_token)
        self.progress_callback = None
        self.current_step = 0
        
        # Initialize OpenAI client
        self.chat_client = OpenAIChatClient(
            api_key=openai_api_key,
            model_id=model
        )
        
        # Create specialized agents
        self._create_agents()
    
    def _create_agents(self):
        """Create the multi-agent team with specialized roles."""
        
        # Agent 1: Code Scanner - Entry point, analyzes structure
        self.code_scanner = self.chat_client.create_agent(
            name="CodeScanner",
            instructions="""You are a Code Scanner agent that analyzes AI/ML codebases.

EXTRACT and report:
1. FRAMEWORKS: LangChain, AutoGen, CrewAI, Semantic Kernel, etc.
2. ARCHITECTURE: Single agent, multi-agent, RAG, ReAct, graph-based
3. LLM_CALLS: ChatOpenAI, Anthropic, invoke(), stream(), specific models
4. TOOLS: @tool decorators, Tool classes, function definitions
5. PATTERNS: Prompt templates, memory, retriever chains

Format with clear headers. Include file paths and line references.
After analysis, hand off to MCPFetcher for documentation lookup."""
        )
        
        # Agent 2: MCP Fetcher - Gets live documentation
        self.mcp_fetcher_agent = self.chat_client.create_agent(
            name="MCPFetcher",
            instructions="""You are an MCP Documentation Fetcher agent.

Based on the CodeScanner's findings, identify:
1. Which frameworks need documentation lookup
2. Which patterns need best practice references
3. Which API calls need official guidance

Summarize the documentation needs and hand off to BestPracticesChecker."""
        )
        
        # Agent 3: Best Practices Checker
        self.best_practices_agent = self.chat_client.create_agent(
            name="BestPracticesChecker",
            instructions="""You are a Best Practices Checker agent.

Based on CodeScanner findings and MCP documentation:
1. Score each framework usage 0-100
2. Check against official patterns (LCEL, function calling, prompt caching)
3. Identify compliance gaps with documentation

Provide specific scores and gaps. Hand off to SlopDetector."""
        )
        
        # Agent 4: Slop Detector
        self.slop_detector = self.chat_client.create_agent(
            name="SlopDetector",
            instructions="""You are a Slop Detector agent that finds anti-patterns.

Categories to check:
🔴 CRITICAL: Security issues, exposed keys, major bugs
🟡 WARNING: Suboptimal patterns, missing error handling
🟢 SUGGESTION: Style improvements, minor optimizations

SLOP TYPES:
- Prompt slop: Verbose prompts, conflicting instructions
- Architecture slop: God agents, missing retry logic
- Tool slop: Reinventing MCPs, inefficient schemas
- Cost slop: No caching, unnecessary context

Rate each issue. Hand off to Optimizer."""
        )
        
        # Agent 5: Optimizer
        self.optimizer = self.chat_client.create_agent(
            name="Optimizer",
            instructions="""You are an Optimizer agent that suggests improvements.

For each issue from SlopDetector:
1. Suggest MCP server replacements
2. Calculate potential cost savings
3. Recommend caching strategies
4. Provide copy-paste code fixes

Format: Effort (Low/Medium/High), Impact, Code example.
Hand off to ReportCompiler."""
        )
        
        # Agent 6: Report Compiler - Final agent
        self.report_compiler = self.chat_client.create_agent(
            name="ReportCompiler",
            instructions="""You are the Report Compiler agent that creates the final AgentLens report.

Compile all findings into a professional Markdown report:

1. **Executive Summary** - Overall score X/100, critical issues count
2. **Code Analysis** - Frameworks, architecture, patterns
3. **🔴 Critical Findings** - With copy-paste fixes
4. **🟡 Warnings** - Should-fix items
5. **🟢 Strengths** - What's done well
6. **Cost Analysis** - Token usage, optimization potential
7. **MCP Opportunities** - Table of replacements
8. **Best Practices Scores** - Per-framework ratings
9. **Top 5 Recommendations** - Prioritized actions
10. **Action Items** - Immediate/Short-term/Long-term

End with: **Report Generated by AgentLens** 🔍"""
        )
    
    def _build_workflow(self):
        """Build the multi-agent workflow with handoffs."""
        return (
            HandoffBuilder(
                name="agentlens_analysis",
                participants=[
                    self.code_scanner,
                    self.mcp_fetcher_agent,
                    self.best_practices_agent,
                    self.slop_detector,
                    self.optimizer,
                    self.report_compiler
                ]
            )
            .set_coordinator(self.code_scanner)
            .add_handoff(self.code_scanner, [self.mcp_fetcher_agent])
            .add_handoff(self.mcp_fetcher_agent, [self.best_practices_agent])
            .add_handoff(self.best_practices_agent, [self.slop_detector])
            .add_handoff(self.slop_detector, [self.optimizer])
            .add_handoff(self.optimizer, [self.report_compiler])
            .with_termination_condition(lambda conv: any("Report Generated by AgentLens" in str(m.text) for m in conv))
            .build()
        )
    
    async def _emit_step(self, agent: str, description: str, detail: str, status: str = "in_progress"):
        if status == "in_progress":
            self.current_step += 1
        if self.progress_callback:
            await self.progress_callback("step", {
                "step_number": self.current_step,
                "agent_name": agent,
                "status": status,
                "description": description,
                "detail": detail
            })
    
    async def analyze_repo(
        self,
        repo_url: str,
        progress_callback: Optional[Callable[[str, any], Awaitable[None]]] = None
    ) -> str:
        """Analyze a repository using multi-agent workflow with OpenTelemetry tracing and Agent-lightning."""
        if AGENT_LIGHTNING_ENABLED:
            return await self._analyze_repo_with_lightning(repo_url, progress_callback)
        else:
            return await self._analyze_repo_impl(repo_url, progress_callback)

    async def _analyze_repo_impl(
        self,
        repo_url: str,
        progress_callback: Optional[Callable[[str, any], Awaitable[None]]] = None
    ) -> str:
        """Internal implementation of repository analysis."""
        with tracer.start_as_current_span("analyze_repo") as span:
            span.set_attribute("repo_url", repo_url)
            
            self.progress_callback = progress_callback
            self.mcp_fetcher = MCPDocsFetcher(progress_callback)
            self.current_step = 0
            
            # Step 1: Validate repository
            with tracer.start_as_current_span("validate_repository"):
                await self._emit_step("RepositoryValidator", "Validating repository URL", f"Checking {repo_url}...")
                
                try:
                    owner, repo = self.github.parse_repo_url(repo_url)
                    repo_info = await self.github.validate_repo(owner, repo)
                except ValueError as e:
                    await self._emit_step("RepositoryValidator", "Validating repository URL", f"❌ {str(e)}", "error")
                    raise
                
                await self._emit_step("RepositoryValidator", "Validating repository URL", 
                                     f"✓ {repo_info.name} ({repo_info.language}, ⭐ {repo_info.stars})", "completed")
            
            # Step 2: Fetch files
            with tracer.start_as_current_span("fetch_files"):
                await self._emit_step("FileGatherer", "Gathering repository files", "Fetching file tree...")
                
                try:
                    file_tree = await self.github.get_file_tree(owner, repo, repo_info.default_branch)
                    contents = await self.github.fetch_repo_contents(owner, repo, repo_info.default_branch)
                except Exception as e:
                    await self._emit_step("FileGatherer", "Gathering repository files", f"❌ {str(e)}", "error")
                    raise ValueError(f"Failed to fetch repository: {e}")
                
                if not contents:
                    raise ValueError("No analyzable files found")
                
                total_lines = sum(c.count('\n') for c in contents.values())
                py_files = sum(1 for f in contents if f.endswith('.py'))
                span.set_attribute("files_count", len(contents))
                span.set_attribute("total_lines", total_lines)
                
                await self._emit_step("FileGatherer", "Gathering repository files",
                                     f"✓ {len(contents)} files ({total_lines:,} lines) • {py_files} Python", "completed")
            
            # Prepare codebase context
            codebase_context = self._prepare_context(repo_info, repo_url, contents, file_tree)
            
            # Run multi-agent analysis
            with tracer.start_as_current_span("multi_agent_analysis"):
                report = await self._run_multi_agent_workflow(codebase_context, contents)
            
            span.set_attribute("report_length", len(report))
            return report

    async def _analyze_repo_with_lightning(
        self,
        repo_url: str,
        progress_callback: Optional[Callable[[str, any], Awaitable[None]]] = None
    ) -> str:
        """Agent-lightning instrumented version of repository analysis."""
        agl.emit_message(f"🚀 Starting Agent-lightning optimized analysis for {repo_url}")
        agl.emit_object({"repo_url": repo_url, "mode": "agent-lightning"})

        try:
            # Run the standard implementation
            report = await self._analyze_repo_impl(repo_url, progress_callback)

            # Calculate quality metrics for reward signal
            quality_score = self._calculate_report_quality(report)

            # Emit reward signal for RL optimization
            agl.emit_reward(quality_score)
            agl.emit_message(f"✅ Analysis complete. Quality score: {quality_score:.2f}")
            agl.emit_object({
                "report_length": len(report),
                "quality_score": quality_score,
                "critical_issues": report.count("🔴"),
                "warnings": report.count("🟡"),
                "strengths": report.count("🟢")
            })

            return report

        except Exception as e:
            agl.emit_exception(e)
            agl.emit_reward(0.0)  # Zero reward on failure
            raise

    def _calculate_report_quality(self, report: str) -> float:
        """
        Calculate a quality score for the analysis report (0.0 to 1.0).
        Used as reward signal for Agent-lightning optimization.
        """
        score = 0.0

        # Base score for completion
        if len(report) > 100:
            score += 0.2

        # Points for finding issues
        critical_count = report.count("🔴") + report.lower().count("critical")
        warnings_count = report.count("🟡") + report.lower().count("warning")
        strengths_count = report.count("🟢") + report.lower().count("strength")

        # Reward balanced analysis
        if critical_count > 0:
            score += min(0.2, critical_count * 0.05)
        if warnings_count > 0:
            score += min(0.2, warnings_count * 0.03)
        if strengths_count > 0:
            score += min(0.1, strengths_count * 0.02)

        # Points for comprehensive sections
        required_sections = [
            "Executive Summary",
            "Critical Findings",
            "Recommendations",
            "Best Practices"
        ]
        for section in required_sections:
            if section.lower() in report.lower():
                score += 0.075

        # Bonus for code examples
        code_blocks = report.count("```")
        if code_blocks > 0:
            score += min(0.1, code_blocks * 0.02)

        return min(1.0, score)
    
    def _prepare_context(self, repo_info: RepoInfo, repo_url: str, contents: dict, file_tree: list) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        context = f"""# Repository: {repo_info.name}
- **Description:** {repo_info.description}
- **Language:** {repo_info.language}
- **Stars:** {repo_info.stars}
- **URL:** {repo_url}
- **Date:** {today}

## Files:
"""
        for f in file_tree[:30]:
            context += f"- {f['path']}\n"
        context += "\n## Code:\n\n"
        
        for path, content in list(contents.items())[:15]:
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            context += f"### {path}\n```\n{content}\n```\n\n"
        
        return context
    
    async def _run_multi_agent_workflow(self, codebase_context: str, contents: dict) -> str:
        """Run the sequential multi-agent analysis."""

        # Step 3: CodeScanner
        await self._emit_step("CodeScanner", "Scanning codebase structure", "Analyzing frameworks and patterns...")

        if AGENT_LIGHTNING_ENABLED:
            agl.emit_message("🔍 CodeScanner agent starting...")

        scan_result = await self.code_scanner.run(
            f"Analyze this AI agent codebase and extract detailed findings:\n\n{codebase_context[:12000]}"
        )
        scan_text = str(scan_result)

        if AGENT_LIGHTNING_ENABLED:
            agl.emit_object({"agent": "CodeScanner", "output_length": len(scan_text)})
        
        # Extract frameworks
        frameworks = []
        if "langchain" in scan_text.lower(): frameworks.append("LangChain")
        if "autogen" in scan_text.lower(): frameworks.append("AutoGen")
        if "anthropic" in scan_text.lower(): frameworks.append("Anthropic")
        if "openai" in scan_text.lower(): frameworks.append("OpenAI")
        
        frameworks_str = ", ".join(frameworks) or "Custom"
        await self._emit_step("CodeScanner", "Scanning codebase structure",
                             f"✓ Frameworks: {frameworks_str}", "completed")
        
        # Step 4: MCP Documentation Fetch
        await self._emit_step("MCPFetcher", "Fetching live documentation", 
                             f"Querying MCP servers for {frameworks_str}...")
        
        # Dynamic MCP queries based on scan results
        mcp_docs = {}
        llm_calls = re.findall(r'(?:ChatOpenAI|ChatAnthropic|OpenAI|invoke|stream)', scan_text, re.I)
        patterns = re.findall(r'(?:ReAct|RAG|retriever|memory|chain|agent)', scan_text, re.I)
        
        if "LangChain" in frameworks:
            query = f"LangChain {' '.join(set(patterns[:3]))} best practices" if patterns else "LangChain LCEL"
            mcp_docs["langchain"] = await self.mcp_fetcher.search_langchain_docs(query)
        
        if "OpenAI" in frameworks or "Anthropic" in frameworks:
            query = f"AI agent {' '.join(set(llm_calls[:2]))} best practices" if llm_calls else "LLM best practices"
            mcp_docs["llm"] = await self.mcp_fetcher.search_ms_learn(query)
        
        mcp_docs["general"] = await self.mcp_fetcher.search_langchain_docs("agent error handling production")
        
        mcp_text = "\n".join([f"## {k}\n{v[:1500]}" for k, v in mcp_docs.items()])
        
        await self._emit_step("MCPFetcher", "Fetching live documentation",
                             f"✓ {len(mcp_docs)} docs fetched", "completed")
        
        # Step 5: Best Practices Check
        await self._emit_step("BestPracticesChecker", "Checking best practices", "Comparing with documentation...")
        
        practices_result = await self.best_practices_agent.run(
            f"Check this codebase against best practices:\n\nSCAN:\n{scan_text[:3000]}\n\nDOCS:\n{mcp_text[:4000]}"
        )
        practices_text = str(practices_result)
        
        violations = practices_text.lower().count("violation") + practices_text.lower().count("missing")
        await self._emit_step("BestPracticesChecker", "Checking best practices",
                             f"✓ Found {violations} improvement areas", "completed")
        
        # Step 6: Slop Detection
        await self._emit_step("SlopDetector", "Detecting anti-patterns", "Analyzing for code slop...")
        
        slop_result = await self.slop_detector.run(
            f"Find anti-patterns in this codebase:\n\n{scan_text[:3000]}\n\nCODE:\n{codebase_context[:6000]}"
        )
        slop_text = str(slop_result)
        
        critical = slop_text.count("🔴") + slop_text.lower().count("critical")
        warnings = slop_text.count("🟡") + slop_text.lower().count("warning")
        
        await self._emit_step("SlopDetector", "Detecting anti-patterns",
                             f"✓ {critical} critical, {warnings} warnings", "completed")
        
        # Step 7: Optimization
        await self._emit_step("Optimizer", "Generating optimizations", "Creating recommendations...")
        
        optimizer_result = await self.optimizer.run(
            f"Suggest optimizations:\n\nISSUES:\n{slop_text[:3000]}\n\nGAPS:\n{practices_text[:2000]}"
        )
        optimizer_text = str(optimizer_result)
        
        recs = optimizer_text.count("```") + optimizer_text.lower().count("recommend")
        await self._emit_step("Optimizer", "Generating optimizations",
                             f"✓ {recs} recommendations with code", "completed")
        
        # Step 8: Final Report
        await self._emit_step("ReportCompiler", "Compiling final report", "Generating markdown report...")
        
        report_result = await self.report_compiler.run(
            f"""Compile the final AgentLens report:

SCAN: {scan_text[:2000]}
PRACTICES: {practices_text[:2000]}
SLOP: {slop_text[:2000]}
OPTIMIZER: {optimizer_text[:2000]}

MCP Sources:
- MS Learn MCP: https://learn.microsoft.com/api/mcp
- LangChain MCP: https://docs.langchain.com/mcp"""
        )
        
        final_report = str(report_result)
        
        await self._emit_step("ReportCompiler", "Compiling final report",
                             f"✓ Report generated ({len(final_report):,} chars)", "completed")
        
        return final_report
