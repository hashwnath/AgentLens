"""
Agent-lightning with LangChain SQLDBToolkit Example
====================================================
Demonstrates how to use Agent-lightning to optimize a SQL agent.
"""

import os
from typing import Dict, Any

try:
    import agentlightning as agl
    from langchain.agents import create_sql_agent
    from langchain_community.agent_toolkits import SQLDatabaseToolkit
    from langchain_community.utilities import SQLDatabase
    from langchain_openai import ChatOpenAI
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install langchain langchain-openai langchain-community")
    exit(1)


class SQLAgentWithLightning:
    """SQL Agent optimized with Agent-lightning."""

    def __init__(self, db_uri: str, model: str = "gpt-4o-mini"):
        # Initialize database
        self.db = SQLDatabase.from_uri(db_uri)

        # Initialize LLM
        self.llm = ChatOpenAI(model=model, temperature=0)

        # Create SQLDBToolkit
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)

        # Create SQL agent
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=True,
            agent_type="openai-tools"
        )

    async def query_with_optimization(self, question: str, expected_result: Any = None) -> Dict[str, Any]:
        """
        Execute SQL query with Agent-lightning instrumentation.

        Args:
            question: Natural language question
            expected_result: Ground truth for reward calculation (optional)

        Returns:
            Dict with result and quality score
        """
        # Emit start of rollout
        agl.emit_message(f"🔍 Processing SQL query: {question}")
        agl.emit_object({"question": question, "db_tables": self.db.get_usable_table_names()})

        try:
            # Execute agent
            result = self.agent.invoke({"input": question})

            # Extract SQL query if available
            sql_query = self._extract_sql_from_result(result)

            # Calculate reward based on execution success and correctness
            reward = self._calculate_reward(result, expected_result, sql_query)

            # Emit reward for RL optimization
            agl.emit_reward(reward)

            # Emit structured output
            agl.emit_object({
                "sql_query": sql_query,
                "result": str(result.get("output", ""))[:200],
                "reward": reward,
                "success": result.get("output") is not None
            })

            agl.emit_message(f"✅ Query complete. Reward: {reward:.3f}")

            return {
                "question": question,
                "sql_query": sql_query,
                "result": result.get("output"),
                "reward": reward
            }

        except Exception as e:
            agl.emit_exception(e)
            agl.emit_reward(0.0)  # Zero reward on failure

            return {
                "question": question,
                "error": str(e),
                "reward": 0.0
            }

    def _extract_sql_from_result(self, result: Dict) -> str:
        """Extract SQL query from agent result."""
        # LangChain SQL agent includes intermediate steps
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if isinstance(step, tuple) and len(step) > 0:
                    action = step[0]
                    if hasattr(action, 'tool_input'):
                        # SQL query is often in tool_input
                        if isinstance(action.tool_input, dict):
                            return action.tool_input.get('query', '')
                        return str(action.tool_input)
        return ""

    def _calculate_reward(self, result: Dict, expected_result: Any, sql_query: str) -> float:
        """
        Calculate reward for RL optimization.

        Reward components:
        - 0.3: Query executed successfully
        - 0.3: Result matches expected (if provided)
        - 0.2: SQL query is valid and non-empty
        - 0.2: No errors in execution
        """
        reward = 0.0

        # Successful execution
        if result.get("output") is not None:
            reward += 0.3

        # SQL query generated
        if sql_query and len(sql_query) > 10:
            reward += 0.2

        # No errors
        if "error" not in str(result.get("output", "")).lower():
            reward += 0.2

        # Correctness (if ground truth provided)
        if expected_result is not None:
            output = result.get("output", "")
            if self._compare_results(output, expected_result):
                reward += 0.3

        return min(1.0, reward)

    def _compare_results(self, actual: Any, expected: Any) -> bool:
        """Compare actual vs expected results."""
        # Simple string comparison (can be made more sophisticated)
        return str(actual).strip().lower() == str(expected).strip().lower()


# ============================================================================
# Training Example with Spider Dataset
# ============================================================================

async def train_sql_agent():
    """
    Training loop for SQL agent optimization.
    Based on Agent-lightning's Spider dataset example.
    """
    print("\n" + "="*60)
    print("🚀 Agent-lightning SQL Agent Training")
    print("="*60 + "\n")

    # Example dataset (replace with actual Spider dataset)
    training_data = [
        {
            "question": "How many employees are there?",
            "db": "sqlite:///example.db",
            "expected": "150"
        },
        {
            "question": "What is the average salary in the Engineering department?",
            "db": "sqlite:///example.db",
            "expected": "95000"
        },
        {
            "question": "List all customers who made purchases in 2024",
            "db": "sqlite:///example.db",
            "expected": None  # No ground truth
        }
    ]

    total_rewards = []

    for idx, sample in enumerate(training_data, 1):
        print(f"\n📝 Sample {idx}/{len(training_data)}")
        print(f"   Question: {sample['question']}")

        # Initialize agent for this database
        agent = SQLAgentWithLightning(
            db_uri=sample["db"],
            model="gpt-4o-mini"
        )

        # Run query with optimization
        result = await agent.query_with_optimization(
            question=sample["question"],
            expected_result=sample.get("expected")
        )

        total_rewards.append(result["reward"])
        print(f"   SQL: {result.get('sql_query', 'N/A')}")
        print(f"   Reward: {result['reward']:.3f}")

    # Training summary
    avg_reward = sum(total_rewards) / len(total_rewards)
    print("\n" + "="*60)
    print(f"📊 Training Complete - Average Reward: {avg_reward:.3f}")
    print("="*60 + "\n")


# ============================================================================
# Simple Usage Example
# ============================================================================

async def simple_example():
    """Simple example of using SQL agent with Agent-lightning."""

    # Create SQL agent
    agent = SQLAgentWithLightning(
        db_uri="sqlite:///chinook.db",  # Example SQLite database
        model="gpt-4o-mini"
    )

    # Query with optimization
    result = await agent.query_with_optimization(
        question="How many albums are in the database?",
        expected_result="347"  # Optional ground truth
    )

    print(f"\nResult: {result['result']}")
    print(f"SQL Query: {result['sql_query']}")
    print(f"Reward: {result['reward']:.3f}")


if __name__ == "__main__":
    import asyncio

    # Run simple example
    # asyncio.run(simple_example())

    # Run training
    # asyncio.run(train_sql_agent())

    print("""
Agent-lightning SQL Agent Example
==================================

This example shows how to optimize LangChain SQLDBToolkit agents.

Usage:
1. Install dependencies:
   pip install langchain langchain-openai langchain-community agentlightning

2. Run simple example:
   asyncio.run(simple_example())

3. Run training loop:
   asyncio.run(train_sql_agent())

For the official Spider dataset example, see:
https://github.com/microsoft/agent-lightning/tree/main/examples/spider
    """)
