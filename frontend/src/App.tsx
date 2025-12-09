import React, { useState, useEffect, useCallback } from 'react';
import Heatmap from './components/Heatmap';
import JsonViewer from './components/JsonViewer';
import ResultsSplitView from './components/ResultsSplitView';
import TopRightTooltips from './components/TopRightTooltips';
import AI_Prompt from './components/kokonutui/ai-prompt';
import FloatingLines from './components/FloatingLines';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import apiService, { 
  createExplanationRequest
} from './services/api';
import {
  ModelInfo,
  MethodInfo,
  Explanation
} from './types';

// Multi-method state type
interface MethodExplanation {
  explanation: Explanation | null;
  loading: boolean;
  error: string | null;
}

interface ComparisonState {
  explanations: Record<string, MethodExplanation>;
  inputText: string;
  selectedApiModel: string;
  overallLoading: boolean;
}

// Error Boundary Component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{
          padding: '20px',
          border: '1px solid #f44336',
          borderRadius: '4px',
          backgroundColor: '#ffebee',
          color: '#c62828'
        }}>
          <h3>Something went wrong</h3>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}

// Main App Component
const App: React.FC = () => {
  const [state, setState] = useState<ComparisonState>({
    explanations: {},
    inputText: '',
    selectedApiModel: 'cerebras/llama3.3-70b',
    overallLoading: false
  });

  const [models, setModels] = useState<ModelInfo[]>([]);
  const [methods, setMethods] = useState<MethodInfo[]>([]);

  // Load available models and methods on mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [modelsData, methodsData] = await Promise.all([
          apiService.getAvailableModels(),
          apiService.getAvailableMethods()
        ]);
        setModels(modelsData);
        setMethods(methodsData);
        
        // Initialize explanation states
        const initialExplanations: Record<string, MethodExplanation> = {};
        methodsData.forEach(method => {
          initialExplanations[method.name] = {
            explanation: null,
            loading: false,
            error: null
          };
        });
        setState(prev => ({ ...prev, explanations: initialExplanations }));
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };

    loadInitialData();
  }, []);

  // Handle multi-method explanation generation
  const handleMultiMethodSubmit = useCallback(async (inputText: string, selectedModel: string) => {
    // Capture current API model selection
    const currentApiModel = selectedModel;
    
    setState(prev => ({ 
      ...prev, 
      inputText, 
      overallLoading: true,
      explanations: Object.keys(prev.explanations).reduce((acc, methodName) => ({
        ...acc,
        [methodName]: { explanation: null, loading: true, error: null }
      }), {} as Record<string, MethodExplanation>)
    }));

    // Get model routing for each method and make parallel calls
    const methodCalls = methods.map(async (method) => {
      try {
        // Auto-route: BERT for internal methods, API model for model-agnostic methods
        const selectedModel = method.requires_internals 
          ? 'huggingface/bert-base' 
          : currentApiModel;

        const request = createExplanationRequest(selectedModel, method.name, inputText);
        const explanation = await apiService.generateExplanation(request);
        
        // Debug: Log the response to see what we're getting
        console.log(`Response for ${method.name}:`, explanation);
        console.log(`Explanation object:`, explanation.explanation);

        return {
          methodName: method.name,
          explanation: explanation.explanation,
          error: null
        };
      } catch (error) {
        return {
          methodName: method.name,
          explanation: null,
          error: error instanceof Error ? error.message : 'Failed to generate explanation'
        };
      }
    });

    // Wait for all calls to complete
    const results = await Promise.all(methodCalls);
    
    // Update state with all results
    setState(prev => {
      const updatedExplanations = { ...prev.explanations };
      results.forEach(result => {
        updatedExplanations[result.methodName] = {
          explanation: result.explanation || null,
          loading: false,
          error: result.error
        };
      });
      
      return {
        ...prev,
        explanations: updatedExplanations,
        overallLoading: false
      };
    });
  }, [methods]);

  return (
    <ErrorBoundary>
      <TopRightTooltips 
        isProcessing={state.overallLoading} 
        hasInputText={!!state.inputText}
        hasExplanations={Object.keys(state.explanations).length > 0}
      />
      <div className="min-h-screen relative overflow-hidden">
        {/* Fixed Background */}
        <div className="fixed inset-0 z-0">
          <FloatingLines 
            linesGradient={['#e947f5', '#2f4ba2']}
            enabledWaves={['top', 'middle', 'bottom']}
            lineCount={[8, 6, 4]}
            animationSpeed={0.5}
            interactive={true}
            mixBlendMode="screen"
          />
        </div>

        {/* Content */}
        <div className="relative z-10">
          <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="text-center mb-16 pt-20">
              <h1 className="text-8xl font-bold text-white mb-4 drop-shadow-[0_4px_12px_rgba(0,0,0,0.8)] leading-tight">
                Uncover AI's Hidden Logic
              </h1>
              <p className="text-3xl text-white/90 drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)] font-medium">
                Compare 5 powerful XAI methods in real-time
              </p>
              <p className="text-xl text-white/80 drop-shadow-[0_1px_6px_rgba(0,0,0,0.5)] mt-2">
                Discover why your AI makes the decisions it does
              </p>
            </div>

            {/* AI Prompt Input */}
            <div className="flex justify-center mb-8">
              <AI_Prompt 
                onSubmit={handleMultiMethodSubmit}
                loading={state.overallLoading}
                models={models.filter(model => 
                  !model.capabilities.attention_weights && 
                  !model.capabilities.hidden_states && 
                  !model.capabilities.gradients
                )}
                selectedModel={state.selectedApiModel}
                onModelChange={(model) => setState(prev => ({ ...prev, selectedApiModel: model }))}
              />
            </div>

            {/* Method Comparison Tabs */}
            {state.inputText && (
              <div className="w-full px-8 py-6">
                <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/30 shadow-lg shadow-[0_0_20px_rgba(255,255,255,0.1)] overflow-hidden">
                  <Tabs defaultValue={methods[0]?.name} className="w-full">
                    <TabsList className="grid w-full grid-cols-5 bg-white/5 border-b border-white/20">
                      {methods.map((method) => (
                        <TabsTrigger 
                          key={method.name} 
                          value={method.name}
                          className="text-white/80 data-[state=active]:text-white data-[state=active]:bg-white/10 rounded-none border-r border-white/20 last:border-r-0 transition-all duration-200"
                        >
                          {method.name.toUpperCase()}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                    
                    {methods.map((method) => {
                      const methodExplanation = state.explanations[method.name] || {
                        explanation: null,
                        loading: false,
                        error: null
                      };
                      const { explanation, loading, error } = methodExplanation;

                      return (
                        <TabsContent key={method.name} value={method.name} className="p-6 m-0">
                          <div className="space-y-6">
                            {/* Loading State */}
                            {loading && (
                              <div className="flex items-center justify-center py-12">
                                <div className="text-center">
                                  <div className="animate-spin rounded-full h-12 w-12 border-2 border-cyan-500 border-t-transparent mx-auto mb-4"></div>
                                  <p className="text-white text-lg font-medium">Analyzing with {method.name}...</p>
                                </div>
                              </div>
                            )}

                            {/* Error State */}
                            {error && (
                              <div className="p-4 bg-red-500/30 backdrop-blur-sm border border-red-500/40 rounded-lg text-red-200">
                                <p className="font-medium mb-2">Error occurred</p>
                                <p className="text-sm">{error}</p>
                              </div>
                            )}

                            {/* Results Display */}
                            {explanation && !loading && (
                              <div className="space-y-6">
                                {/* Split View: Attention Flow + AI Response */}
                                <ResultsSplitView explanation={explanation} />

                                {/* Token Importance Section */}
                                {explanation.scores && explanation.scores.length > 0 && (
                                  <div>
                                    <h3 className="text-xl font-bold text-white mb-3">Token Importance Analysis</h3>
                                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                                      <Heatmap 
                                        tokens={explanation.tokens} 
                                        scores={explanation.scores}
                                        method={explanation.method}
                                      />
                                    </div>
                                  </div>
                                )}

                                {/* Details Section */}
                                {explanation.metadata && (
                                  <div>
                                    <h3 className="text-xl font-bold text-white mb-3">Technical Details</h3>
                                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 max-h-96 overflow-y-auto">
                                      <JsonViewer data={explanation.metadata} />
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </TabsContent>
                      );
                    })}
                  </Tabs>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default App;
