import numpy as np
import asyncio
from typing import List, Dict, Any, Tuple
import logging
from lime.lime_text import LimeTextExplainer
from sklearn.feature_extraction.text import CountVectorizer
import time

from .base_explainer import BaseExplainer
from ..schemas.models import Explanation, ExplanationMetadata, ModelCapabilities


class LimeExplainer(BaseExplainer):
    """LIME explainer for text classification/regression using black-box perturbation"""
    
    def __init__(self, model_wrapper, num_samples: int = 5000, num_features: int = 50, **kwargs):
        """
        Initialize LIME explainer
        
        Args:
            model_wrapper: Model wrapper instance
            num_samples: Number of perturbed samples to generate
            num_features: Number of features to include in explanation
        """
        super().__init__(model_wrapper, **kwargs)
        self.num_samples = num_samples
        self.num_features = num_features
        
        # Initialize LIME explainer
        self.lime_explainer = LimeTextExplainer(
            class_names=['output'],
            split_expression=r'\W+',  # Split on non-word characters
            bow=False,  # Use bag of words
            random_state=42
        )
        
    @property
    def requires_internals(self) -> bool:
        """LIME is a black-box method, doesn't require internals"""
        return False
    
    async def _predict_fn(self, texts: List[str]) -> np.ndarray:
        """
        Prediction function for LIME - generates model outputs for perturbed texts
        
        Args:
            texts: List of perturbed text samples
            
        Returns:
            Array of prediction scores
        """
        predictions = []
        
        for text in texts:
            try:
                # Generate prediction using the model
                output = await self.model_wrapper.generate(text, temperature=0.1)
                
                # For simplicity, use text length as a proxy for "output score"
                # In a real implementation, you might want to use logprobs or other metrics
                score = len(output.text) / 100.0  # Normalize to reasonable range
                predictions.append(score)
                
            except Exception as e:
                self.logger.warning(f"Error predicting for text '{text[:50]}...': {e}")
                predictions.append(0.0)  # Default score on error
        
        return np.array(predictions)
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        Generate LIME explanation for input text
        
        Args:
            input_text: Text to explain
            **kwargs: Additional parameters
            
        Returns:
            Explanation object with LIME results
        """
        start_time = time.time()
        self._validate_input(input_text)
        
        try:
            # Get model output for original text
            original_output = await self.model_wrapper.generate(input_text)
            
            # Generate LIME explanation
            explanation = self.lime_explainer.explain_instance(
                text_instance=input_text,
                classifier_fn=self._predict_fn,
                num_features=self.num_features,
                num_samples=self.num_samples
            )
            
            # Extract tokens and scores from LIME explanation
            tokens, scores = self._extract_lime_features(explanation)
            
            # Normalize scores to 0-1 range
            normalized_scores = self._normalize_scores(scores)
            
            # Create metadata
            metadata = ExplanationMetadata(
                execution_time=time.time() - start_time,
                num_samples=self.num_samples,
                method_params={
                    'num_samples': self.num_samples,
                    'num_features': self.num_features
                },
                model_capabilities=ModelCapabilities(**self.model_capabilities)
            )
            
            # Create explanation object
            result = Explanation(
                model=self.model_wrapper.model_name,
                method='lime',
                input_text=input_text,
                output_text=original_output.text,
                tokens=tokens,
                scores=normalized_scores,
                narrative=self._generate_lime_narrative(None),  # Will be generated below
                metadata=metadata
            )
            
            # Generate narrative
            result.narrative = self._generate_lime_narrative(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating LIME explanation: {e}")
            raise
    
    def _extract_lime_features(self, lime_exp) -> Tuple[List[str], List[float]]:
        """
        Extract tokens and importance scores from LIME explanation
        
        Args:
            lime_exp: LIME explanation object
            
        Returns:
            Tuple of (tokens, scores)
        """
        # Get feature list from LIME explanation
        features = lime_exp.as_list()
        
        tokens = []
        scores = []
        
        for feature, score in features:
            # Features might be words or phrases
            if isinstance(feature, str):
                # Split multi-word features
                feature_tokens = feature.split()
                for token in feature_tokens:
                    if token.strip():
                        tokens.append(token.strip())
                        scores.append(abs(score))  # Use absolute importance
        
        # If no tokens extracted, fall back to simple tokenization
        if not tokens:
            tokens = lime_exp.text_instance.split()
            scores = [0.5] * len(tokens)  # Equal importance
        
        return tokens, scores
    
    def _generate_lime_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for LIME explanations"""
        if explanation is None:
            return "LIME explanation being generated..."
        
        top_tokens = sorted(
            zip(explanation.tokens, explanation.scores), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        narrative = f"LIME analysis identified the most influential tokens through local perturbation. "
        narrative += f"Generated {self.num_samples} perturbed samples to understand local model behavior. "
        narrative += f"The top contributing tokens are: "
        narrative += ", ".join([f"'{token}' (importance: {score:.3f})" for token, score in top_tokens])
        narrative += ". These tokens had the highest impact on the model's output when systematically perturbed."
        
        return narrative


class LimeClassificationExplainer(LimeExplainer):
    """LIME explainer specifically for classification tasks"""
    
    def __init__(self, model_wrapper, class_names: List[str] = None, **kwargs):
        super().__init__(model_wrapper, **kwargs)
        self.class_names = class_names or ['negative', 'positive']
        
        # Reinitialize LIME explainer with class names
        self.lime_explainer = LimeTextExplainer(
            class_names=self.class_names,
            split_expression=r'\W+',
            bow=False,
            random_state=42
        )
    
    async def _predict_fn(self, texts: List[str]) -> np.ndarray:
        """
        Prediction function for classification - returns class probabilities
        
        Args:
            texts: List of perturbed text samples
            
        Returns:
            Array of class probabilities
        """
        predictions = []
        
        for text in texts:
            try:
                output = await self.model_wrapper.generate(text, temperature=0.1)
                
                # Simple heuristic: use sentiment-like scoring based on text content
                # In a real implementation, you'd use actual model probabilities
                text_lower = output.text.lower()
                positive_words = ['good', 'great', 'excellent', 'positive', 'yes']
                negative_words = ['bad', 'terrible', 'negative', 'no', 'poor']
                
                pos_score = sum(1 for word in positive_words if word in text_lower)
                neg_score = sum(1 for word in negative_words if word in text_lower)
                
                if pos_score > neg_score:
                    predictions.append([0.2, 0.8])  # [negative_prob, positive_prob]
                else:
                    predictions.append([0.8, 0.2])
                
            except Exception as e:
                self.logger.warning(f"Error predicting for text: {e}")
                predictions.append([0.5, 0.5])  # Neutral prediction
        
        return np.array(predictions)
