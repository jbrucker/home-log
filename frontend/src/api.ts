// Axios instance.
// This file is used in Pinia configuration, src/stores/auth.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',  // Proxy to backend, configured in vite.config.ts
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
});

export default api;