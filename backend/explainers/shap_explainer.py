import numpy as np
import asyncio
from typing import List, Dict, Any, Tuple, Optional
import logging
import shap
from shap.explainers import KernelExplainer
import time

from .base_explainer import BaseExplainer
from ..schemas.models import Explanation, ExplanationMetadata, ModelCapabilities


class ShapExplainer(BaseExplainer):
    """SHAP explainer using KernelSHAP for model-agnostic explanations"""
    
    def __init__(self, model_wrapper, num_samples: int = 1000, background_samples: int = 10, **kwargs):
        """
        Initialize SHAP explainer
        
        Args:
            model_wrapper: Model wrapper instance
            num_samples: Number of samples for SHAP explanation
            background_samples: Number of background samples for baseline
        """
        super().__init__(model_wrapper, **kwargs)
        self.num_samples = num_samples
        self.background_samples = background_samples
        self.background_data: Optional[List[str]] = None
        self.shap_explainer: Optional[KernelExplainer] = None
        
    @property
    def requires_internals(self) -> bool:
        """SHAP KernelExplainer is black-box, doesn't require internals"""
        return False
    
    async def _initialize_background_data(self, input_text: str) -> List[str]:
        """
        Initialize background data for SHAP baseline
        
        Args:
            input_text: Reference text to generate variations from
            
        Returns:
            List of background text samples
        """
        background_samples = []
        
        # Create variations by removing/masking words
        words = input_text.split()
        
        # Empty string as baseline
        background_samples.append("")
        
        # Random subsets of words
        np.random.seed(42)
        for _ in range(self.background_samples - 1):
            if len(words) > 1:
                # Randomly keep 30-70% of words
                keep_ratio = np.random.uniform(0.3, 0.7)
                num_keep = max(1, int(len(words) * keep_ratio))
                selected_indices = np.random.choice(len(words), num_keep, replace=False)
                selected_indices.sort()
                
                masked_text = " ".join([words[i] for i in selected_indices])
                background_samples.append(masked_text)
            else:
                background_samples.append("")
        
        return background_samples
    
    async def _predict_fn(self, texts: List[str]) -> np.ndarray:
        """
        Prediction function for SHAP - generates model outputs
        
        Args:
            texts: List of text samples
            
        Returns:
            Array of prediction scores
        """
        predictions = []
        
        for text in texts:
            try:
                # Generate prediction using the model
                output = await self.model_wrapper.generate(text, temperature=0.1)
                
                # Use output characteristics as prediction score
                # In real implementation, you might use logprobs or specific task metrics
                score = len(output.text.strip()) / 100.0  # Normalize to reasonable range
                predictions.append(score)
                
            except Exception as e:
                self.logger.warning(f"Error predicting for text '{text[:50]}...': {e}")
                predictions.append(0.0)  # Default score on error
        
        return np.array(predictions)
    
    def _text_to_features(self, text: str) -> np.ndarray:
        """
        Convert text to feature vector for SHAP
        
        Args:
            text: Input text
            
        Returns:
            Feature vector (binary word presence)
        """
        # Simple bag-of-words representation
        words = set(text.lower().split())
        
        # Use vocabulary from background data if available
        if self.background_data:
            all_words = set()
            for sample in self.background_data:
                all_words.update(sample.lower().split())
            vocab = sorted(list(all_words))
        else:
            vocab = sorted(list(words))
        
        # Create binary feature vector
        features = np.zeros(len(vocab))
        for i, word in enumerate(vocab):
            if word in words:
                features[i] = 1
        
        return features
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        Generate SHAP explanation for input text
        
        Args:
            input_text: Text to explain
            **kwargs: Additional parameters
            
        Returns:
            Explanation object with SHAP results
        """
        start_time = time.time()
        self._validate_input(input_text)
        
        try:
            # Get model output for original text
            original_output = await self.model_wrapper.generate(input_text)
            
            # Initialize background data
            self.background_data = await self._initialize_background_data(input_text)
            
            # Create SHAP explainer
            self.shap_explainer = KernelExplainer(
                self._predict_fn,
                self.background_data
            )
            
            # Generate SHAP values
            shap_values = self.shap_explainer.shap_values(
                [input_text],
                nsamples=self.num_samples
            )
            
            # Extract tokens and scores from SHAP values
            tokens, scores = self._extract_shap_features(input_text, shap_values[0])
            
            # Normalize scores to 0-1 range (using absolute values for importance)
            normalized_scores = self._normalize_scores([abs(s) for s in scores])
            
            # Create metadata
            metadata = ExplanationMetadata(
                execution_time=time.time() - start_time,
                num_samples=self.num_samples,
                method_params={
                    'num_samples': self.num_samples,
                    'background_samples': self.background_samples
                },
                model_capabilities=ModelCapabilities(**self.model_capabilities)
            )
            
            # Create explanation object
            result = Explanation(
                model=self.model_wrapper.model_name,
                method='shap',
                input_text=input_text,
                output_text=original_output.text,
                tokens=tokens,
                scores=normalized_scores,
                narrative=self._generate_shap_narrative(None),  # Will be generated below
                metadata=metadata
            )
            
            # Generate narrative
            result.narrative = self._generate_shap_narrative(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating SHAP explanation: {e}")
            raise
    
    def _extract_shap_features(self, input_text: str, shap_values: np.ndarray) -> Tuple[List[str], List[float]]:
        """
        Extract tokens and SHAP values from explanation
        
        Args:
            input_text: Original input text
            shap_values: SHAP values array
            
        Returns:
            Tuple of (tokens, shap_scores)
        """
        # Tokenize input text
        tokens = input_text.split()
        
        # For simplicity, assign SHAP values to tokens based on position
        # In a more sophisticated implementation, you'd map features back to tokens
        if len(shap_values) >= len(tokens):
            scores = shap_values[:len(tokens)].tolist()
        else:
            # If fewer SHAP values than tokens, pad with zeros
            scores = shap_values.tolist() + [0.0] * (len(tokens) - len(shap_values))
        
        return tokens, scores
    
    def _generate_shap_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for SHAP explanations"""
        if explanation is None:
            return "SHAP explanation being generated..."
        
        top_tokens = sorted(
            zip(explanation.tokens, explanation.scores), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        narrative = f"SHAP analysis reveals token importance through game-theoretic attribution. "
        narrative += f"Generated {self.num_samples} samples to estimate marginal contributions. "
        narrative += f"The most significant tokens are: "
        narrative += ", ".join([f"'{token}' (importance: {score:.3f})" for token, score in top_tokens])
        narrative += ". These tokens contribute most to the predicted output based on their Shapley values, "
        narrative += "representing their average marginal contribution across all possible feature coalitions."
        
        return narrative


class ShapTextExplainer(ShapExplainer):
    """Enhanced SHAP explainer with better text feature handling"""
    
    def __init__(self, model_wrapper, use_tokenizer: bool = True, **kwargs):
        super().__init__(model_wrapper, **kwargs)
        self.use_tokenizer = use_tokenizer
        self.vocab: Optional[List[str]] = None
    
    async def _build_vocabulary(self, texts: List[str]) -> List[str]:
        """
        Build vocabulary from text samples
        
        Args:
            texts: List of text samples
            
        Returns:
            Vocabulary list
        """
        all_words = set()
        for text in texts:
            all_words.update(text.lower().split())
        
        self.vocab = sorted(list(all_words))
        return self.vocab
    
    def _text_to_features(self, text: str) -> np.ndarray:
        """
        Convert text to features using vocabulary
        
        Args:
            text: Input text
            
        Returns:
            Feature vector
        """
        if self.vocab is None:
            # Fallback to simple tokenization
            return super()._text_to_features(text)
        
        words = set(text.lower().split())
        features = np.zeros(len(self.vocab))
        
        for i, word in enumerate(self.vocab):
            if word in words:
                features[i] = 1
        
        return features
    
    def _extract_shap_features(self, input_text: str, shap_values: np.ndarray) -> Tuple[List[str], List[float]]:
        """
        Extract tokens and scores with better mapping
        
        Args:
            input_text: Original input text
            shap_values: SHAP values
            
        Returns:
            Tuple of (tokens, scores)
        """
        if self.vocab is None:
            return super()._extract_shap_features(input_text, shap_values)
        
        # Map SHAP values back to tokens that are present in input
        input_words = input_text.lower().split()
        token_scores = []
        
        for word in input_words:
            # Find SHAP value for this word
            if word in self.vocab:
                word_idx = self.vocab.index(word)
                if word_idx < len(shap_values):
                    token_scores.append(shap_values[word_idx])
                else:
                    token_scores.append(0.0)
            else:
                token_scores.append(0.0)
        
        return input_text.split(), token_scores
