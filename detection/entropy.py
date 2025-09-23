"""Entropy-based secret detection."""

import math
import re
from typing import List, Tuple


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not text:
        return 0.0
    
    # Count character frequencies
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    
    # Calculate entropy
    entropy = 0.0
    text_len = len(text)
    
    for count in char_counts.values():
        probability = count / text_len
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy


def detect_high_entropy_strings(text: str, threshold: float = 4.5, min_length: int = 20) -> List[Tuple[str, float, int, int]]:
    """Detect high entropy strings in text.
    
    Args:
        text: Text to scan
        threshold: Entropy threshold
        min_length: Minimum string length to consider
        
    Returns:
        List of (string, entropy, start_pos, end_pos) tuples
    """
    # Find potential secret strings (alphanumeric + common symbols)
    pattern = r'[A-Za-z0-9+/=_-]{' + str(min_length) + ',}'
    matches = []
    
    for match in re.finditer(pattern, text):
        candidate = match.group(0)
        entropy = calculate_entropy(candidate)
        
        if entropy >= threshold:
            matches.append((candidate, entropy, match.start(), match.end()))
    
    return matches


def is_likely_secret(text: str, entropy_threshold: float = 4.5) -> Tuple[bool, float]:
    """Check if text is likely a secret based on entropy.
    
    Args:
        text: Text to analyze
        entropy_threshold: Minimum entropy threshold
        
    Returns:
        Tuple of (is_likely_secret, entropy_score)
    """
    if len(text) < 10:  # Too short to be meaningful
        return False, 0.0
    
    entropy = calculate_entropy(text)
    
    # Additional heuristics
    has_mixed_case = any(c.islower() for c in text) and any(c.isupper() for c in text)
    has_numbers = any(c.isdigit() for c in text)
    has_symbols = any(c in "+/=_-" for c in text)
    
    # Boost confidence for strings with mixed character types
    confidence_boost = 0.0
    if has_mixed_case:
        confidence_boost += 0.1
    if has_numbers:
        confidence_boost += 0.1
    if has_symbols:
        confidence_boost += 0.1
    
    adjusted_entropy = entropy + confidence_boost
    
    return adjusted_entropy >= entropy_threshold, adjusted_entropy


def filter_common_false_positives(text: str) -> bool:
    """Filter out common false positives.
    
    Args:
        text: Text to check
        
    Returns:
        True if likely a false positive
    """
    # Common false positive patterns
    false_positive_patterns = [
        r'^[0-9]+$',  # Pure numbers
        r'^[A-Z]+$',  # Pure uppercase
        r'^[a-z]+$',  # Pure lowercase
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$',  # Dates
        r'^[0-9]{2}:[0-9]{2}:[0-9]{2}$',  # Times
        r'^[0-9]+\.[0-9]+\.[0-9]+$',  # Version numbers
        r'^[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}$',  # UUIDs
    ]
    
    for pattern in false_positive_patterns:
        if re.match(pattern, text):
            return True
    
    # Check for repeated patterns (low entropy indicators)
    if len(set(text)) < len(text) * 0.3:  # Less than 30% unique characters
        return True
    
    return False
