#!/usr/bin/env python3
"""Interactive LLM configuration helper for VaultSentinel."""

import os
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

def main():
    """Interactive LLM configuration."""
    print("🤖 VaultSentinel LLM Configuration Helper")
    print("=" * 50)
    
    # Check if .env exists
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found. Please run: cp env.example .env")
        return
    
    print("\n📋 Available LLM Providers:")
    print("1. OpenAI (GPT models)")
    print("2. Google Gemini")
    print("3. Both (use both providers)")
    print("4. None (disable LLM classifiers)")
    
    choice = input("\nSelect provider (1-4): ").strip()
    
    if choice == "4":
        # Disable LLM
        update_env_file(env_path, {
            "LLM_CLASSIFIER_ENABLED": "false"
        })
        print("✅ LLM classifiers disabled")
        return
    
    # Get provider choice
    if choice == "1":
        provider = "openai"
    elif choice == "2":
        provider = "gemini"
    elif choice == "3":
        provider = "both"
    else:
        print("❌ Invalid choice")
        return
    
    # Configure OpenAI if needed
    if provider in ["openai", "both"]:
        print("\n🤖 OpenAI Configuration:")
        openai_key = input("Enter OpenAI API key (or press Enter to skip): ").strip()
        if openai_key:
            print("\nAvailable OpenAI models:")
            print("1. gpt-3.5-turbo (fast, cost-effective)")
            print("2. gpt-4 (more accurate, slower)")
            print("3. gpt-4-turbo (balanced)")
            
            model_choice = input("Select model (1-3): ").strip()
            if model_choice == "1":
                openai_model = "gpt-3.5-turbo"
            elif model_choice == "2":
                openai_model = "gpt-4"
            elif model_choice == "3":
                openai_model = "gpt-4-turbo"
            else:
                openai_model = "gpt-3.5-turbo"
        else:
            openai_key = "your_openai_api_key_here"
            openai_model = "gpt-3.5-turbo"
    else:
        openai_key = "your_openai_api_key_here"
        openai_model = "gpt-3.5-turbo"
    
    # Configure Gemini if needed
    if provider in ["gemini", "both"]:
        print("\n🧠 Gemini Configuration:")
        gemini_key = input("Enter Gemini API key (or press Enter to skip): ").strip()
        if gemini_key:
            print("\nAvailable Gemini models:")
            print("1. gemini-1.5-flash (fast, cost-effective)")
            print("2. gemini-1.5-pro (more accurate, slower)")
            
            model_choice = input("Select model (1-2): ").strip()
            if model_choice == "2":
                gemini_model = "gemini-1.5-pro"
            else:
                gemini_model = "gemini-1.5-flash"
        else:
            gemini_key = "your_gemini_api_key_here"
            gemini_model = "gemini-1.5-flash"
    else:
        gemini_key = "your_gemini_api_key_here"
        gemini_model = "gemini-1.5-flash"
    
    # Get confidence threshold
    print("\n🎯 LLM Confidence Threshold:")
    print("This determines how confident the LLM must be to classify something as a secret.")
    print("0.5 = lenient, 0.7 = balanced, 0.9 = strict")
    confidence = input("Enter confidence threshold (0.5-0.9, default 0.7): ").strip()
    if not confidence:
        confidence = "0.7"
    
    # Update .env file
    updates = {
        "LLM_CLASSIFIER_ENABLED": "true",
        "LLM_PROVIDER": provider,
        "OPENAI_API_KEY": openai_key,
        "GEMINI_API_KEY": gemini_key,
        "OPENAI_MODEL": openai_model,
        "GEMINI_MODEL": gemini_model,
        "LLM_CONFIDENCE_THRESHOLD": confidence
    }
    
    update_env_file(env_path, updates)
    
    print("\n✅ Configuration updated!")
    print(f"Provider: {provider}")
    if provider in ["openai", "both"]:
        print(f"OpenAI Model: {openai_model}")
    if provider in ["gemini", "both"]:
        print(f"Gemini Model: {gemini_model}")
    print(f"Confidence Threshold: {confidence}")
    
    print("\n🚀 To test your configuration:")
    print("python test_llm_classifiers.py")

def update_env_file(env_path: Path, updates: dict):
    """Update .env file with new values."""
    # Read existing .env file
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update or add lines
    updated_keys = set()
    for i, line in enumerate(lines):
        for key, value in updates.items():
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                updated_keys.add(key)
                break
    
    # Add new lines for keys not found
    for key, value in updates.items():
        if key not in updated_keys:
            lines.append(f"{key}={value}\n")
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    main()
