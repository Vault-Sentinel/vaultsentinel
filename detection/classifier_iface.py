"""Interface for pluggable ML/LLM classifiers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Iterable
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Result from a classifier."""
    confidence: float
    label: str
    reasoning: str = ""


class SecretClassifier(ABC):
    """Abstract base class for secret classifiers."""
    
    @abstractmethod
    def classify(self, text: str, context: Dict) -> ClassificationResult:
        """Classify a potential secret.
        
        Args:
            text: The text to classify
            context: Additional context (file path, line content, etc.)
            
        Returns:
            Classification result with confidence and label
        """
        pass


class RuleBasedClassifier(SecretClassifier):
    """Rule-based fallback classifier."""
    
    def __init__(self):
        """Initialize rule-based classifier."""
        self.rules = {
            "high_confidence": [
                "aws_access_key",
                "aws_secret_key", 
                "slack_webhook",
                "github_token",
                "rsa_private_key"
            ],
            "medium_confidence": [
                "bearer_token",
                "jwt_token",
                "postgres_url",
                "mysql_url",
                "mongodb_url"
            ],
            "low_confidence": [
                "generic_token",
                "api_key",
                "password"
            ]
        }
    
    def classify(self, text: str, context: Dict) -> ClassificationResult:
        """Classify using rule-based approach."""
        secret_kind = context.get("secret_kind", "unknown")
        file_path = context.get("file_path", "")
        line_content = context.get("line_content", "")
        
        # Base confidence from secret kind
        if secret_kind in self.rules["high_confidence"]:
            confidence = 0.9
        elif secret_kind in self.rules["medium_confidence"]:
            confidence = 0.7
        elif secret_kind in self.rules["low_confidence"]:
            confidence = 0.5
        else:
            confidence = 0.3
        
        # Adjust based on context
        if "/test" in file_path.lower():
            confidence *= 0.5
        if "example" in line_content.lower():
            confidence *= 0.3
        if "config" in file_path.lower():
            confidence *= 1.2
        
        # Cap confidence
        confidence = min(1.0, max(0.0, confidence))
        
        return ClassificationResult(
            confidence=confidence,
            label=secret_kind,
            reasoning=f"Rule-based classification for {secret_kind}"
        )


class MLClassifier(SecretClassifier):
    """ML-based classifier (placeholder for future implementation)."""
    
    def __init__(self, model_path: str = None):
        """Initialize ML classifier."""
        self.model_path = model_path
        self.model = None
        # TODO: Load ML model when implemented
    
    def classify(self, text: str, context: Dict) -> ClassificationResult:
        """Classify using ML model."""
        # TODO: Implement ML-based classification
        # For now, fall back to rule-based
        rule_classifier = RuleBasedClassifier()
        return rule_classifier.classify(text, context)


class LLMClassifier(SecretClassifier):
    """LLM-based classifier using MCP (Model Context Protocol) client."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo", provider: str = "openai"):
        """Initialize LLM classifier."""
        self.name = f"llm_{provider}_{model}"
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.mcp_client = None
        
        # Import MCP client
        try:
            from api.clients import get_mcp_client
            self.mcp_client = get_mcp_client()
        except ImportError as e:
            print(f"Warning: MCP client not available: {e}")
            print("Falling back to rule-based classifier")
    
    def classify(self, text: str, context: Dict) -> ClassificationResult:
        """Classify using LLM via MCP client."""
        if not self.mcp_client:
            # Fall back to rule-based if no MCP client
            rule_classifier = RuleBasedClassifier()
            return rule_classifier.classify(text, context)
        
        try:
            import asyncio
            # Run async MCP call in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._classify_with_mcp(text, context))
            finally:
                loop.close()
        except Exception as e:
            print(f"LLM classification error: {e}")
            # Fall back to rule-based
            rule_classifier = RuleBasedClassifier()
            return rule_classifier.classify(text, context)
    
    async def _classify_with_mcp(self, text: str, context: Dict) -> ClassificationResult:
        """Classify using MCP client."""
        prompt = self._build_prompt(text, context)
        
        # Build conversation for MCP chat endpoint
        conversation = {
            "messages": [
                {"role": "system", "content": "You are a security expert analyzing potential secrets. Respond with JSON only."},
                {"role": "user", "content": prompt}
            ],
            "model": self.model,
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        # Use MCP client for chat completion
        response = await self.mcp_client.chat(conversation)
        
        if response["status"] == "ok" and response["result"]:
            # Extract text from MCP response
            if isinstance(response["result"], list) and len(response["result"]) > 0:
                result_text = response["result"][0].get("text", "")
            elif isinstance(response["result"], dict):
                result_text = response["result"].get("text", "")
            else:
                result_text = str(response["result"])
            
            return self._parse_llm_response(result_text)
        else:
            # MCP request failed, fall back to rule-based
            rule_classifier = RuleBasedClassifier()
            return rule_classifier.classify(text, context)
    
    def _build_prompt(self, text: str, context: Dict) -> str:
        """Build prompt for LLM classification."""
        file_path = context.get("file_path", "unknown")
        secret_kind = context.get("secret_kind", "unknown")
        
        return f"""
Analyze this potential secret and determine if it's a real security risk.

Text: "{text}"
File: {file_path}
Detected as: {secret_kind}

Consider:
1. Is this a real secret or a placeholder/example?
2. What's the confidence level (0.0-1.0)?
3. What type of secret is it?

Respond with JSON:
{{
    "is_secret": true/false,
    "confidence": 0.0-1.0,
    "secret_type": "aws_access_key|github_token|etc",
    "reasoning": "brief explanation"
}}
"""
    
    def _parse_llm_response(self, response: str) -> ClassificationResult:
        """Parse LLM response."""
        try:
            import json
            result = json.loads(response.strip())
            
            return ClassificationResult(
                confidence=float(result.get("confidence", 0.5)),
                label=result.get("secret_type", "unknown"),
                reasoning=result.get("reasoning", "LLM analysis")
            )
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return ClassificationResult(
                confidence=0.5,
                label="unknown",
                reasoning="LLM parsing error"
            )
    
    def detect(self, context) -> Iterable:
        """Detect secrets using LLM classification."""
        # This is a classifier, not a detector, so we don't implement detection
        # The LLM classifier is used by other detectors for classification
        return []
    
    def is_enabled(self) -> bool:
        """Check if the LLM classifier is enabled."""
        return self.mcp_client is not None


def get_classifier(classifier_type: str = "rule", **kwargs) -> SecretClassifier:
    """Get a classifier instance.
    
    Args:
        classifier_type: Type of classifier ("rule", "ml", "llm")
        **kwargs: Additional arguments for classifier initialization
        
    Returns:
        Classifier instance
    """
    if classifier_type == "rule":
        return RuleBasedClassifier()
    elif classifier_type == "ml":
        return MLClassifier(**kwargs)
    elif classifier_type == "llm":
        return LLMClassifier(**kwargs)
    else:
        raise ValueError(f"Unknown classifier type: {classifier_type}")
