import numpy as np
import asyncio
from typing import List, Dict, Any, Tuple, Optional
import logging
import time

from .base_explainer import BaseExplainer
from ..schemas.models import Explanation, ExplanationMetadata, ModelCapabilities, ContrastScore


class ContrastCATExplainer(BaseExplainer):
    """
    Contrast-CAT explainer - fallback implementation using output probability comparison
    since activations are not available through OpenRouter API
    """
    
    def __init__(self, model_wrapper, contrast_mode: str = "negation", 
                 num_contrast_samples: int = 5, **kwargs):
        """
        Initialize Contrast-CAT explainer with fallback methods
        
        Args:
            model_wrapper: Model wrapper instance
            contrast_mode: How to generate contrasting inputs ("negation", "synonym", "random")
            num_contrast_samples: Number of contrasting samples to generate
        """
        super().__init__(model_wrapper, **kwargs)
        self.contrast_mode = contrast_mode
        self.num_contrast_samples = num_contrast_samples
        
    @property
    def requires_internals(self) -> bool:
        """True Contrast-CAT requires activations, but we use fallback"""
        return True
    
    @property
    def fallback_available(self) -> bool:
        """Output comparison fallback is available"""
        return True
    
    async def _generate_contrastive_input(self, input_text: str) -> str:
        """
        Generate a contrasting version of the input text
        
        Args:
            input_text: Original input text
            
        Returns:
            Contrasting input text
        """
        if self.contrast_mode == "negation":
            # Add negation words
            negations = ["not", "never", "no", "don't", "can't", "won't"]
            tokens = input_text.split()
            
            if tokens:
                # Insert negation at beginning or after first verb
                contrast_tokens = tokens.copy()
                insert_pos = 0 if tokens[0].lower() not in ["the", "a", "an"] else 1
                contrast_tokens.insert(insert_pos, np.random.choice(negations))
                return " ".join(contrast_tokens)
        
        elif self.contrast_mode == "synonym":
            # Simple synonym replacement (placeholder)
            synonyms = {
                "good": "bad",
                "great": "terrible", 
                "positive": "negative",
                "increase": "decrease",
                "high": "low"
            }
            
            tokens = input_text.split()
            contrast_tokens = []
            
            for token in tokens:
                lower_token = token.lower()
                if lower_token in synonyms:
                    contrast_tokens.append(synonyms[lower_token])
                else:
                    contrast_tokens.append(token)
            
            return " ".join(contrast_tokens)
        
        elif self.contrast_mode == "random":
            # Random word replacement
            tokens = input_text.split()
            if len(tokens) > 1:
                # Shuffle word order
                shuffled = tokens.copy()
                np.random.shuffle(shuffled)
                return " ".join(shuffled)
        
        return input_text  # Fallback
    
    async def _measure_output_similarity(self, output1: str, output2: str) -> float:
        """
        Measure similarity between two outputs
        
        Args:
            output1: First output text
            output2: Second output text
            
        Returns:
            Similarity score (0-1)
        """
        # Simple token-based similarity
        tokens1 = set(output1.lower().split())
        tokens2 = set(output2.lower().split())
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        if union == 0:
            return 1.0  # Both outputs are empty
        
        return intersection / union
    
    async def _compute_contrast_scores(self, input_text: str) -> List[ContrastScore]:
        """
        Compute contrast scores for each token
        
        Args:
            input_text: Input text to analyze
            
        Returns:
            List of contrast scores
        """
        tokens = input_text.split()
        contrast_scores = []
        
        # Generate original output
        original_output = await self.model_wrapper.generate(input_text, temperature=0.1)
        
        # Generate multiple contrastive inputs and compute differences
        for i, token in enumerate(tokens):
            total_contrast = 0.0
            baseline_similarity = 0.0
            
            for _ in range(self.num_contrast_samples):
                # Generate contrastive input by modifying this token
                contrastive_tokens = tokens.copy()
                
                if self.contrast_mode == "negation":
                    # Add negation near this token
                    if i == 0:
                        contrastive_tokens.insert(0, "not")
                    else:
                        contrastive_tokens.insert(i, "not")
                elif self.contrast_mode == "synonym":
                    # Replace with opposite meaning
                    contrastive_tokens[i] = "NOT_" + token
                else:
                    # Remove token
                    contrastive_tokens[i] = ""
                
                contrastive_text = " ".join([t for t in contrastive_tokens if t])
                
                try:
                    # Generate contrastive output
                    contrastive_output = await self.model_wrapper.generate(contrastive_text, temperature=0.1)
                    
                    # Measure similarity difference
                    similarity = await self._measure_output_similarity(
                        original_output.text, 
                        contrastive_output.text
                    )
                    
                    total_contrast += (1.0 - similarity)  # Contrast = dissimilarity
                    
                    if baseline_similarity == 0.0:
                        baseline_similarity = similarity
                    
                except Exception as e:
                    self.logger.warning(f"Error in contrast computation: {e}")
                    total_contrast += 0.0
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            # Average contrast across samples
            avg_contrast = total_contrast / self.num_contrast_samples
            
            contrast_score = ContrastScore(
                token=token,
                contrast_value=avg_contrast,
                baseline_activation=baseline_similarity,
                contrast_activation=baseline_similarity - avg_contrast
            )
            
            contrast_scores.append(contrast_score)
        
        return contrast_scores
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        Generate Contrast-CAT explanation using output comparison fallback
        
        Args:
            input_text: Text to explain
            **kwargs: Additional parameters
            
        Returns:
            Explanation object with Contrast-CAT results
        """
        start_time = time.time()
        self._validate_input(input_text)
        
        try:
            # Get model output for original text
            original_output = await self.model_wrapper.generate(input_text)
            
            # Compute contrast scores
            contrast_scores = await self._compute_contrast_scores(input_text)
            
            # Extract tokens and scores for standard format
            tokens = [cs.token for cs in contrast_scores]
            scores = [abs(cs.contrast_value) for cs in contrast_scores]
            
            # Normalize scores to 0-1 range
            normalized_scores = self._normalize_scores(scores)
            
            # Create metadata
            metadata = ExplanationMetadata(
                execution_time=time.time() - start_time,
                num_samples=len(tokens) * self.num_contrast_samples,
                method_params={
                    'contrast_mode': self.contrast_mode,
                    'num_contrast_samples': self.num_contrast_samples,
                    'fallback_method': 'output_similarity_comparison'
                },
                model_capabilities=ModelCapabilities(**self.model_capabilities)
            )
            
            # Create explanation object
            result = Explanation(
                model=self.model_wrapper.model_name,
                method='contrast_cat',
                input_text=input_text,
                output_text=original_output.text,
                tokens=tokens,
                scores=normalized_scores,
                contrast_scores=contrast_scores,
                narrative=self._generate_contrast_narrative(result),
                metadata=metadata
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating Contrast-CAT explanation: {e}")
            raise
    
    def _generate_contrast_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for Contrast-CAT explanations"""
        if explanation is None:
            return "Contrast-CAT analysis being generated..."
        
        top_contrasts = sorted(
            explanation.contrast_scores or [], 
            key=lambda x: abs(x.contrast_value), 
            reverse=True
        )[:5]
        
        narrative = f"Contrast-CAT analysis (fallback: output similarity comparison). "
        narrative += f"Since activations are not available through the API, computed contrast by "
        narrative += f"generating {self.num_contrast_samples} contrasting inputs using {self.contrast_mode} mode "
        narrative += f"and measuring output dissimilarity. "
        narrative += f"The most contrastive tokens are: "
        narrative += ", ".join([f"'{cs.token}' (contrast: {cs.contrast_value:.3f})" for cs in top_contrasts])
        narrative += ". Higher contrast values indicate tokens that, when modified, cause the largest changes in model output."
        
        return narrative


class TrueContrastCATExplainer(ContrastCATExplainer):
    """
    Placeholder for true Contrast-CAT implementation with real activation comparisons
    (would work with local models that expose activations)
    """
    
    @property
    def requires_internals(self) -> bool:
        """True Contrast-CAT requires activations"""
        return True
    
    @property
    def fallback_available(self) -> bool:
        """Fallback to output comparison is available"""
        return True
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        True Contrast-CAT explanation with activation comparisons
        
        Note: This would work with local models that can expose activations.
        For API models, it falls back to output similarity comparison.
        """
        if not self.model_capabilities.get("hidden_states", False):
            self.logger.info("Activations not available, falling back to output similarity comparison")
            return await super().explain(input_text, **kwargs)
        
        # Placeholder for true activation-based Contrast-CAT computation
        # This would involve:
        # 1. Getting activations for original input
        # 2. Getting activations for contrastive inputs  
        # 3. Computing activation differences per token/layer
        # 4. Identifying most contrastive activations
        
        self.logger.warning("True activation-based Contrast-CAT not implemented yet, using fallback")
        return await super().explain(input_text, **kwargs)
