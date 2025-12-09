import numpy as np
import asyncio
from typing import List, Dict, Any, Tuple, Optional
import logging
import time

from .base_explainer import BaseExplainer
from ..schemas.models import Explanation, ExplanationMetadata, ModelCapabilities


class InSeqExplainer(BaseExplainer):
    """
    InSeq Token Attribution explainer - fallback implementation using occlusion sensitivity
    since gradients are not available through OpenRouter API
    """
    
    def __init__(self, model_wrapper, occlusion_mode: str = "mask", perturbation_steps: int = 20, **kwargs):
        """
        Initialize InSeq explainer with fallback methods
        
        Args:
            model_wrapper: Model wrapper instance
            occlusion_mode: How to occlude tokens ("mask", "remove", "replace")
            perturbation_steps: Number of perturbation steps per token
        """
        super().__init__(model_wrapper, **kwargs)
        self.occlusion_mode = occlusion_mode
        self.perturbation_steps = perturbation_steps
        
    @property
    def requires_internals(self) -> bool:
        """True InSeq requires gradients, but we use fallback"""
        return True
    
    @property
    def fallback_available(self) -> bool:
        """Occlusion-based fallback is available"""
        return True
    
    async def _occlude_token(self, text: str, token_idx: int) -> str:
        """
        Occlude a specific token in the text
        
        Args:
            text: Original text
            token_idx: Index of token to occlude
            
        Returns:
            Text with occluded token
        """
        tokens = text.split()
        
        if token_idx >= len(tokens):
            return text
        
        if self.occlusion_mode == "mask":
            tokens[token_idx] = "[MASK]"
        elif self.occlusion_mode == "remove":
            tokens[token_idx] = ""
        elif self.occlusion_mode == "replace":
            tokens[token_idx] = "UNK"
        
        return " ".join([t for t in tokens if t])
    
    async def _measure_output_change(self, original_text: str, perturbed_text: str) -> float:
        """
        Measure change in model output between original and perturbed text
        
        Args:
            original_text: Original input text
            perturbed_text: Perturbed input text
            
        Returns:
            Magnitude of output change
        """
        try:
            # Generate outputs
            original_output = await self.model_wrapper.generate(original_text, temperature=0.1)
            perturbed_output = await self.model_wrapper.generate(perturbed_text, temperature=0.1)
            
            # Simple similarity metric based on text characteristics
            # In a real implementation, you might use semantic similarity or logprob differences
            original_len = len(original_output.text)
            perturbed_len = len(perturbed_output.text)
            
            # Use length difference as a simple proxy for output change
            change = abs(original_len - perturbed_len) / max(original_len, perturbed_len, 1)
            
            return change
            
        except Exception as e:
            self.logger.warning(f"Error measuring output change: {e}")
            return 0.0
    
    async def _compute_occlusion_importance(self, input_text: str) -> List[float]:
        """
        Compute token importance using occlusion sensitivity
        
        Args:
            input_text: Input text to analyze
            
        Returns:
            List of importance scores for each token
        """
        tokens = input_text.split()
        importance_scores = []
        
        for i, token in enumerate(tokens):
            # Generate perturbed text by occluding this token
            perturbed_text = await self._occlude_token(input_text, i)
            
            # Measure output change
            change = await self._measure_output_change(input_text, perturbed_text)
            importance_scores.append(change)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return importance_scores
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        Generate InSeq explanation using occlusion-based fallback
        
        Args:
            input_text: Text to explain
            **kwargs: Additional parameters
            
        Returns:
            Explanation object with InSeq results
        """
        start_time = time.time()
        self._validate_input(input_text)
        
        try:
            # Get model output for original text
            original_output = await self.model_wrapper.generate(input_text)
            
            # Compute token importance using occlusion
            importance_scores = await self._compute_occlusion_importance(input_text)
            
            # Tokenize input
            tokens = input_text.split()
            
            # Normalize scores to 0-1 range
            normalized_scores = self._normalize_scores(importance_scores)
            
            # Create metadata
            metadata = ExplanationMetadata(
                execution_time=time.time() - start_time,
                num_samples=len(tokens),
                method_params={
                    'occlusion_mode': self.occlusion_mode,
                    'perturbation_steps': self.perturbation_steps,
                    'fallback_method': 'occlusion_sensitivity'
                },
                model_capabilities=ModelCapabilities(**self.model_capabilities)
            )
            
            # Create explanation object
            result = Explanation(
                model=self.model_wrapper.model_name,
                method='inseq',
                input_text=input_text,
                output_text=original_output.text,
                tokens=tokens,
                scores=normalized_scores,
                narrative=self._generate_inseq_narrative(result),
                metadata=metadata
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating InSeq explanation: {e}")
            raise
    
    def _generate_inseq_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for InSeq explanations"""
        if explanation is None:
            return "InSeq token attribution analysis being generated..."
        
        top_tokens = sorted(
            zip(explanation.tokens, explanation.scores), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        narrative = f"InSeq token attribution analysis (fallback: occlusion sensitivity). "
        narrative += f"Since gradient access is not available through the API, token importance was computed by "
        narrative += f"measuring output changes when each token is occluded ({self.occlusion_mode} mode). "
        narrative += f"The most influential tokens are: "
        narrative += ", ".join([f"'{token}' (importance: {score:.3f})" for token, score in top_tokens])
        narrative += ". Higher importance indicates that removing or masking the token significantly changes the model's output."
        
        return narrative


class GradientBasedInSeqExplainer(InSeqExplainer):
    """
    Placeholder for true gradient-based InSeq implementation
    (would work with local models that expose gradients)
    """
    
    @property
    def requires_internals(self) -> bool:
        """True gradient-based method requires model internals"""
        return True
    
    @property
    def fallback_available(self) -> bool:
        """Fallback to occlusion is available"""
        return True
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        True gradient-based explanation (placeholder)
        
        Note: This would work with local models that can expose gradients.
        For API models, it falls back to occlusion sensitivity.
        """
        if not self.model_capabilities.get("gradients", False):
            self.logger.info("Gradients not available, falling back to occlusion sensitivity")
            return await super().explain(input_text, **kwargs)
        
        # Placeholder for true gradient computation
        # This would involve:
        # 1. Forward pass to get embeddings
        # 2. Backward pass to compute gradients
        # 3. Gradient-based attribution (Integrated Gradients, etc.)
        
        self.logger.warning("True gradient-based InSeq not implemented yet, using fallback")
        return await super().explain(input_text, **kwargs)


class IntegratedGradientsExplainer(InSeqExplainer):
    """
    Integrated Gradients implementation (fallback version)
    """
    
    def __init__(self, model_wrapper, num_steps: int = 50, baseline: str = "", **kwargs):
        super().__init__(model_wrapper, **kwargs)
        self.num_steps = num_steps
        self.baseline = baseline
    
    async def _compute_integrated_gradients(self, input_text: str) -> List[float]:
        """
        Compute integrated gradients using interpolation approach
        
        Args:
            input_text: Input text to analyze
            
        Returns:
            List of attribution scores
        """
        tokens = input_text.split()
        attribution_scores = []
        
        for i, token in enumerate(tokens):
            # Create interpolation steps from baseline to input
            total_attribution = 0.0
            
            for step in range(1, self.num_steps + 1):
                # Interpolate between baseline and current token
                alpha = step / self.num_steps
                
                # Create interpolated text (simplified approach)
                if self.baseline:
                    interpolated_tokens = tokens.copy()
                    interpolated_tokens[i] = self.baseline if alpha < 0.5 else token
                else:
                    interpolated_tokens = tokens[:i] + [token if alpha > 0.5 else ""] + tokens[i+1:]
                
                interpolated_text = " ".join([t for t in interpolated_tokens if t])
                
                # Measure output change at this step
                change = await self._measure_output_change(input_text, interpolated_text)
                total_attribution += change
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.05)
            
            # Average attribution across steps
            attribution_scores.append(total_attribution / self.num_steps)
        
        return attribution_scores
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """Generate Integrated Gradients explanation"""
        start_time = time.time()
        self._validate_input(input_text)
        
        try:
            # Get model output for original text
            original_output = await self.model_wrapper.generate(input_text)
            
            # Compute integrated gradients
            attribution_scores = await self._compute_integrated_gradients(input_text)
            
            # Tokenize input
            tokens = input_text.split()
            
            # Normalize scores to 0-1 range
            normalized_scores = self._normalize_scores(attribution_scores)
            
            # Create metadata
            metadata = ExplanationMetadata(
                execution_time=time.time() - start_time,
                num_samples=len(tokens) * self.num_steps,
                method_params={
                    'num_steps': self.num_steps,
                    'baseline': self.baseline,
                    'fallback_method': 'interegrated_gradients_approximation'
                },
                model_capabilities=ModelCapabilities(**self.model_capabilities)
            )
            
            # Create explanation object
            result = Explanation(
                model=self.model_wrapper.model_name,
                method='inseq',
                input_text=input_text,
                output_text=original_output.text,
                tokens=tokens,
                scores=normalized_scores,
                narrative=self._generate_integrated_gradients_narrative(result),
                metadata=metadata
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating Integrated Gradients explanation: {e}")
            raise
    
    def _generate_integrated_gradients_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for Integrated Gradients explanations"""
        if explanation is None:
            return "Integrated Gradients analysis being generated..."
        
        top_tokens = sorted(
            zip(explanation.tokens, explanation.scores), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        narrative = f"Integrated Gradients analysis (approximation for API models). "
        narrative += f"Computed token attribution by interpolating between baseline ('{self.baseline}') and input across {self.num_steps} steps. "
        narrative += f"The most influential tokens are: "
        narrative += ", ".join([f"'{token}' (attribution: {score:.3f})" for token, score in top_tokens])
        narrative += ". This method approximates true integrated gradients by measuring output changes along the interpolation path."
        
        return narrative
