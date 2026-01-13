import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add timestamp for cache busting if needed
    config.headers['X-Request-Time'] = new Date().toISOString();
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor with error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle different error scenarios
    if (!error.response) {
      // Network error
      console.error('Network error:', error.message);
      return Promise.reject({
        status: 'network_error',
        message: 'Unable to connect to server. Please check your connection.',
        originalError: error,
      });
    }

    const { status, data } = error.response;

    switch (status) {
      case 400:
        return Promise.reject({
          status: 'validation_error',
          message: data.detail || 'Invalid request',
          originalError: error,
        });
      case 404:
        return Promise.reject({
          status: 'not_found',
          message: data.detail || 'Resource not found',
          originalError: error,
        });
      case 401:
        return Promise.reject({
          status: 'unauthorized',
          message: 'Session expired. Please login again.',
          originalError: error,
        });
      case 403:
        return Promise.reject({
          status: 'forbidden',
          message: 'You do not have permission to perform this action.',
          originalError: error,
        });
      case 422:
        return Promise.reject({
          status: 'unprocessable_entity',
          message: data.detail || 'Request validation failed',
          details: data.errors,
          originalError: error,
        });
      case 500:
        return Promise.reject({
          status: 'server_error',
          message: 'Server error. Please try again later.',
          originalError: error,
        });
      case 503:
        return Promise.reject({
          status: 'service_unavailable',
          message: 'Service temporarily unavailable. Please try again later.',
          originalError: error,
        });
      default:
        return Promise.reject({
          status: 'unknown_error',
          message: data.detail || `Error: ${status}`,
          originalError: error,
        });
    }
  }
);

export default api;
