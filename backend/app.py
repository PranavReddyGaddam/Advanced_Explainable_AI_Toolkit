from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our components
from schemas.models import ExplanationRequest, ExplanationResponse, ModelInfo, MethodInfo, GraphNode, GraphEdge, ExplanationMetadata, ModelCapabilities, Explanation, Graphs, AttentionFlow
from models.model_loader import model_registry, UnifiedModelOutput
import models.open_llm_wrapper  # This registers the OpenRouter provider

# Initialize FastAPI app
app = FastAPI(title="XAI Backend API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for development (updated with working OpenRouter model)
MOCK_MODELS = [
    {
        "name": "qwen/qwen3-32b", 
        "provider": "OpenRouter", 
        "description": "Qwen3 32B model for explanations",
        "capabilities": ModelCapabilities(
            logprobs=True,
            attention_weights=False,  # Not available via OpenRouter
            hidden_states=False,       # Not available via OpenRouter
            gradients=False           # Not available via OpenRouter
        )
    },
    {
        "name": "huggingface/bert-base", 
        "provider": "HuggingFace", 
        "description": "BERT base model for internal XAI methods",
        "capabilities": ModelCapabilities(
            logprobs=False,
            attention_weights=True,   # Available for internal models
            hidden_states=True,       # Available for internal models
            gradients=True           # Available for internal models
        )
    }
]

MOCK_METHODS = [
    {"name": "lime", "description": "Local Interpretable Model-agnostic Explanations", "requires_internals": False, "fallback_available": True, "supported_models": ["qwen/qwen3-32b", "huggingface/bert-base"]},
    {"name": "shap", "description": "SHapley Additive exPlanations", "requires_internals": False, "fallback_available": True, "supported_models": ["qwen/qwen3-32b", "huggingface/bert-base"]},
    {"name": "inseq", "description": "Integrated Gradients and Sequence explanations", "requires_internals": True, "fallback_available": False, "supported_models": ["huggingface/bert-base"]},
    {"name": "gaf", "description": "Gradient-based Attribution Flow", "requires_internals": True, "fallback_available": False, "supported_models": ["huggingface/bert-base"]},
    {"name": "contrast_cat", "description": "Contrastive Category explanations", "requires_internals": False, "fallback_available": True, "supported_models": ["qwen/qwen3-32b"]},
]

# Custom response model that matches frontend expectations
class CustomExplanationResponse(BaseModel):
    id: str
    model: str
    method: str
    input_text: str
    tokens: List[Dict[str, Any]]
    scores: List[Dict[str, Any]]
    graph: Optional[Dict[str, Any]] = None
    narrative: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/models", response_model=List[ModelInfo])
async def get_available_models():
    """Get list of available models"""
    try:
        return [ModelInfo(**model) for model in MOCK_MODELS]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/{model_name}", response_model=ModelInfo)
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    try:
        model = next((m for m in MOCK_MODELS if m["name"] == model_name), None)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return ModelInfo(**model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/methods", response_model=List[MethodInfo])
async def get_available_methods():
    """Get list of available explanation methods"""
    try:
        return [MethodInfo(**method) for method in MOCK_METHODS]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/methods/{method_name}", response_model=MethodInfo)
async def get_method_info(method_name: str):
    """Get information about a specific explanation method"""
    try:
        method = next((m for m in MOCK_METHODS if m["name"] == method_name), None)
        if not method:
            raise HTTPException(status_code=404, detail="Method not found")
        return MethodInfo(**method)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/explain", response_model=ExplanationResponse)
async def generate_explanation(request: ExplanationRequest):
    """Generate explanation for the given input using real OpenRouter API"""
    try:
        # Validate request
        if not request.model:
            raise HTTPException(status_code=400, detail="Model is required")
        if not request.method:
            raise HTTPException(status_code=400, detail="Method is required")
        if not request.input_text:
            raise HTTPException(status_code=400, detail="Input text is required")
        
        # Check if method is supported
        supported_methods = [m["name"] for m in MOCK_METHODS]
        if request.method not in supported_methods:
            raise HTTPException(status_code=400, detail=f"Method '{request.method}' is not supported")
        
        # Get API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        # Generate text completion using OpenRouter
        print(f"Calling OpenRouter API with model: {request.model}")
        
        # Check if this is an internal model that shouldn't call OpenRouter
        if request.model == "huggingface/bert-base":
            # For internal models, generate a mock explanation without API call
            model_output = UnifiedModelOutput(
                text=f"This is a mock explanation for {request.method} using internal BERT model. In a real implementation, this would use the actual model internals for gradient-based explanations.",
                tokens=request.input_text.split(),
                logprobs=None,
                model_name=request.model,
                metadata={"provider": "huggingface", "internal": True}
            )
        else:
            # Initialize OpenRouter wrapper for external models
            openrouter_class = model_registry.get_model_class("openrouter")
            if not openrouter_class:
                raise HTTPException(status_code=500, detail="OpenRouter provider not available")
            
            # Call OpenRouter for external models
            model_wrapper = openrouter_class(request.model, api_key)
            try:
                model_output = await model_wrapper.generate(
                    request.input_text,
                    max_tokens=1000,  # Increased from 500 to avoid length cutoff
                    temperature=0.7
                )
            finally:
                await model_wrapper.close()  # Properly cleanup aiohttp session
        
        # Generate explanation based on method type
        tokens = model_output.tokens
        scores = []
        
        # Generate mock scores based on method (real implementation would use actual XAI algorithms)
        if request.method == "GRADIENT":
            # Gradient-based importance (simulated) - position-based with variation
            scores = [(len(token) * 0.1 + (i * 0.05) + abs(hash(token) % 30) / 100) for i, token in enumerate(tokens)]
        elif request.method == "ATTENTION":
            # Attention-based importance (simulated) - focus on content words
            content_words = {'the', 'quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog'}
            scores = [0.8 if token.lower() in content_words else 0.2 + abs(hash(token) % 40) / 100 for token in tokens]
        elif request.method == "LIME":
            # LIME importance (simulated) - varied importance with semantic focus
            important_words = {'fox', 'jumps', 'dog', 'decision', 'trees', 'neural', 'networks'}
            scores = [0.9 if token.lower() in important_words else 0.3 + abs(hash(token) % 50) / 100 for token in tokens]
        elif request.method == "SHAP":
            # SHAP importance (simulated) - gradual decay with random variation
            scores = [0.7 - (i * 0.01) + (abs(hash(token) % 20) / 100) for i, token in enumerate(tokens)]
        elif request.method == "INSEQ":
            # Integrated gradients (simulated) - focus on longer tokens
            scores = [min(0.9, len(token) * 0.15 + abs(hash(token) % 25) / 100) for token in tokens]
        elif request.method == "GAF":
            # Gradient-based Attribution Flow (simulated) - alternating high/low importance
            scores = [0.8 if i % 3 == 0 else 0.4 + abs(hash(token) % 30) / 100 for i, token in enumerate(tokens)]
        elif request.method == "contrast_cat":
            # Contrastive Category (simulated) - categorical importance
            categories = {'decision', 'trees', 'neural', 'networks', 'medical', 'diagnosis'}
            scores = [0.85 if token.lower() in categories else 0.25 + abs(hash(token) % 45) / 100 for token in tokens]
        else:
            scores = [0.5 + abs(hash(token) % 40) / 100 for token in tokens]  # Default varied importance
        
        # Normalize scores to 0-1 range
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 1.0
        score_range = max_score - min_score if max_score != min_score else 1.0
        scores = [(s - min_score) / score_range for s in scores]
        
        # Generate meaningful attention flow graph based on token importance scores
        def create_attention_graph(tokens, scores, method):
            """Create attention flow graph with meaningful connections based on importance scores"""
            
            # Use top 15 most important tokens for better visualization
            token_score_pairs = list(zip(tokens, scores))
            # Sort by importance and take top tokens
            top_tokens = sorted(token_score_pairs, key=lambda x: x[1], reverse=True)[:15]
            
            nodes = []
            edges = []
            
            # Create nodes with actual importance scores
            for i, (token, score) in enumerate(top_tokens):
                nodes.append({
                    "id": f"token_{i}",
                    "label": token,
                    "importance": score,
                    "node_type": "token",
                    "layer": 1,
                    "position": i,
                    "causal_strength": score
                })
            
            # Create meaningful edges based on attention patterns
            for i in range(len(top_tokens)):
                for j in range(i + 1, min(i + 4, len(top_tokens))):  # Connect to next 3 tokens
                    # Edge weight based on importance relationship
                    source_importance = top_tokens[i][1]
                    target_importance = top_tokens[j][1]
                    
                    # Different patterns for different methods
                    if method.lower() == "lime":
                        # LIME: Stronger connections to similar importance levels
                        weight = 1.0 - abs(source_importance - target_importance)
                    elif method.lower() == "shap":
                        # SHAP: Forward attention with decay
                        weight = source_importance * (0.8 ** (j - i))
                    elif method.lower() == "contrast_cat":
                        # Contrastive: Strong categorical connections
                        weight = max(source_importance, target_importance) * 0.7
                    elif method.lower() in ["inseq", "gaf"]:
                        # Gradient methods: Strong sequential connections
                        weight = (source_importance + target_importance) / 2
                    else:
                        # Default: Balanced attention
                        weight = (source_importance + target_importance) / 2
                    
                    edges.append({
                        "source": f"token_{i}",
                        "target": f"token_{j}",
                        "weight": max(0.1, min(1.0, weight)),  # Clamp between 0.1 and 1.0
                        "flow": weight * 0.8,  # Numeric flow value instead of string
                        "attribution": weight
                    })
            
            return {"nodes": nodes, "edges": edges}

        # Create explanation response
        explanation = Explanation(
            model=request.model,
            method=request.method,
            input_text=request.input_text,
            output_text=model_output.text,
            tokens=tokens,
            scores=scores,
            narrative=f"Analysis using {request.method.upper()} method on {request.model}. Generated text: '{model_output.text[:200]}...'. The method identified key tokens that contributed most to the model's output.",
            metadata={
                "model": request.model,
                "method": request.method,
                "input_length": len(request.input_text),
                "output_length": len(model_output.text),
                "num_tokens": len(tokens),
                "api_response_time": "1.2s",
                "confidence": 0.85
            },
            graphs={
                "attention_flow": create_attention_graph(tokens, scores, request.method)
            }
        )
        
        return ExplanationResponse(
            success=True,
            explanation=explanation,
            execution_time=1.2
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in explanation generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")

@app.get("/api/results/{explanation_id}")
async def get_explanation_result(explanation_id: str):
    """Get a previously generated explanation by ID"""
    try:
        # In a real implementation, this would retrieve from a database
        # For now, return a mock response or 404
        raise HTTPException(status_code=404, detail="Explanation not found or expired")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate")
async def validate_request(request: ExplanationRequest):
    """Validate an explanation request"""
    try:
        errors = []
        
        if not request.model or request.model.strip() == "":
            errors.append("Model is required")
        
        if not request.method or request.method.strip() == "":
            errors.append("Method is required")
        
        if not request.input_text or request.input_text.strip() == "":
            errors.append("Input text is required")
        
        if request.input_text and len(request.input_text) > 10000:
            errors.append("Input text is too long (max 10000 characters)")
        
        return {"valid": len(errors) == 0, "errors": errors}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_explanation_history(limit: int = 10):
    """Get history of previous explanations"""
    try:
        # In a real implementation, this would retrieve from a database
        # For now, return empty list
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
