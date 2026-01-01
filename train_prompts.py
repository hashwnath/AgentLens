"""
AgentLens - Automatic Prompt Optimization (APO) Training Script
================================================================
Uses Microsoft Agent Lightning to optimize agent prompts automatically.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, TypedDict

import agentlightning as agl
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Directory for saved prompts
PROMPTS_DIR = Path("prompts")
PROMPTS_DIR.mkdir(exist_ok=True)

# Initial prompt for code analysis
INITIAL_PROMPT = """You are an expert AI code reviewer that analyzes AI agent codebases.

Analyze the provided code and identify:
1. Frameworks used (LangChain, AutoGen, OpenAI, etc.)
2. Anti-patterns and issues
3. Best practices compliance
4. Optimization opportunities

Code to analyze:
{code}

Provide a structured analysis with:
- Overall score (0-100)
- Key findings
- Recommendations"""


# Task structure for training
class AnalysisTask(TypedDict):
    code: str
    expected_score: int
    notes: str


# Sample training data
TRAINING_DATA = [
    {
        "code": """
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

llm = OpenAI(api_key="sk-1234567890")  # Hardcoded key!

prompt = PromptTemplate(template="Answer: {question}")
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run("What is AI?")
print(result)
""",
        "expected_score": 30,
        "notes": "Has exposed API key, uses deprecated LLMChain, no error handling"
    },
    {
        "code": """
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{question}")
])
chain = prompt | llm | StrOutputParser()

try:
    result = chain.invoke({"question": "What is AI?"})
    print(result)
except Exception as e:
    logging.error(f"LLM call failed: {e}")
""",
        "expected_score": 85,
        "notes": "Uses LCEL, env vars for keys, has error handling"
    },
]


def score_analysis(analysis: str, expected_score: int) -> float:
    """Score the analysis quality by comparing to expected score."""
    # Extract score from analysis if present
    import re
    score_match = re.search(r'(\d+)/100|score[:\s]+(\d+)', analysis.lower())
    if score_match:
        found_score = int(score_match.group(1) or score_match.group(2))
        # Reward accuracy: higher reward if closer to expected
        diff = abs(found_score - expected_score)
        reward = max(0.0, 1.0 - (diff / 100))
    else:
        reward = 0.3  # Partial reward if no score found
    
    # Bonus for mentioning key issues
    bonus = 0.0
    if "api key" in analysis.lower() or "hardcoded" in analysis.lower():
        bonus += 0.1
    if "error handling" in analysis.lower():
        bonus += 0.1
    if "lcel" in analysis.lower() or "expression language" in analysis.lower():
        bonus += 0.1
    
    return min(1.0, reward + bonus)


@agl.rollout
def analyze_code(task: AnalysisTask, prompt_template: agl.PromptTemplate) -> float:
    """
    Agent rollout function for code analysis.
    
    This is automatically called by the trainer with:
    - task: The current training task
    - prompt_template: The (optimizing) prompt template resource
    """
    client = OpenAI()
    
    # Format prompt with task data
    prompt = prompt_template.format(code=task["code"])
    
    # Call LLM to analyze the code
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use mini for training efficiency
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    analysis = response.choices[0].message.content
    print(f"\n📝 Analysis preview: {analysis[:200]}...")
    
    # Score the analysis
    reward = score_analysis(analysis, task["expected_score"])
    print(f"🎯 Reward: {reward:.2f}")
    
    return reward


def save_optimized_prompts(resources: dict[str, Any]):
    """Save optimized prompts to disk."""
    for name, resource in resources.items():
        if hasattr(resource, 'template'):
            path = PROMPTS_DIR / f"{name}.txt"
            path.write_text(resource.template)
            print(f"✅ Saved optimized prompt: {path}")


def run_training(n_epochs: int = 3, n_runners: int = 2):
    """Run APO training to optimize agent prompts."""
    print("\n🔍 AgentLens - Automatic Prompt Optimization")
    print("=" * 50)
    
    # Create APO algorithm with AsyncOpenAI (required for gradient computation)
    from openai import AsyncOpenAI
    algo = agl.APO(AsyncOpenAI())
    
    # Use shared memory strategy to avoid pickle issues with multiprocessing
    strategy = agl.SharedMemoryExecutionStrategy(n_runners=n_runners)
    
    # Create trainer with initial prompt
    trainer = agl.Trainer(
        algorithm=algo,
        strategy=strategy,
        adapter=agl.TraceToMessages(),
        initial_resources={
            "prompt_template": agl.PromptTemplate(
                template=INITIAL_PROMPT,
                engine="f-string"
            )
        },
    )
    
    print(f"\n📊 Training Configuration:")
    print(f"   - Epochs: {n_epochs}")
    print(f"   - Parallel runners: {n_runners}")
    print(f"   - Training samples: {len(TRAINING_DATA)}")
    
    # Prepare datasets
    train_dataset = [AnalysisTask(**d) for d in TRAINING_DATA]
    val_dataset = train_dataset[:1]  # Use first sample for validation
    
    print(f"\n🚀 Starting APO training...")
    
    try:
        # Run training
        trainer.fit(
            agent=analyze_code,
            train_dataset=train_dataset,
            val_dataset=val_dataset,
        )
        
        # Save optimized prompts
        print("\n💾 Saving optimized prompts...")
        final_resources = trainer.get_resources()
        save_optimized_prompts(final_resources)
        
        print("\n✅ Training complete!")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentLens APO Training")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--runners", type=int, default=2, help="Number of parallel runners")
    args = parser.parse_args()
    
    run_training(n_epochs=args.epochs, n_runners=args.runners)


if __name__ == "__main__":
    main()
