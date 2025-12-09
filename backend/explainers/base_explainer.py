from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import logging
from ..schemas.models import Explanation, ModelCapabilities


class BaseExplainer(ABC):
    """Abstract base class for all explainability methods"""
    
    def __init__(self, model_wrapper, **kwargs):
        """
        Initialize explainer with model wrapper
        
        Args:
            model_wrapper: Model wrapper instance (OpenRouter, OpenAI, etc.)
            **kwargs: Method-specific parameters
        """
        self.model_wrapper = model_wrapper
        self.model_capabilities = model_wrapper.capabilities
        self.method_name = self.__class__.__name__.replace('Explainer', '').lower()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        Generate explanation for input text
        
        Args:
            input_text: Text to explain
            **kwargs: Method-specific parameters
            
        Returns:
            Explanation object with results
        """
        pass
    
    @property
    def requires_internals(self) -> bool:
        """Whether this method requires access to model internals"""
        return False
    
    @property
    def fallback_available(self) -> bool:
        """Whether fallback implementation is available for API-only models"""
        return True
    
    @property
    def supported_methods(self) -> List[str]:
        """List of supported method variants"""
        return [self.method_name]
    
    def _validate_input(self, input_text: str) -> None:
        """Validate input text"""
        if not input_text or not input_text.strip():
            raise ValueError("Input text cannot be empty")
        if len(input_text) > 10000:  # Reasonable limit
            raise ValueError("Input text too long (max 10000 characters)")
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range"""
        if not scores:
            return scores
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same, return equal weights
            return [0.5] * len(scores)
        
        normalized = [(score - min_score) / (max_score - min_score) for score in scores]
        return normalized
    
    def _generate_narrative(self, explanation: Explanation) -> str:
        """Generate natural language narrative for explanation"""
        if explanation.method == "lime":
            return self._generate_lime_narrative(explanation)
        elif explanation.method == "shap":
            return self._generate_shap_narrative(explanation)
        elif explanation.method == "inseq":
            return self._generate_inseq_narrative(explanation)
        elif explanation.method == "gaf":
            return self._generate_gaf_narrative(explanation)
        elif explanation.method == "contrast_cat":
            return self._generate_contrast_narrative(explanation)
        elif explanation.method == "attribution_patching":
            return self._generate_patching_narrative(explanation)
        elif explanation.method == "slalom":
            return self._generate_slalom_narrative(explanation)
        else:
            return f"Explanation generated using {explanation.method} method."
    
    def _generate_lime_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for LIME explanations"""
        top_tokens = sorted(
            zip(explanation.tokens, explanation.scores), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        narrative = f"LIME analysis identified the most influential tokens in the input. "
        narrative += f"The top contributing tokens are: "
        narrative += ", ".join([f"'{token}' (score: {score:.3f})" for token, score in top_tokens])
        narrative += ". These tokens had the highest impact on the model's output through local perturbation analysis."
        
        return narrative
    
    def _generate_shap_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for SHAP explanations"""
        top_tokens = sorted(
            zip(explanation.tokens, explanation.scores), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        narrative = f"SHAP analysis reveals token importance through game-theoretic attribution. "
        narrative += f"The most significant tokens are: "
        narrative += ", ".join([f"'{token}' (score: {score:.3f})" for token, score in top_tokens])
        narrative += ". These tokens contribute most to the predicted output based on their marginal contributions."
        
        return narrative
    
    def _generate_inseq_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for InSeq explanations"""
        return f"Token attribution analysis using gradient-based methods (fallback: occlusion sensitivity). The most important tokens are highlighted in the visualization."
    
    def _generate_gaf_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for GAF explanations"""
        return f"Generalized Attention Flow analysis identifies information flow paths through the model (fallback: token co-occurrence analysis)."
    
    def _generate_contrast_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for Contrast-CAT explanations"""
        return f"Contrastive activation analysis compares model behavior between contrasting inputs to identify discriminative features."
    
    def _generate_patching_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for Attribution Patching explanations"""
        return f"Causal attribution analysis through token-level intervention identifies which input tokens most affect the output."
    
    def _generate_slalom_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for SLALOM explanations"""
        if explanation.surrogate_logic:
            narrative = f"SLALOM surrogate model achieved {explanation.surrogate_logic.accuracy:.3f} accuracy. "
            narrative += f"Key logic segments: "
            segments = explanation.surrogate_logic.segments[:3]
            narrative += "; ".join([f"'{seg.condition}' (weight: {seg.weight:.3f})" for seg in segments])
            return narrative
        return "SLALOM surrogate model analysis completed."
    
    async def _measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
