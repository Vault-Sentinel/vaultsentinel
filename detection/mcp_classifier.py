"""MCP-based LLM classifier for secret detection."""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from api.clients.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of MCP classification."""
    is_secret: bool
    is_vulnerability: bool
    type: str
    severity: str
    confidence: float
    remediation: str
    reasoning: str


class MCPClassifier:
    """MCP-based LLM classifier."""
    
    def __init__(self):
        """Initialize MCP classifier."""
        self.mcp_client = get_mcp_client()
    
    async def classify_candidates(self, candidates: List[Dict[str, Any]]) -> List[ClassificationResult]:
        """Classify multiple candidates in batch."""
        results = []
        
        # Process in batches to avoid overwhelming the MCP server
        batch_size = 5
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            batch_results = await self._classify_batch(batch)
            results.extend(batch_results)
        
        return results
    
    async def _classify_batch(self, candidates: List[Dict[str, Any]]) -> List[ClassificationResult]:
        """Classify a batch of candidates."""
        try:
            # Build classification prompt
            prompt = self._build_classification_prompt(candidates)
            
            # Call MCP
            conversation = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a security expert analyzing code for secrets and vulnerabilities. Respond with JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "provider": "gemini"
            }
            
            response = await self.mcp_client.chat(conversation)
            
            if response.get("status") == "ok" and response.get("result"):
                return self._parse_classification_response(response["result"], candidates)
            else:
                logger.error(f"MCP classification failed: {response}")
                return self._create_fallback_results(candidates)
                
        except Exception as e:
            logger.error(f"MCP classification error: {e}")
            return self._create_fallback_results(candidates)
    
    def _build_classification_prompt(self, candidates: List[Dict[str, Any]]) -> str:
        """Build classification prompt for MCP."""
        prompt = "Analyze these code snippets for secrets and vulnerabilities. For each snippet, determine:\n"
        prompt += "1. Is this a real secret or vulnerability? (true/false)\n"
        prompt += "2. What type is it? (aws_access_key, github_token, password, etc.)\n"
        prompt += "3. Severity level (CRITICAL, HIGH, MEDIUM, LOW)\n"
        prompt += "4. Confidence (0.0-1.0)\n"
        prompt += "5. Brief remediation advice\n"
        prompt += "6. Reasoning\n\n"
        
        for i, candidate in enumerate(candidates):
            prompt += f"Candidate {i+1}:\n"
            prompt += f"File: {candidate.get('file_path', 'unknown')}\n"
            prompt += f"Line: {candidate.get('start_line', 'unknown')}\n"
            prompt += f"Context: {candidate.get('context', '')}\n"
            prompt += f"Snippet: {candidate.get('snippet', '')}\n\n"
        
        prompt += "Respond with JSON array format:\n"
        prompt += """[
  {
    "candidate_index": 0,
    "is_secret": true,
    "is_vulnerability": false,
    "type": "aws_access_key",
    "severity": "HIGH",
    "confidence": 0.9,
    "remediation": "Rotate the AWS access key immediately",
    "reasoning": "This appears to be a valid AWS access key format"
  }
]"""
        
        return prompt
    
    def _parse_classification_response(self, response: Any, candidates: List[Dict[str, Any]]) -> List[ClassificationResult]:
        """Parse MCP response into classification results."""
        results = []
        
        try:
            # Handle different response formats
            if isinstance(response, list):
                classifications = response
            elif isinstance(response, dict) and "choices" in response:
                classifications = response["choices"]
            else:
                logger.error(f"Unexpected response format: {type(response)}")
                return self._create_fallback_results(candidates)
            
            for classification in classifications:
                if isinstance(classification, dict):
                    result = ClassificationResult(
                        is_secret=classification.get("is_secret", False),
                        is_vulnerability=classification.get("is_vulnerability", False),
                        type=classification.get("type", "unknown"),
                        severity=classification.get("severity", "LOW"),
                        confidence=float(classification.get("confidence", 0.5)),
                        remediation=classification.get("remediation", "Review and secure this item"),
                        reasoning=classification.get("reasoning", "No reasoning provided")
                    )
                    results.append(result)
                else:
                    # Handle text responses that need parsing
                    try:
                        parsed = json.loads(str(classification))
                        result = ClassificationResult(
                            is_secret=parsed.get("is_secret", False),
                            is_vulnerability=parsed.get("is_vulnerability", False),
                            type=parsed.get("type", "unknown"),
                            severity=parsed.get("severity", "LOW"),
                            confidence=float(parsed.get("confidence", 0.5)),
                            remediation=parsed.get("remediation", "Review and secure this item"),
                            reasoning=parsed.get("reasoning", "No reasoning provided")
                        )
                        results.append(result)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Failed to parse classification: {e}")
                        results.append(self._create_fallback_result())
            
            # Ensure we have results for all candidates
            while len(results) < len(candidates):
                results.append(self._create_fallback_result())
            
            return results[:len(candidates)]
            
        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
            return self._create_fallback_results(candidates)
    
    def _create_fallback_results(self, candidates: List[Dict[str, Any]]) -> List[ClassificationResult]:
        """Create fallback results when MCP fails."""
        return [self._create_fallback_result() for _ in candidates]
    
    def _create_fallback_result(self) -> ClassificationResult:
        """Create a fallback result."""
        return ClassificationResult(
            is_secret=False,
            is_vulnerability=False,
            type="unknown",
            severity="LOW",
            confidence=0.1,
            remediation="Manual review recommended",
            reasoning="MCP classification failed, manual review required"
        )
    
    async def classify_single_text(self, text: str) -> ClassificationResult:
        """Classify a single text input (for MCP classify page)."""
        try:
            conversation = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a security expert. Analyze the provided text for secrets or vulnerabilities. Respond with JSON only."
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this text for secrets or vulnerabilities:

Text: "{text}"

Respond with JSON:
{{
  "is_secret": true/false,
  "is_vulnerability": true/false,
  "type": "secret_type_or_vulnerability",
  "severity": "CRITICAL/HIGH/MEDIUM/LOW",
  "confidence": 0.0-1.0,
  "remediation": "brief_remediation_advice",
  "reasoning": "brief_explanation"
}}"""
                    }
                ],
                "provider": "gemini"
            }
            
            response = await self.mcp_client.chat(conversation)
            
            if response.get("status") == "ok" and response.get("result"):
                return self._parse_single_classification(response["result"])
            else:
                logger.error(f"MCP single classification failed: {response}")
                return self._create_fallback_result()
                
        except Exception as e:
            logger.error(f"MCP single classification error: {e}")
            return self._create_fallback_result()
    
    def _parse_single_classification(self, response: Any) -> ClassificationResult:
        """Parse single classification response."""
        try:
            # Handle different response formats
            if isinstance(response, list) and len(response) > 0:
                classification = response[0]
            elif isinstance(response, dict):
                classification = response
            else:
                return self._create_fallback_result()
            
            # Parse JSON if it's a string
            if isinstance(classification, str):
                try:
                    classification = json.loads(classification)
                except json.JSONDecodeError:
                    return self._create_fallback_result()
            
            return ClassificationResult(
                is_secret=classification.get("is_secret", False),
                is_vulnerability=classification.get("is_vulnerability", False),
                type=classification.get("type", "unknown"),
                severity=classification.get("severity", "LOW"),
                confidence=float(classification.get("confidence", 0.5)),
                remediation=classification.get("remediation", "Review and secure this item"),
                reasoning=classification.get("reasoning", "No reasoning provided")
            )
            
        except Exception as e:
            logger.error(f"Error parsing single classification: {e}")
            return self._create_fallback_result()
