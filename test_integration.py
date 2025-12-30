#!/usr/bin/env python3
"""
Integration Test for Agent-lightning
=====================================
Validates that Agent-lightning is properly integrated with AgentLens.
"""

import sys


def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")

    try:
        import agentlightning as agl
        print("   ✅ agentlightning imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import agentlightning: {e}")
        print("   💡 Install with: pip install agentlightning")
        return False

    try:
        from analyzer import AgentAnalyzer, AGENT_LIGHTNING_ENABLED
        print(f"   ✅ AgentAnalyzer imported (Agent-lightning: {'enabled' if AGENT_LIGHTNING_ENABLED else 'disabled'})")

        if not AGENT_LIGHTNING_ENABLED:
            print("   ⚠️  Agent-lightning is disabled in analyzer.py")
            return False

    except ImportError as e:
        print(f"   ❌ Failed to import analyzer: {e}")
        return False

    return True


def test_analyzer_methods():
    """Test that analyzer has Agent-lightning methods."""
    print("\n🔍 Testing analyzer methods...")

    try:
        from analyzer import AgentAnalyzer

        # Check for new methods
        required_methods = [
            '_analyze_repo_with_lightning',
            '_calculate_report_quality'
        ]

        for method in required_methods:
            if hasattr(AgentAnalyzer, method):
                print(f"   ✅ {method} exists")
            else:
                print(f"   ❌ {method} missing")
                return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    return True


def test_quality_scoring():
    """Test the quality scoring function."""
    print("\n🔍 Testing quality scoring...")

    try:
        from analyzer import AgentAnalyzer

        analyzer = AgentAnalyzer(
            openai_api_key="test-key",
            model="gpt-4o"
        )

        # Test with a sample report
        sample_report = """
# AgentLens Analysis Report

## Executive Summary
- Overall Score: 85/100
- Critical Issues: 2

## 🔴 Critical Findings
1. Exposed API key in config.py

## 🟡 Warnings
1. Missing error handling

## 🟢 Strengths
1. Good code structure

## Recommendations
Use environment variables for API keys

```python
import os
api_key = os.getenv("API_KEY")
```

## Best Practices
Follows security best practices
"""

        score = analyzer._calculate_report_quality(sample_report)
        print(f"   ✅ Quality score calculated: {score:.3f}")

        if 0.0 <= score <= 1.0:
            print(f"   ✅ Score is valid (0.0-1.0 range)")
        else:
            print(f"   ❌ Score out of range: {score}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    return True


def test_training_script():
    """Test that training script exists and can be imported."""
    print("\n🔍 Testing training script...")

    try:
        import train_agent
        print("   ✅ train_agent.py can be imported")

        if hasattr(train_agent, 'AgentLensTrainer'):
            print("   ✅ AgentLensTrainer class exists")
        else:
            print("   ❌ AgentLensTrainer class missing")
            return False

        if hasattr(train_agent, 'run_benchmark'):
            print("   ✅ run_benchmark function exists")
        else:
            print("   ❌ run_benchmark function missing")
            return False

    except ImportError as e:
        print(f"   ❌ Failed to import train_agent: {e}")
        return False

    return True


def test_emit_functions():
    """Test that agl.emit functions are available."""
    print("\n🔍 Testing Agent-lightning emit functions...")

    try:
        import agentlightning as agl

        emit_functions = [
            'emit_message',
            'emit_object',
            'emit_reward',
            'emit_exception'
        ]

        for func in emit_functions:
            if hasattr(agl, func):
                print(f"   ✅ agl.{func} available")
            else:
                print(f"   ⚠️  agl.{func} not found (may be version-specific)")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("="*60)
    print("⚡ Agent-lightning Integration Test Suite")
    print("="*60 + "\n")

    tests = [
        test_imports,
        test_analyzer_methods,
        test_quality_scoring,
        test_training_script,
        test_emit_functions
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "="*60)
    print("📊 Test Results")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed! Agent-lightning integration is ready.")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
