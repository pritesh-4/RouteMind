"""
Intent Classification Engine for RouteMind.
Deterministic, keyword-based classifier that acts as a placeholder for future AI-based classifications.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Set
from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    """
    Standardized classification response model representing the classified intent details.
    """

    intent: str = Field(..., description="The classified task category/intent.")
    confidence: float = Field(..., description="Confidence score from 0.0 to 100.0.")
    matched_keywords: List[str] = Field(..., description="List of matched keywords.")
    classification_reason: str = Field(
        ..., description="Rationale for this classification."
    )
    complexity: str = Field(
        default="medium",
        description="The estimated complexity of the user request (simple, medium, complex)."
    )


class BaseIntentClassifier(ABC):
    """
    Abstract contract for all intent classifiers in RouteMind.
    Enables swapping rule-based classifiers for LLM-based ones in the future.
    """

    @abstractmethod
    def classify(self, message: str) -> IntentResult:
        """
        Analyzes user input message to determine user intent.

        Args:
            message: User prompt string.

        Returns:
            IntentResult containing classified intent metadata.
        """
        pass


class RuleBasedIntentClassifier(BaseIntentClassifier):
    """
    Lightweight rule-based intent classifier using keyword heuristics.
    """

    def __init__(self) -> None:
        # Standardized lists of lowercase keywords for each intent
        self._keyword_rules = {
            "coding": {
                "debug",
                "debugging",
                "stacktrace",
                "exception",
                "error",
                "fix",
                "logs",
                "code",
                "python",
                "javascript",
                "react",
                "html",
                "css",
                "compile",
                "function",
                "class",
                "bug",
                "git",
                "api",
                "json",
                "develop",
                "algorithm",
                "programming",
                "program",
                "programmer",
                "software",
                "rust",
                "typescript",
                "c++",
                "java",
                "golang",
            },
            "math": {
                "solve",
                "x²",
                "equation",
                "math",
                "calculate",
                "integral",
                "derivative",
                "plus",
                "minus",
                "algebra",
                "calculus",
                "arithmetic",
                "geometry",
                "formula",
            },
            "reasoning": {
                "reason",
                "reasoning",
                "logic",
                "prove",
                "proof",
                "puzzle",
                "riddle",
                "step-by-step",
                "why",
            },
            "research": {
                "research",
                "study",
                "literature",
                "scientific",
                "concept",
                "theory",
            },
            "analysis": {
                "analysis",
                "analyze",
                "deep analysis",
                "evaluate",
                "evaluation",
                "investigate",
                "compare",
                "explain",
                "explaining",
                "history",
            },
            "planning": {
                "plan",
                "planning",
                "roadmap",
                "schedule",
                "milestones",
                "timeline",
            },
            "strategy": {
                "strategy",
                "strategic",
                "strategic planning",
                "optimize",
                "optimization",
            },
            "document": {
                "document analysis",
                "parse document",
                "read document",
                "document",
                "docx",
                "xlsx",
                "csv",
                "file",
                "pdf analysis",
                "parse pdf",
                "read pdf",
                "pdf",
                "summarize",
                "summarization",
                "summary",
                "outline",
                "brief",
            },
            "writing": {
                "write",
                "essay",
                "email",
                "draft",
                "poem",
                "story",
                "paragraph",
                "letter",
                "blog",
                "compose",
                "editorial",
                "article",
                "copywrite",
            },
            "image": {
                "image understanding",
                "parse image",
                "read image",
                "image",
                "picture",
                "photo",
                "diagram",
                "graphic",
                "visual",
                "sketch",
                "paint",
                "draw",
                "generate image",
            },
        }
        self._fallback_intent = "general"

    def _detect_complexity(self, message: str) -> str:
        cleaned = message.lower().strip()
        
        # Simple keywords / greetings / short queries
        simple_keywords = {"hello", "hi", "hey", "test", "ping", "help", "greet", "greetings"}
        words = set(re.findall(r"\b\w+\b", cleaned))
        
        if len(cleaned) < 15 or (len(words) <= 2 and words.issubset(simple_keywords)):
            return "simple"
            
        # Complex keywords
        complex_keywords = {
            "design", "architecture", "distributed", "event-driven", "system design",
            "microservices", "kubernetes", "compiler", "deep learning", "proof",
            "optimization", "complex", "production-ready", "concurrency", "thread-safe",
            "scalability", "sharding", "database design", "refactor", "performance audit",
            "neural", "asynchronous", "performance", "throughput", "redundancy"
        }
        
        has_complex_keyword = any(kw in cleaned for kw in complex_keywords)
        if len(cleaned) > 200 or has_complex_keyword:
            return "complex"
            
        return "medium"

    def classify(self, message: str) -> IntentResult:
        """
        Calculates user intent using word boundary matches for exact keywords.
        Confidence scales with number of keywords matched.

        Args:
            message: User prompt to evaluate.

        Returns:
            IntentResult standard schema.
        """
        # Clean and tokenize message
        cleaned_message = message.lower().strip()
        words = set(re.findall(r"\b\w+\b", cleaned_message))
        # Handle special keywords containing non-alphanumeric chars or multi-word keywords
        for special_keyword in [
            "x²",
            "document analysis",
            "pdf analysis",
            "image understanding",
            "general chat",
            "general",
            "generate image",
            "parse document",
            "read document",
            "parse pdf",
            "read pdf",
            "parse image",
            "read image",
            "deep analysis",
            "strategic planning",
        ]:
            if special_keyword in cleaned_message:
                words.add(special_keyword)

        best_intent = self._fallback_intent
        max_matches = 0
        best_matched_keywords: Set[str] = set()

        # Check keyword overlaps for each configured intent category
        for intent, keywords in self._keyword_rules.items():
            intersection = words.intersection(keywords)
            matches_count = len(intersection)
            if matches_count > max_matches:
                max_matches = matches_count
                best_intent = intent
                best_matched_keywords = intersection

        # Compute confidence score dynamically
        if max_matches == 0:
            confidence = 50.0
            reason = "No matching keywords found. Defaulting to general intent."
        else:
            # Baseline is 80.0% for matching one keyword, plus 5.0% for each additional, capped at 100.0%
            confidence = min(80.0 + (max_matches - 1) * 5.0, 100.0)
            reason = (
                f"Matched {max_matches} keyword(s) for intent '{best_intent}': "
                f"{sorted(list(best_matched_keywords))}."
            )

        complexity = self._detect_complexity(message)

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            matched_keywords=sorted(list(best_matched_keywords)),
            classification_reason=reason,
            complexity=complexity,
        )
