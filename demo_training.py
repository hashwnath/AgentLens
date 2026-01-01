"""
AgentLens - Agent Lightning Full Demo
=====================================
Demonstrates full Agent Lightning integration with:
- agl.emit_reward() for multi-dimensional rewards
- agl.emit_message() for logging
- agl.operation() for span tracking
- AgentOps for visualization

Run with: python demo_training.py
"""

import os
from typing import TypedDict

import agentlightning as agl
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize AgentOps for tracing
import agentops
agentops.init(api_key=os.getenv("AGENTOPS_API_KEY"))

print("""
╔══════════════════════════════════════════════════════════════╗
║      🔍 AgentLens + ⚡ Agent Lightning Demo                   ║
║                                                              ║
║  Automatic Prompt Optimization (APO) for Code Analysis      ║
╚══════════════════════════════════════════════════════════════╝
""")

# Initial prompt for code analysis
INITIAL_PROMPT = """You are an AI code reviewer. Analyze the code below.

Provide:
1. Overall score (0-100)
2. Key issues found
3. Recommendations

Code:
{code}"""


class AnalysisTask(TypedDict):
    code: str
    expected_score: int
    label: str


# Sample training data - clearly bad vs good code
TRAINING_DATA = [
    {
        "code": """
# BAD CODE EXAMPLE
from langchain.llms import OpenAI
api_key = "sk-1234567890abcdef"  # EXPOSED KEY!
llm = OpenAI(api_key=api_key)
result = llm("Hello")
print(result)
""",
        "expected_score": 30,
        "label": "⚠️ BAD CODE"
    },
    {
        "code": """
# GOOD CODE EXAMPLE  
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY")
)

try:
    result = llm.invoke("Hello")
    print(result)
except Exception as e:
    print(f"Error: {e}")
""",
        "expected_score": 85,
        "label": "✅ GOOD CODE"
    },
]


@agl.rollout
def analyze_code(task: AnalysisTask, prompt_template: agl.PromptTemplate) -> float:
    """
    Rollout function with full Agent Lightning tracking.
    """
    print(f"\n{'='*60}")
    print(f"📋 Analyzing: {task['label']}")
    print(f"{'='*60}")
    
    client = OpenAI()
    
    # Format prompt with task data
    prompt = prompt_template.format(code=task["code"])
    
    # Emit a message showing the analysis is starting
    agl.emit_message(f"Starting analysis of {task['label']}")
    
    # Call LLM with operation span tracking
    with agl.operation(name="llm_analysis"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        analysis = response.choices[0].message.content
    
    # Show analysis preview
    preview = analysis[:300].replace('\n', ' ')
    print(f"📝 Analysis: {preview}...")
    
    # Extract score from response
    import re
    score_match = re.search(r'(\d+)/100|score[:\s]+(\d+)', analysis.lower())
    extracted_score = 50
    if score_match:
        extracted_score = int(score_match.group(1) or score_match.group(2))
    
    print(f"📊 Extracted Score: {extracted_score}/100 (Expected: {task['expected_score']})")
    
    # Calculate reward based on accuracy
    accuracy_diff = abs(extracted_score - task["expected_score"])
    accuracy_reward = max(0.0, 1.0 - (accuracy_diff / 100))
    
    # Check for key issue detection
    detection_reward = 0.0
    if "api key" in analysis.lower() or "exposed" in analysis.lower() or "hardcoded" in analysis.lower():
        detection_reward += 0.2
        print("🔍 Detected: API key issue")
    if "error handling" in analysis.lower() or "try" in analysis.lower():
        detection_reward += 0.1
        print("🔍 Detected: Error handling")
    
    # Emit multi-dimensional reward
    total_reward = min(1.0, accuracy_reward + detection_reward)
    
    agl.emit_reward({
        "accuracy": accuracy_reward,
        "detection": detection_reward,
        "total": total_reward
    }, primary_key="total")
    
    print(f"🎯 Rewards: accuracy={accuracy_reward:.2f}, detection={detection_reward:.2f}, total={total_reward:.2f}")
    
    # Emit final message
    agl.emit_message(f"Analysis complete: score={extracted_score}, reward={total_reward:.2f}")
    
    return total_reward


def run_demo():
    """Run a simplified demo for recording."""
    print("⚙️  Initializing Agent Lightning...")
    
    # Create APO with simplified config for faster demo
    algo = agl.APO(AsyncOpenAI())
    
    # Use shared memory strategy
    strategy = agl.SharedMemoryExecutionStrategy(n_runners=1)
    
    # Create trainer
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
    
    print("""
📊 Training Configuration:
   ├─ Algorithm: APO (Automatic Prompt Optimization)
   ├─ Beam Width: 1
   ├─ Branches: 1
   └─ Training Samples: 2
    """)
    
    # Prepare datasets
    train_dataset = [AnalysisTask(**d) for d in TRAINING_DATA]
    val_dataset = train_dataset[:1]
    
    print("🚀 Starting APO Training...\n")
    print("   Watch the AgentOps dashboard for live traces!")
    print("   https://app.agentops.ai/sessions\n")
    
    try:
        trainer.fit(
            agent=analyze_code,
            train_dataset=train_dataset,
            val_dataset=val_dataset,
        )
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        
        # Get optimized prompt
        resources = trainer.get_resources()
        if "prompt_template" in resources:
            print("\n📝 Optimized Prompt:")
            print("-"*40)
            print(resources["prompt_template"].template[:500])
            print("-"*40)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()
