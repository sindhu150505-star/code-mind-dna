import axios from 'axios';

// Development uses Vite's local /api proxy. Production can override the
// deployed backend URL with VITE_API_URL and otherwise preserves the existing API.
const apiBaseUrl = import.meta.env.VITE_API_URL
  || (import.meta.env.DEV ? '/api' : 'https://codemind-dna-api.onrender.com/api');

const api = axios.create({
  baseURL: apiBaseUrl.replace(/\/$/, ''),
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');

  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
