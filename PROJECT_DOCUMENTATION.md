# XAI (Explainable AI) Visualization Platform - Technical Documentation

## Project Overview

This project is a comprehensive Explainable AI (XAI) visualization platform that allows users to compare multiple XAI methods in real-time. The platform provides interactive visualizations including attention flow graphs, token importance heatmaps, and detailed explanations for AI model decisions.

## Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom glass morphism effects
- **State Management**: React useState and useCallback hooks
- **Routing**: React Router DOM (previously implemented, later removed)
- **Animation**: Framer Motion for animated tooltips
- **Visualization**: D3.js for force-directed graphs, Recharts for heatmaps

### Backend Architecture
- **Framework**: FastAPI with Python
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Model Integration**: OpenRouter API for external LLM access
- **Data Validation**: Pydantic models for request/response schemas
- **Async Processing**: Full async/await support for concurrent operations

## Technical Components

### Frontend Components

#### Core Application Components
- **App.tsx**: Main application container with error boundary
- **AI_Prompt.tsx**: Interactive input component with persistent prompt functionality
- **ResultsSplitView.tsx**: Split-pane layout for attention flow graph and AI response
- **FloatingLines.tsx**: Three.js based animated background effects
- **TopRightTooltips.tsx**: Animated team member tooltips with conditional visibility

#### Visualization Components
- **NodeGraph.tsx**: D3.js force-directed graph for attention flow visualization
  - Dynamic node sizing based on importance scores
  - Interactive tooltips with node details
  - Zoom and pan capabilities
  - Method-specific edge weight calculations
- **Heatmap.tsx**: Token importance bar chart using Recharts
  - Responsive container with 500px height
  - Color-coded importance gradients
  - Horizontal layout for better token readability
- **JsonViewer.tsx**: Collapsible JSON display for technical details

#### UI Components
- **AnimatedTooltip.tsx**: Framer Motion powered tooltip with spring animations
- **Tabs.tsx**: Method comparison interface
- **ErrorBoundary.tsx**: React error boundary for graceful error handling

### Backend Components

#### API Endpoints
- **GET /api/models**: Retrieve available AI models with capabilities
- **GET /api/methods**: Get supported XAI methods and their requirements
- **POST /api/explain**: Generate explanations using specified XAI method

#### Model Integration
- **OpenRouter Integration**: External LLM API access with proper session management
- **Internal Model Support**: HuggingFace BERT for mock explanations
- **Model Registry**: Dynamic model provider registration system

#### XAI Methods Implementation
- **LIME**: Local Interpretable Model-agnostic Explanations
- **SHAP**: SHapley Additive exPlanations using game theory
- **InSeq**: In-sequence token attribution using gradients
- **GAF**: Generalized Attention Flow analysis
- **Contrastive Category**: Contrastive activation analysis
- **Attribution Patching**: Causal attribution through layer-wise patching
- **Slalom**: Surrogate model with interpretable logic extraction

## Data Flow Architecture

### Request Processing Pipeline
1. **Input Collection**: User enters prompt via AI_Prompt component
2. **Method Selection**: User chooses XAI method(s) for comparison
3. **Model Selection**: User selects target AI model
4. **API Request**: Frontend sends POST request to /api/explain
5. **Backend Processing**: 
   - Tokenization of input text
   - Model inference via OpenRouter or internal models
   - XAI method application with importance scoring
   - Graph generation based on token importance
6. **Response Generation**: Comprehensive explanation with visualizations
7. **Frontend Rendering**: Dynamic visualization of results

### State Management
- **ComparisonState**: Manages explanations, input text, model selection, and loading states
- **Multi-method Support**: Simultaneous comparison of multiple XAI methods
- **Real-time Updates**: Dynamic UI updates during processing

## Visualization Techniques

### Attention Flow Graphs
- **Force-directed layout**: D3.js simulation with customizable physics
- **Node Importance**: Size-based visualization using actual importance scores
- **Edge Weights**: Method-specific attention pattern calculations
- **Interactive Features**: Hover tooltips, zoom controls, node selection

### Token Importance Heatmaps
- **Bar Chart Layout**: Horizontal orientation for better token readability
- **Color Gradients**: Multi-color importance scale (green to red)
- **Responsive Design**: Dynamic sizing with 500px height constraint
- **Data Processing**: Top token filtering for performance optimization

### Graph Generation Algorithms
```python
# Method-specific attention patterns
def create_attention_graph(tokens, scores, method):
    if method.lower() == "lime":
        # Stronger connections to similar importance levels
        weight = 1.0 - abs(source_importance - target_importance)
    elif method.lower() == "shap":
        # Forward attention with decay
        weight = source_importance * (0.8 ** (j - i))
    elif method.lower() == "contrast_cat":
        # Strong categorical connections
        weight = max(source_importance, target_importance) * 0.7
    # ... additional method-specific patterns
```

## Technical Implementation Details

### Frontend Technical Stack
- **React 18**: Latest React features including concurrent rendering
- **TypeScript**: Full type safety with custom interfaces and enums
- **Vite**: Fast development server and optimized builds
- **Tailwind CSS**: Utility-first styling with custom configurations
- **Three.js**: 3D graphics for animated backgrounds
- **D3.js**: Data-driven visualizations with force simulations
- **Recharts**: React-based charting library
- **Framer Motion**: Production-ready animations

