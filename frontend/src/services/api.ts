import axios, { AxiosResponse } from 'axios';
import {
  PaperProcessRequest,
  PaperResponse,
  PaperListResponse,
  PaperMetadata,
  ProcessingProgress,
  FileUploadResponse,
  HealthResponse,
  Statistics,
  ApiError,
  ConfigurationRequest,
  ConfigurationResponse,
  ConfigurationValidation,
  AvailableModelsResponse,
} from '@/types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Handle unauthorized
      console.error('Unauthorized access');
    } else if (error.response?.status >= 500) {
      // Handle server errors
      console.error('Server error:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// API functions

export const healthCheck = async (): Promise<HealthResponse> => {
  const response: AxiosResponse<HealthResponse> = await api.get('/health');
  return response.data;
};

export const processPaper = async (
  request: PaperProcessRequest
): Promise<{ paper_id: string; status: string; message: string }> => {
  const response = await api.post('/papers/process', request);
  return response.data;
};

export const processPaperSync = async (
  request: PaperProcessRequest
): Promise<PaperResponse> => {
  const response: AxiosResponse<PaperResponse> = await api.post('/papers/process-sync', request);
  return response.data;
};

export const listPapers = async (
  page: number = 1,
  per_page: number = 20,
  search?: string
): Promise<PaperListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: per_page.toString(),
  });
  
  if (search) {
    params.append('search', search);
  }
  
  const response: AxiosResponse<PaperListResponse> = await api.get(`/papers?${params}`);
  return response.data;
};

export const getPaper = async (paperId: string): Promise<any> => {
  const response = await api.get(`/papers/${paperId}`);
  return response.data;
};

export const getPaperProgress = async (paperId: string): Promise<ProcessingProgress> => {
  const response: AxiosResponse<ProcessingProgress> = await api.get(`/papers/${paperId}/progress`);
  return response.data;
};

export const downloadPaper = async (
  paperId: string,
  format: 'html' | 'pdf' | 'json' = 'html'
): Promise<Blob> => {
  const response = await api.get(`/papers/${paperId}/download`, {
    params: { format },
    responseType: 'blob',
  });
  return response.data;
};

export const deletePaper = async (paperId: string): Promise<{ message: string }> => {
  const response = await api.delete(`/papers/${paperId}`);
  return response.data;
};

export const uploadFile = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<FileUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response: AxiosResponse<FileUploadResponse> = await api.post('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
  
  return response.data;
};

export const deleteUploadedFile = async (uploadId: string): Promise<{ message: string }> => {
  const response = await api.delete(`/files/${uploadId}`);
  return response.data;
};

export const getStatistics = async (): Promise<Statistics> => {
  const response: AxiosResponse<Statistics> = await api.get('/stats');
  return response.data;
};

// WebSocket utilities

export const createProgressWebSocket = (
  paperId: string,
  onMessage: (progress: ProcessingProgress) => void,
  onError?: (error: Event) => void,
  onClose?: (event: CloseEvent) => void
): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/progress/${paperId}`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log('WebSocket connected for paper:', paperId);
  };
  
  ws.onmessage = (event) => {
    try {
      const progress: ProcessingProgress = JSON.parse(event.data);
      onMessage(progress);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) {
      onError(error);
    }
  };
  
  ws.onclose = (event) => {
    console.log('WebSocket closed for paper:', paperId);
    if (onClose) {
      onClose(event);
    }
  };
  
  // Send ping every 30 seconds to keep connection alive
  const pingInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send('ping');
    } else {
      clearInterval(pingInterval);
    }
  }, 30000);
  
  return ws;
};

export const createGeneralWebSocket = (
  onMessage: (data: any) => void,
  onError?: (error: Event) => void,
  onClose?: (event: CloseEvent) => void
): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/general`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log('General WebSocket connected');
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) {
      onError(error);
    }
  };
  
  ws.onclose = (event) => {
    console.log('General WebSocket closed');
    if (onClose) {
      onClose(event);
    }
  };
  
  return ws;
};

// Utility functions

export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};

export const isValidArxivUrl = (url: string): boolean => {
  const arxivPattern = /^https?:\/\/(www\.)?arxiv\.org\/(abs|pdf)\/\d{4}\.\d{4,5}(v\d+)?$/;
  return arxivPattern.test(url);
};

export const extractArxivId = (url: string): string | null => {
  const match = url.match(/(\d{4}\.\d{4,5}(?:v\d+)?)/);
  return match ? match[1] : null;
};

export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Error handling utilities

export const handleApiError = (error: any): string => {
  if (error.response?.data?.error) {
    return error.response.data.error;
  } else if (error.response?.data?.detail) {
    return error.response.data.detail;
  } else if (error.message) {
    return error.message;
  } else {
    return 'An unexpected error occurred';
  }
};

export const isApiError = (error: any): error is ApiError => {
  return error && typeof error.error === 'string';
};

// Configuration API functions

export const getConfiguration = async (): Promise<ConfigurationResponse> => {
  const response: AxiosResponse<ConfigurationResponse> = await api.get('/config');
  return response.data;
};

export const updateConfiguration = async (
  request: ConfigurationRequest
): Promise<ConfigurationResponse> => {
  const response: AxiosResponse<ConfigurationResponse> = await api.put('/config', request);
  return response.data;
};

export const resetConfiguration = async (): Promise<ConfigurationResponse> => {
  const response: AxiosResponse<ConfigurationResponse> = await api.post('/config/reset');
  return response.data;
};

export const validateConfiguration = async (): Promise<ConfigurationValidation> => {
  const response: AxiosResponse<ConfigurationValidation> = await api.get('/config/validate');
  return response.data;
};

export const getAvailableModels = async (
  tempApiKey?: string,
  tempApiBase?: string
): Promise<AvailableModelsResponse> => {
  const params = new URLSearchParams();
  if (tempApiKey) {
    params.append('api_key', tempApiKey);
  }
  if (tempApiBase) {
    params.append('api_base', tempApiBase);
  }
  
  const url = params.toString() ? `/config/models?${params}` : '/config/models';
  const response: AxiosResponse<AvailableModelsResponse> = await api.get(url);
  return response.data;
};

// Export the axios instance for custom requests
export { api };
export default api;
