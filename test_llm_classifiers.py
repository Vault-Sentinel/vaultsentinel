#!/usr/bin/env python3
"""Test script for LLM classifiers in VaultSentinel."""

import os
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from detection.classifier_iface import LLMClassifier, RuleBasedClassifier
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_classifiers():
    """Test different classifiers on sample secrets."""
    
    # Sample test cases
    test_cases = [
        {
            "text": "AKIA1234567890ABCDEF",
            "context": {"file_path": "config.py", "secret_kind": "aws_access_key", "line_content": "AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF"},
            "expected": "Real AWS key"
        },
        {
            "text": "AKIA0000000000000000",
            "context": {"file_path": "test_config.py", "secret_kind": "aws_access_key", "line_content": "TEST_AWS_KEY=AKIA0000000000000000"},
            "expected": "Test/placeholder key"
        },
        {
            "text": "ghp_1234567890abcdef1234567890abcdef12345678",
            "context": {"file_path": "secrets.json", "secret_kind": "github_token", "line_content": '"github_token": "ghp_1234567890abcdef1234567890abcdef12345678"'},
            "expected": "Real GitHub token"
        },
        {
            "text": "your_github_token_here",
            "context": {"file_path": "example.py", "secret_kind": "github_token", "line_content": "token = 'your_github_token_here'"},
            "expected": "Placeholder text"
        },
        {
            "text": "https://hooks.slack.com/services/T123/B456/xyz789",
            "context": {"file_path": "config.yaml", "secret_kind": "slack_webhook", "line_content": "webhook_url: https://hooks.slack.com/services/T123/B456/xyz789"},
            "expected": "Real Slack webhook"
        },
        {
            "text": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            "context": {"file_path": "README.md", "secret_kind": "slack_webhook", "line_content": "webhook_url: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"},
            "expected": "Example webhook"
        }
    ]
    
    print("🧪 Testing VaultSentinel Classifiers")
    print("=" * 50)
    
    # Test rule-based classifier
    print("\n📋 Rule-Based Classifier:")
    rule_classifier = RuleBasedClassifier()
    for i, case in enumerate(test_cases, 1):
        result = rule_classifier.classify(case["text"], case["context"])
        print(f"  {i}. {case['text'][:20]}... -> {result.confidence:.2f} confidence, {result.label}")
    
    # Test OpenAI classifier if API key is available
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    if openai_key and openai_key != "your_openai_api_key_here":
        print(f"\n🤖 OpenAI Classifier ({openai_model}):")
        openai_classifier = LLMClassifier(
            api_key=openai_key,
            model=openai_model,
            provider="openai"
        )
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. Testing: {case['text'][:20]}...")
            result = openai_classifier.classify(case["text"], case["context"])
            print(f"     -> {result.confidence:.2f} confidence, {result.label}")
            print(f"     -> Reasoning: {result.reasoning}")
    else:
        print("\n🤖 OpenAI Classifier: SKIPPED (no API key)")
    
    # Test Gemini classifier if API key is available
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        print(f"\n🧠 Gemini Classifier ({gemini_model}):")
        gemini_classifier = LLMClassifier(
            api_key=gemini_key,
            model=gemini_model,
            provider="gemini"
        )
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. Testing: {case['text'][:20]}...")
            result = gemini_classifier.classify(case["text"], case["context"])
            print(f"     -> {result.confidence:.2f} confidence, {result.label}")
            print(f"     -> Reasoning: {result.reasoning}")
    else:
        print("\n🧠 Gemini Classifier: SKIPPED (no API key)")
    
    print("\n✅ Test completed!")
    print("\nTo run with your API keys:")
    print("1. Set OPENAI_API_KEY in your .env file")
    print("2. Set GEMINI_API_KEY in your .env file")
    print("3. Run: python test_llm_classifiers.py")

if __name__ == "__main__":
    test_classifiers()
