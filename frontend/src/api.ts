// Axios instance.
// This file is used in Pinia configuration, src/stores/auth.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',  // import.meta.env.VITE_API_URL, Proxy to backend, configured in vite.config.ts
  headers: {
    'Content-Type': 'application/json'
  },
  // force Axios to handle redirects so it always includes authorization header
  // otherwise, browser will handle redirects and omit authorization header
  maxRedirects: 0
});

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
});

// Interceptor to handle redirects in order to always include authorization header
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 307) {
      const redirectUrl = error.response.headers.location
      // Manually follow redirect and include authorization
      return api.get(redirectUrl)
    }
  }
)

export default api;