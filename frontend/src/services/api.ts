import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  ExplanationRequest,
  ExplanationResponse,
  ModelInfo,
  MethodInfo
} from '../types';

class ApiService {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      timeout: 300000, // 5 minutes timeout for long explanations
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: any): Error {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data?.error || error.response.data?.detail || 'Unknown server error';
      
      switch (status) {
        case 400:
          return new Error(`Bad Request: ${message}`);
        case 401:
          return new Error('Unauthorized: Please check your API credentials');
        case 403:
          return new Error('Forbidden: You do not have permission to perform this action');
        case 404:
          return new Error('Not Found: The requested resource does not exist');
        case 429:
          return new Error('Rate Limit Exceeded: Please wait before making another request');
        case 500:
          return new Error(`Server Error: ${message}`);
        case 502:
          return new Error('Bad Gateway: The server is temporarily unavailable');
        case 503:
          return new Error('Service Unavailable: The server is currently down');
        default:
          return new Error(`HTTP Error ${status}: ${message}`);
      }
    } else if (error.request) {
      // Request was made but no response received
      return new Error('Network Error: Unable to connect to the server. Please check your internet connection.');
    } else {
      // Something else happened
      return new Error(`Request Error: ${error.message}`);
    }
  }

  // Explanation endpoints
  async generateExplanation(request: ExplanationRequest): Promise<ExplanationResponse> {
    try {
      const response: AxiosResponse<ExplanationResponse> = await this.client.post(
        '/api/explain',
        request
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getExplanation(explanationId: string): Promise<ExplanationResponse> {
    try {
      const response: AxiosResponse<ExplanationResponse> = await this.client.get(
        `/api/results/${explanationId}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Model endpoints
  async getAvailableModels(): Promise<ModelInfo[]> {
    try {
      const response: AxiosResponse<ModelInfo[]> = await this.client.get(
        '/api/models'
      );
      return response.data;
    } catch (error) {
      // Fall back to mock data in development
      if (process.env.NODE_ENV === 'development' && (window as any).__XAI_MOCK_DATA__) {
        console.warn('Using mock models data due to API unavailability');
        return (window as any).__XAI_MOCK_DATA__.models;
      }
      throw error;
    }
  }

  async getModelInfo(modelName: string): Promise<ModelInfo> {
    try {
      const response: AxiosResponse<ModelInfo> = await this.client.get(
        `/api/models/${modelName}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Method endpoints
  async getAvailableMethods(): Promise<MethodInfo[]> {
    try {
      const response: AxiosResponse<MethodInfo[]> = await this.client.get(
        '/api/methods'
      );
      return response.data;
    } catch (error) {
      // Fall back to mock data in development
      if (process.env.NODE_ENV === 'development' && (window as any).__XAI_MOCK_DATA__) {
        console.warn('Using mock methods data due to API unavailability');
        return (window as any).__XAI_MOCK_DATA__.methods;
      }
      throw error;
    }
  }

  async getMethodInfo(methodName: string): Promise<MethodInfo> {
    try {
      const response: AxiosResponse<MethodInfo> = await this.client.get(
        `/api/methods/${methodName}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await this.client.get('/api/health');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Utility methods
  async validateRequest(request: ExplanationRequest): Promise<boolean> {
    try {
      const response = await this.client.post('/api/validate', request);
      return response.data.valid;
    } catch (error) {
      return false;
    }
  }

  async getExplanationHistory(limit: number = 10): Promise<ExplanationResponse[]> {
    try {
      const response: AxiosResponse<ExplanationResponse[]> = await this.client.get(
        `/api/history?limit=${limit}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Cancel ongoing request (if supported)
  cancelRequest(requestId: string): void {
    // Implementation depends on how request cancellation is handled on the backend
    console.log(`Cancelling request: ${requestId}`);
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;

// Export types for external use
export type { ApiService };

// Helper functions for common operations
export const createExplanationRequest = (
  model: string,
  method: string,
  inputText: string,
  methodParams: Record<string, any> = {}
): ExplanationRequest => ({
  model,
  method,
  input_text: inputText,
  method_params: methodParams,
});

export const validateExplanationRequest = (request: ExplanationRequest): string[] => {
  const errors: string[] = [];
  
  if (!request.model || request.model.trim() === '') {
    errors.push('Model is required');
  }
  
  if (!request.method || request.method.trim() === '') {
    errors.push('Method is required');
  }
  
  if (!request.input_text || request.input_text.trim() === '') {
    errors.push('Input text is required');
  }
  
  if (request.input_text && request.input_text.length > 10000) {
    errors.push('Input text is too long (max 10000 characters)');
  }
  
  return errors;
};

// Constants for API configuration
export const API_CONFIG = {
  TIMEOUT: 300000, // 5 minutes
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
  MAX_INPUT_LENGTH: 10000,
  SUPPORTED_METHODS: [
    'lime',
    'shap', 
    'inseq',
    'gaf',
    'contrast_cat',
    'attribution_patching',
    'slalom'
  ],
  DEFAULT_MODEL: 'cerebras/llama3.3-70b',
  DEFAULT_METHOD: 'lime'
};
