"""Main entry point for VaultSentinel."""

import argparse
import logging
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from core.agent import VaultSentinelAgent
from core.interfaces import get_registry
from connectors.github_connector import GitHubConnector
from detectors.regex_detector import RegexDetector
from detectors.entropy_detector import EntropyDetector
from detection.classifier_iface import LLMClassifier
from remediation.slack_notifier import SlackNotifier
from remediation.aws_remediation import AWSRemediationHandler
from api.app import create_app
import uvicorn

def register_plugins():
    """Register all plugins with the registry."""
    registry = get_registry()
    
    # Register connectors
    registry.register_connector(GitHubConnector())
    
    # Register detectors
    registry.register_detector(RegexDetector())
    registry.register_detector(EntropyDetector())
    
    # Register LLM classifiers based on configuration
    from core.config import get_config
    config = get_config()
    
    if config.llm_classifier_enabled:
        if config.llm_provider in ["openai", "both"] and config.openai_api_key and config.openai_api_key != "your_openai_api_key_here":
            print(f"🤖 Registering OpenAI classifier ({config.openai_model})...")
            openai_classifier = LLMClassifier(
                api_key=config.openai_api_key,
                model=config.openai_model,
                provider="openai"
            )
            registry.register_detector(openai_classifier)
        
        if config.llm_provider in ["gemini", "both"] and config.gemini_api_key and config.gemini_api_key != "your_gemini_api_key_here":
            print(f"🧠 Registering Gemini classifier ({config.gemini_model})...")
            gemini_classifier = LLMClassifier(
                api_key=config.gemini_api_key,
                model=config.gemini_model,
                provider="gemini"
            )
            registry.register_detector(gemini_classifier)
    
    # Register remediation handlers
    registry.register_remediation_handler(SlackNotifier())
    registry.register_remediation_handler(AWSRemediationHandler())

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="VaultSentinel - Continuous Secrets Shielding")
    parser.add_argument("--run-once", action="store_true", help="Run a single scan cycle")
    parser.add_argument("--test-connections", action="store_true", help="Test external connections")
    parser.add_argument("--api-only", action="store_true", help="Run API server only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register plugins
    register_plugins()
    
    try:
        if args.api_only:
            print("Starting API server...")
            app = create_app()
            uvicorn.run(app, host=args.host, port=args.port)
        else:
            # Initialize agent
            agent = VaultSentinelAgent()
            
            if args.test_connections:
                print("Testing connections...")
                agent._test_connections()
                print("All connections successful!")
                return
            
            if args.run_once:
                print("Running single scan cycle...")
                results = agent.run_once()
                print(f"Scan completed: {results}")
            else:
                print("Starting VaultSentinel agent...")
                agent.start()
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())