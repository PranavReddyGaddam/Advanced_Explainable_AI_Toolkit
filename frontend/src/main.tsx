import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Mock data for development since backend isn't ready yet
// This can be removed once the backend is running
const mockData = {
  models: [
    {
      name: "cerebras/llama3.3-70b",
      provider: "Cerebras",
      capabilities: {
        logprobs: true,
        attention_weights: false,
        hidden_states: false,
        gradients: false
      },
      description: "Llama 3.3 70B model hosted on Cerebras"
    },
    {
      name: "qwen/qwen3-235b-a22b-2507", 
      provider: "Cerebras",
      capabilities: {
        logprobs: true,
        attention_weights: false,
        hidden_states: false,
        gradients: false
      },
      description: "Qwen3 235B model hosted on Cerebras"
    }
  ],
  methods: [
    {
      name: "lime",
      description: "Local Interpretable Model-agnostic Explanations",
      requires_internals: false,
      fallback_available: false,
      supported_models: ["all"]
    },
    {
      name: "shap", 
      description: "SHapley Additive exPlanations using game theory",
      requires_internals: false,
      fallback_available: false,
      supported_models: ["all"]
    },
    {
      name: "inseq",
      description: "In-sequence token attribution using gradients",
      requires_internals: true,
      fallback_available: true,
      supported_models: ["all"]
    },
    {
      name: "gaf",
      description: "Generalized Attention Flow analysis",
      requires_internals: true, 
      fallback_available: true,
      supported_models: ["all"]
    },
    {
      name: "contrast_cat",
      description: "Contrastive activation analysis",
      requires_internals: true,
      fallback_available: true, 
      supported_models: ["all"]
    },
    {
      name: "attribution_patching",
      description: "Causal attribution through layer-wise patching",
      requires_internals: true,
      fallback_available: true,
      supported_models: ["all"]
    },
    {
      name: "slalom",
      description: "Surrogate model with interpretable logic extraction",
      requires_internals: false,
      fallback_available: false,
      supported_models: ["all"]
    }
  ]
};

// Add mock data to window for development
if (process.env.NODE_ENV === 'development') {
  (window as any).__XAI_MOCK_DATA__ = mockData;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
