import numpy as np
import asyncio
from typing import List, Dict, Any, Tuple, Optional
import logging
import networkx as nx
import time
from collections import defaultdict

from .base_explainer import BaseExplainer
from ..schemas.models import Explanation, ExplanationMetadata, ModelCapabilities, GraphNode, GraphEdge, AttentionFlow


class GAFExplainer(BaseExplainer):
    """
    Generalized Attention Flow explainer - fallback implementation using token co-occurrence
    since attention weights are not available through OpenRouter API
    """
    
    def __init__(self, model_wrapper, flow_algorithm: str = "edmonds_karp", 
                 num_perturbations: int = 30, **kwargs):
        """
        Initialize GAF explainer with fallback methods
        
        Args:
            model_wrapper: Model wrapper instance
            flow_algorithm: Algorithm for max-flow computation
            num_perturbations: Number of perturbations for pseudo-attention construction
        """
        super().__init__(model_wrapper, **kwargs)
        self.flow_algorithm = flow_algorithm
        self.num_perturbations = num_perturbations
        
    @property
    def requires_internals(self) -> bool:
        """True GAF requires attention weights, but we use fallback"""
        return True
    
    @property
    def fallback_available(self) -> bool:
        """Pseudo-attention fallback is available"""
        return True
    
    async def _generate_perturbed_outputs(self, input_text: str) -> List[str]:
        """
        Generate perturbed outputs to understand token relationships
        
        Args:
            input_text: Original input text
            
        Returns:
            List of perturbed output texts
        """
        outputs = []
        tokens = input_text.split()
        
        # Original output
        original_output = await self.model_wrapper.generate(input_text, temperature=0.1)
        outputs.append(original_output.text)
        
        # Perturb each token and generate output
        for i in range(min(len(tokens), self.num_perturbations)):
            perturbed_tokens = tokens.copy()
            perturbed_tokens[i] = "MASK"
            perturbed_text = " ".join(perturbed_tokens)
            
            try:
                perturbed_output = await self.model_wrapper.generate(perturbed_text, temperature=0.1)
                outputs.append(perturbed_output.text)
            except Exception as e:
                self.logger.warning(f"Error generating perturbed output: {e}")
                outputs.append("")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return outputs
    
    def _build_pseudo_attention_graph(self, input_text: str, outputs: List[str]) -> nx.DiGraph:
        """
        Build pseudo-attention graph from input-output relationships
        
        Args:
            input_text: Original input text
            outputs: List of perturbed outputs
            
        Returns:
            Directed graph with pseudo-attention weights
        """
        tokens = input_text.split()
        graph = nx.DiGraph()
        
        # Add nodes for each token
        for i, token in enumerate(tokens):
            graph.add_node(f"token_{i}", label=token, position=i, layer=0)
        
        # Add source and sink nodes
        graph.add_node("source", label="SOURCE", layer=-1)
        graph.add_node("sink", label="SINK", layer=1)
        
        # Build co-occurrence matrix from outputs
        co_occurrence = defaultdict(lambda: defaultdict(float))
        
        for output in outputs:
            output_tokens = output.lower().split()
            for i, input_token in enumerate(tokens):
                for j, output_token in enumerate(output_tokens):
                    # Simple co-occurrence scoring
                    co_occurrence[i][j] += 1.0 / len(outputs)
        
        # Add edges based on co-occurrence
        max_cooccurrence = max([max(occ.values()) for occ in co_occurrence.values()] + [1.0])
        
        for i in range(len(tokens)):
            # Edge from source to token
            token_importance = sum(co_occurrence[i].values()) / max_cooccurrence
            graph.add_edge("source", f"token_{i}", weight=token_importance)
            
            # Edges between tokens based on sequential importance
            for j in range(len(tokens)):
                if i != j:
                    # Compute similarity based on shared output influence
                    shared_influence = set(co_occurrence[i].keys()) & set(co_occurrence[j].keys())
                    similarity = len(shared_influence) / max(len(tokens), 1)
                    
                    if similarity > 0.1:  # Threshold for edge creation
                        graph.add_edge(f"token_{i}", f"token_{j}", weight=similarity)
            
            # Edge from token to sink
            graph.add_edge(f"token_{i}", "sink", weight=token_importance)
        
        return graph
    
    def _compute_max_flow(self, graph: nx.DiGraph) -> Dict[str, float]:
        """
        Compute maximum flow from source to sink
        
        Args:
            graph: Input directed graph
            
        Returns:
            Dictionary of edge flows
        """
        try:
            # Create capacity graph (copy weights to capacities)
            capacity_graph = graph.copy()
            
            # Compute max flow
            flow_dict = nx.maximum_flow(
                capacity_graph, 
                "source", 
                "sink", 
                flow_func=getattr(nx, f"maximum_flow_{self.flow_algorithm}")
            )[1]
            
            # Extract edge flows
            edge_flows = {}
            for source, flows in flow_dict.items():
                for target, flow in flows.items():
                    if flow > 0:
                        edge_flows[f"{source}->{target}"] = flow
            
            return edge_flows
            
        except Exception as e:
            self.logger.error(f"Error computing max flow: {e}")
            return {}
    
    def _graph_to_schema_format(self, graph: nx.DiGraph, flow_dict: Dict[str, float]) -> AttentionFlow:
        """
        Convert NetworkX graph to schema format
        
        Args:
            graph: NetworkX directed graph
            flow_dict: Dictionary of edge flows
            
        Returns:
            AttentionFlow schema object
        """
        nodes = []
        edges = []
        
        # Convert nodes
        for node_id, node_data in graph.nodes(data=True):
            if node_id not in ["source", "sink"]:  # Skip special nodes
                node = GraphNode(
                    id=node_id,
                    label=node_data.get("label", ""),
                    layer=node_data.get("layer", 0),
                    position=node_data.get("position", 0),
                    importance=node_data.get("importance", 0.5)
                )
                nodes.append(node)
        
        # Convert edges with flow values
        for source, target, edge_data in graph.edges(data=True):
            if source not in ["source", "sink"] and target not in ["source", "sink"]:
                edge_key = f"{source}->{target}"
                flow = flow_dict.get(edge_key, edge_data.get("weight", 0.0))
                
                edge = GraphEdge(
                    source=source,
                    target=target,
                    weight=edge_data.get("weight", 0.0),
                    flow=flow
                )
                edges.append(edge)
        
        return AttentionFlow(nodes=nodes, edges=edges)
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        Generate GAF explanation using pseudo-attention fallback
        
        Args:
            input_text: Text to explain
            **kwargs: Additional parameters
            
        Returns:
            Explanation object with GAF results
        """
        start_time = time.time()
        self._validate_input(input_text)
        
        try:
            # Get model output for original text
            original_output = await self.model_wrapper.generate(input_text)
            
            # Generate perturbed outputs
            outputs = await self._generate_perturbed_outputs(input_text)
            
            # Build pseudo-attention graph
            graph = self._build_pseudo_attention_graph(input_text, outputs)
            
            # Compute max flow
            flow_dict = self._compute_max_flow(graph)
            
            # Convert to schema format
            attention_flow = self._graph_to_schema_format(graph, flow_dict)
            
            # Extract token importance scores from node importance
            tokens = input_text.split()
            scores = []
            
            for i, token in enumerate(tokens):
                node_id = f"token_{i}"
                if node_id in graph.nodes:
                    # Use flow through node as importance score
                    incoming_flow = sum(flow for (src, tgt), flow in flow_dict.items() 
                                      if tgt == node_id)
                    scores.append(min(incoming_flow, 1.0))
                else:
                    scores.append(0.5)  # Default importance
            
            # Normalize scores
            normalized_scores = self._normalize_scores(scores)
            
            # Create metadata
            metadata = ExplanationMetadata(
                execution_time=time.time() - start_time,
                num_samples=len(outputs),
                method_params={
                    'flow_algorithm': self.flow_algorithm,
                    'num_perturbations': self.num_perturbations,
                    'fallback_method': 'pseudo_attention_cooccurrence'
                },
                model_capabilities=ModelCapabilities(**self.model_capabilities)
            )
            
            # Create explanation object
            result = Explanation(
                model=self.model_wrapper.model_name,
                method='gaf',
                input_text=input_text,
                output_text=original_output.text,
                tokens=tokens,
                scores=normalized_scores,
                narrative=self._generate_gaf_narrative(result),
                metadata=metadata
            )
            
            # Add graph data
            from ..schemas.models import Graphs
            result.graphs = Graphs(attention_flow=attention_flow)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating GAF explanation: {e}")
            raise
    
    def _generate_gaf_narrative(self, explanation: Explanation) -> str:
        """Generate narrative for GAF explanations"""
        if explanation is None:
            return "GAF analysis being generated..."
        
        narrative = f"Generalized Attention Flow analysis (fallback: pseudo-attention from co-occurrence). "
        narrative += f"Since attention weights are not available through the API, constructed attention-like graph "
        narrative += f"from {self.num_perturbations} perturbed outputs using token co-occurrence patterns. "
        narrative += f"Applied {self.flow_algorithm} algorithm to compute maximum flow through the attention graph. "
        
        if explanation.graphs and explanation.graphs.attention_flow:
            num_nodes = len(explanation.graphs.attention_flow.nodes)
            num_edges = len(explanation.graphs.attention_flow.edges)
            narrative += f"The resulting graph contains {num_nodes} nodes and {num_edges} edges, "
            narrative += f"showing information flow paths through the model's 'attention' mechanism."
        
        return narrative


class TrueGAFExplainer(GAFExplainer):
    """
    Placeholder for true GAF implementation with real attention weights
    (would work with local models that expose attention)
    """
    
    @property
    def requires_internals(self) -> bool:
        """True GAF requires attention weights"""
        return True
    
    @property
    def fallback_available(self) -> bool:
        """Fallback to pseudo-attention is available"""
        return True
    
    async def explain(self, input_text: str, **kwargs) -> Explanation:
        """
        True GAF explanation with real attention weights
        
        Note: This would work with local models that can expose attention weights.
        For API models, it falls back to pseudo-attention.
        """
        if not self.model_capabilities.get("attention_weights", False):
            self.logger.info("Attention weights not available, falling back to pseudo-attention")
            return await super().explain(input_text, **kwargs)
        
        # Placeholder for true attention-based GAF computation
        # This would involve:
        # 1. Getting attention weights from all layers
        # 2. Constructing multi-layer attention graph
        # 3. Computing max flow through attention network
        
        self.logger.warning("True attention-based GAF not implemented yet, using fallback")
        return await super().explain(input_text, **kwargs)
