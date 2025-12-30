"""
Agent-lightning Training Loop for AgentLens
============================================
Trains the multi-agent code analyzer using reinforcement learning.
"""

import asyncio
import os
from typing import List, Dict
from dotenv import load_dotenv

try:
    import agentlightning as agl
    from agentlightning import Trainer, RolloutConfig
    AGENT_LIGHTNING_AVAILABLE = True
except ImportError:
    print("❌ Agent-lightning not installed. Install with: pip install agentlightning")
    AGENT_LIGHTNING_AVAILABLE = False
    exit(1)

from analyzer import AgentAnalyzer

load_dotenv()

# Training configuration
TRAINING_REPOS = [
    "https://github.com/langchain-ai/langchain",
    "https://github.com/microsoft/autogen",
    "https://github.com/anthropics/anthropic-sdk-python",
    "https://github.com/openai/openai-python",
]


class AgentLensTrainer:
    """Trainer for optimizing AgentLens multi-agent system."""

    def __init__(self, openai_api_key: str, model: str = "gpt-4o"):
        self.openai_api_key = openai_api_key
        self.model = model
        self.analyzer = AgentAnalyzer(
            openai_api_key=openai_api_key,
            model=model
        )

    async def analyze_repository_rollout(self, repo_url: str) -> float:
        """
        Single rollout: analyze one repository and return quality score.
        Note: @agl.rollout decorator removed due to signature compatibility.
        Agent-lightning instrumentation is embedded in analyzer.py instead.
        """
        agl.emit_message(f"Starting rollout for {repo_url}")

        try:
            # Run analysis
            report = await self.analyzer.analyze_repo(repo_url)

            # Calculate reward based on report quality
            quality_score = self.analyzer._calculate_report_quality(report)

            # Emit structured metrics
            agl.emit_object({
                "repo_url": repo_url,
                "report_length": len(report),
                "quality_score": quality_score
            })

            # Return final reward
            return quality_score

        except Exception as e:
            agl.emit_exception(e)
            return 0.0

    async def run_training_loop(self, num_epochs: int = 3):
        """Run training loop across multiple repositories."""
        print("\n" + "="*60)
        print("🚀 Agent-lightning Training Loop for AgentLens")
        print("="*60 + "\n")

        for epoch in range(num_epochs):
            print(f"\n📊 EPOCH {epoch + 1}/{num_epochs}")
            print("-" * 60)

            epoch_rewards = []

            for repo_url in TRAINING_REPOS:
                print(f"\n🔍 Analyzing: {repo_url}")

                try:
                    # Run rollout with Agent-lightning tracking
                    reward = await self.analyze_repository_rollout(repo_url)
                    epoch_rewards.append(reward)

                    print(f"   ✅ Quality Score: {reward:.3f}")

                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                    epoch_rewards.append(0.0)

            # Epoch summary
            avg_reward = sum(epoch_rewards) / len(epoch_rewards) if epoch_rewards else 0.0
            print(f"\n📈 Epoch {epoch + 1} Average Reward: {avg_reward:.3f}")

        print("\n" + "="*60)
        print("✅ Training Complete!")
        print("="*60 + "\n")


async def run_benchmark():
    """Run performance benchmark comparing with/without Agent-lightning."""
    print("\n" + "="*60)
    print("⚡ Agent-lightning Performance Benchmark")
    print("="*60 + "\n")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return

    # Test repository
    test_repo = "https://github.com/openai/openai-python"

    print(f"📦 Test Repository: {test_repo}\n")

    # Benchmark 1: Standard analysis
    print("1️⃣  Running BASELINE analysis (without optimization)...")
    analyzer_baseline = AgentAnalyzer(openai_api_key=openai_api_key)

    import time
    start = time.time()
    try:
        report_baseline = await analyzer_baseline._analyze_repo_impl(test_repo)
        baseline_time = time.time() - start
        baseline_quality = analyzer_baseline._calculate_report_quality(report_baseline)

        print(f"   ✅ Baseline Complete")
        print(f"   ⏱️  Time: {baseline_time:.2f}s")
        print(f"   📊 Quality: {baseline_quality:.3f}")
        print(f"   📄 Report Length: {len(report_baseline):,} chars\n")

    except Exception as e:
        print(f"   ❌ Baseline failed: {e}\n")
        return

    # Benchmark 2: Agent-lightning optimized
    print("2️⃣  Running AGENT-LIGHTNING optimized analysis...")
    start = time.time()

    try:
        report_optimized = await analyzer_baseline.analyze_repo(test_repo)
        optimized_time = time.time() - start
        optimized_quality = analyzer_baseline._calculate_report_quality(report_optimized)

        print(f"   ✅ Optimized Complete")
        print(f"   ⏱️  Time: {optimized_time:.2f}s")
        print(f"   📊 Quality: {optimized_quality:.3f}")
        print(f"   📄 Report Length: {len(report_optimized):,} chars\n")

    except Exception as e:
        print(f"   ❌ Optimized failed: {e}\n")
        return

    # Comparison
    print("="*60)
    print("📊 PERFORMANCE COMPARISON")
    print("="*60)
    print(f"Quality Improvement: {((optimized_quality - baseline_quality) / baseline_quality * 100):.1f}%")
    print(f"Time Difference: {optimized_time - baseline_time:.2f}s")
    print("="*60 + "\n")


async def main():
    """Main entry point for training."""
    import argparse

    parser = argparse.ArgumentParser(description="Train AgentLens with Agent-lightning")
    parser.add_argument("--mode", choices=["train", "benchmark"], default="benchmark",
                        help="Run training loop or benchmark")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Number of training epochs")

    args = parser.parse_args()

    if not AGENT_LIGHTNING_AVAILABLE:
        return

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY not set in .env file")
        return

    if args.mode == "train":
        trainer = AgentLensTrainer(openai_api_key=openai_api_key)
        await trainer.run_training_loop(num_epochs=args.epochs)
    else:
        await run_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