### Backend Technical Stack
- **FastAPI**: Modern async web framework with automatic documentation
- **Pydantic**: Data validation and serialization
- **OpenRouter API**: External LLM integration with proper async handling
- **aiohttp**: Async HTTP client for API calls
- **Python 3.8+**: Async/await support and type hints

### Performance Optimizations
- **Concurrent Processing**: Parallel API calls for multiple methods
- **Token Filtering**: Top 15 most important tokens for graph visualization
- **Lazy Loading**: Components load data only when needed
- **Memory Management**: Proper cleanup of D3.js visualizations and HTTP sessions
- **Responsive Design**: Dynamic sizing based on viewport constraints

## Data Structures

### Frontend Types
```typescript
interface Explanation {
  model: string;
  method: string;
  input_text: string;
  output_text: string;
  tokens: string[];
  scores: number[];
  narrative: string;
  metadata: Record<string, any>;
  graphs?: Graphs;
}

interface Graphs {
  attention_flow?: AttentionFlow;
  causal_graph?: CausalGraph;
}
```

### Backend Schemas
```python
class ExplanationRequest(BaseModel):
    model: str
    method: str
    input_text: str
    parameters: Optional[Dict[str, Any]] = None

class GraphNode(BaseModel):
    id: str
    label: str
    importance: float
    node_type: str
    layer: int
    position: int
    causal_strength: float
```

## API Specification

### Models Endpoint
- **URL**: GET /api/models
- **Response**: List of available models with capabilities
- **Capabilities Include**: logprobs, attention_weights, hidden_states, gradients

### Methods Endpoint
- **URL**: GET /api/methods
- **Response**: List of XAI methods with requirements
- **Method Properties**: requires_internals, fallback_available, supported_models

### Explanation Endpoint
- **URL**: POST /api/explain
- **Request**: model, method, input_text, optional parameters
- **Response**: Complete explanation with visualizations
- **Processing Time**: Typically 1-3 seconds per method

## Error Handling

### Frontend Error Handling
- **Error Boundary**: Catches React component errors
- **API Error Handling**: User-friendly error messages
- **Loading States**: Visual feedback during processing
- **Validation**: Input validation before API calls

### Backend Error Handling
- **HTTPException**: Proper HTTP status codes
- **Validation Errors**: Pydantic validation with detailed messages
- **API Failures**: Graceful fallback for external API issues
- **Resource Cleanup**: Proper session and connection management

## Development Setup

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

### Environment Configuration
- **Frontend**: Vite environment variables
- **Backend**: .env file with OpenRouter API key
- **Development**: Mock data for offline development

## Security Considerations

### API Security
- **API Key Management**: Secure storage of OpenRouter credentials
- **Input Validation**: Sanitization of user inputs
- **Rate Limiting**: Protection against API abuse
- **CORS Configuration**: Proper cross-origin resource sharing

### Data Privacy
- **No Data Persistence**: No storage of user prompts or results
- **API Security**: Secure transmission to external APIs
- **Session Management**: Proper cleanup of HTTP sessions

## Deployment Architecture

### Frontend Deployment
- **Build Process**: Vite production build with optimizations
- **Static Assets**: Optimized JavaScript and CSS bundles
- **Environment Configuration**: Production environment variables

### Backend Deployment
- **Container Support**: Docker-ready configuration
- **API Documentation**: Automatic Swagger/OpenAPI generation
- **Health Checks**: Application health monitoring endpoints

## Future Enhancements

### Planned Features
- **Additional XAI Methods**: Integration of more explanation techniques
- **Model Comparison**: Side-by-side model analysis
- **Export Functionality**: PDF/CSV export of explanations
- **Collaboration Features**: Shared explanation sessions
- **Advanced Visualizations**: 3D attention patterns, temporal analysis

### Technical Improvements
- **Caching Layer**: Redis for API response caching
- **Database Integration**: PostgreSQL for explanation history
- **Microservices Architecture**: Separate services for scaling
- **Real-time Updates**: WebSocket for live processing updates

## Testing Strategy

### Frontend Testing
- **Unit Tests**: Component testing with React Testing Library
- **Integration Tests**: API integration testing
- **Visual Testing**: Screenshot testing for UI components

### Backend Testing
- **Unit Tests**: Pydantic model validation
- **Integration Tests**: API endpoint testing
- **Load Testing**: Performance testing under load

## Performance Metrics

### Frontend Performance
- **Bundle Size**: Optimized JavaScript bundles
- **Load Time**: < 2 seconds initial load
- **Interaction Response**: < 100ms UI updates

### Backend Performance
- **API Response Time**: < 3 seconds for explanations
- **Concurrent Requests**: Support for multiple simultaneous requests
- **Memory Usage**: Efficient resource management

## Code Quality Standards

### TypeScript Standards
- **Strict Type Checking**: Full TypeScript strict mode
- **Interface Definitions**: Comprehensive type definitions
- **ESLint Configuration**: Code quality enforcement

### Python Standards
- **Type Hints**: Full type annotation coverage
- **Code Formatting**: Black code formatter
- **Linting**: Flake8 for code quality

This documentation provides a comprehensive overview of the XAI Visualization Platform's technical architecture, implementation details, and operational characteristics for team reporting and development purposes.
