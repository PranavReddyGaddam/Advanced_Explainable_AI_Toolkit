// XAI Toolkit TypeScript Type Definitions

export interface GraphNode {
  id: string;
  label?: string;
  importance?: number;
  layer?: number;
  position?: number;
  node_type?: 'token' | 'layer' | 'head';
  causal_strength?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight?: number;
  flow?: number;
  attribution?: number;
}

export interface AttentionFlow {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CausalGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Graphs {
  attention_flow?: AttentionFlow;
  causal_graph?: CausalGraph;
}

export interface LogicSegment {
  condition: string;
  weight: number;
  confidence: number;
  tokens: string[];
}

export interface SurrogateLogic {
  segments: LogicSegment[];
  accuracy?: number;
  correlation?: number;
}

export interface ContrastScore {
  token: string;
  contrast_value: number;
  baseline_activation?: number;
  contrast_activation?: number;
}

export interface ModelCapabilities {
  logprobs: boolean;
  attention_weights: boolean;
  hidden_states: boolean;
  gradients: boolean;
}

export interface ExplanationMetadata {
  execution_time?: number;
  num_samples?: number;
  method_params: Record<string, any>;
  model_capabilities?: ModelCapabilities;
}

export interface Explanation {
  model: string;
  method: string;
  input_text: string;
  output_text: string;
  tokens: string[];
  scores: number[];
  graphs?: Graphs;
  surrogate_logic?: SurrogateLogic;
  contrast_scores?: ContrastScore[];
  narrative?: string;
  metadata?: ExplanationMetadata;
}

export interface ExplanationRequest {
  model: string;
  method: string;
  input_text: string;
  method_params?: Record<string, any>;
}

export interface ExplanationResponse {
  success: boolean;
  explanation?: Explanation;
  error?: string;
  execution_time?: number;
}

export interface ModelInfo {
  name: string;
  provider: string;
  capabilities: ModelCapabilities;
  description?: string;
}

export interface MethodInfo {
  name: string;
  description: string;
  requires_internals: boolean;
  fallback_available: boolean;
  supported_models: string[];
}

// Component Props Types
export interface HeatmapProps {
  tokens: string[];
  scores: number[];
  method: string;
  width?: number;
  height?: number;
}

export interface NodeGraphProps {
  graphData: AttentionFlow | CausalGraph;
  width?: number;
  height?: number;
}

export interface JsonViewerProps {
  data: any;
  expanded?: boolean;
}

export interface NarrativePanelProps {
  narrative: string;
  metadata?: ExplanationMetadata;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// UI State Types
export type ViewMode = 'heatmap' | 'graph' | 'json' | 'narrative';

export interface AppState {
  explanation: Explanation | null;
  loading: boolean;
  error: string | null;
  selectedModel: string;
  selectedMethod: string;
  inputText: string;
  viewMode: ViewMode;
}

// Color Scale Types
export interface ColorScale {
  (value: number): string;
  domain(): number[];
  range(): string[];
}

// D3.js Types (simplified)
export interface D3Selection {
  select(selector: string): any;
  selectAll(selector: string): any;
  data<T>(data: T[]): any;
  enter(): any;
  append(name: string): any;
  attr(name: string, value: any): any;
  style(name: string, value: any): any;
  text(value: any): any;
  on(event: string, handler: Function): any;
}

export interface SimulationNode extends GraphNode {
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
}

export interface SimulationLink {
  source: string | SimulationNode;
  target: string | SimulationNode;
  weight?: number;
  flow?: number;
  attribution?: number;
}
