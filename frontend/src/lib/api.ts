import axios from 'axios';
export const API_URL = import.meta.env.VITE_API_URL ?? "";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// attach access token to each request
api.interceptors.request.use((config) => {
  config.withCredentials = true;
  return config
})
