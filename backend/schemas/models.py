from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
import json


class GraphNode(BaseModel):
    """Node in attention or causal graph"""
    id: str
    label: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0, le=1)
    layer: Optional[int] = None
    position: Optional[int] = None
    node_type: Optional[str] = None  # For causal graphs: "token", "layer", "head"
    causal_strength: Optional[float] = Field(None, ge=0, le=1)


class GraphEdge(BaseModel):
    """Edge in attention or causal graph"""
    source: str
    target: str
    weight: Optional[float] = Field(None, ge=0)
    flow: Optional[float] = Field(None, ge=0)
    attribution: Optional[float] = Field(None, ge=0)


class AttentionFlow(BaseModel):
    """Attention flow graph structure"""
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []


class CausalGraph(BaseModel):
    """Causal attribution graph structure"""
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []


class Graphs(BaseModel):
    """Container for all graph structures"""
    attention_flow: Optional[AttentionFlow] = None
    causal_graph: Optional[CausalGraph] = None


class LogicSegment(BaseModel):
    """Logic segment from SLALOM surrogate model"""
    condition: str
    weight: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    tokens: List[str] = []


class SurrogateLogic(BaseModel):
    """SLALOM surrogate model logic"""
    segments: List[LogicSegment] = []
    accuracy: Optional[float] = Field(None, ge=0, le=1)
    correlation: Optional[float] = Field(None, ge=-1, le=1)


class ContrastScore(BaseModel):
    """Contrast-CAT score for individual token"""
    token: str
    contrast_value: float
    baseline_activation: Optional[float] = None
    contrast_activation: Optional[float] = None


class ModelCapabilities(BaseModel):
    """Model capability flags"""
    logprobs: bool = False
    attention_weights: bool = False
    hidden_states: bool = False
    gradients: bool = False


class ExplanationMetadata(BaseModel):
    """Metadata for explanation results"""
    execution_time: Optional[float] = None
    num_samples: Optional[int] = None
    method_params: Dict[str, Any] = {}
    model_capabilities: Optional[ModelCapabilities] = None


class Explanation(BaseModel):
    """Main explanation output structure"""
    model: str
    method: str
    input_text: str
    output_text: str
    tokens: List[str]
    scores: List[float]
    
    # Optional fields for different methods
    graphs: Optional[Graphs] = None
    surrogate_logic: Optional[SurrogateLogic] = None
    contrast_scores: Optional[List[ContrastScore]] = None
    narrative: Optional[str] = None
    metadata: Optional[ExplanationMetadata] = None
    
    @validator('scores')
    def scores_match_tokens(cls, v, values):
        if 'tokens' in values and len(v) != len(values['tokens']):
            raise ValueError('Scores length must match tokens length')
        return v
    
    @validator('tokens')
    def tokens_not_empty(cls, v):
        if not v:
            raise ValueError('Tokens cannot be empty')
        return v
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return self.json(indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Explanation':
        """Create from JSON string"""
        return cls.parse_raw(json_str)
    
    @classmethod
    def validate_schema(cls, data: Dict[str, Any]) -> 'Explanation':
        """Validate and create from dictionary"""
        return cls(**data)


class ExplanationRequest(BaseModel):
    """Request structure for explanation API"""
    model: str
    method: str
    input_text: str
    method_params: Dict[str, Any] = {}
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = [
            'lime', 'shap', 'inseq', 'gaf', 
            'contrast_cat', 'attribution_patching', 'slalom'
        ]
        if v not in allowed_methods:
            raise ValueError(f'Method must be one of: {allowed_methods}')
        return v


class ExplanationResponse(BaseModel):
    """Response structure for explanation API"""
    success: bool
    explanation: Optional[Explanation] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class ModelInfo(BaseModel):
    """Model information for API endpoints"""
    name: str
    provider: str
    capabilities: ModelCapabilities
    description: Optional[str] = None


class MethodInfo(BaseModel):
    """Method information for API endpoints"""
    name: str
    description: str
    requires_internals: bool
    fallback_available: bool
    supported_models: List[str] = []
