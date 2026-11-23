import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL ?? "";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "x-csrftoken",
  // axios only attaches the XSRF header to same-origin requests by default;
  // the dev SPA is cross-origin (5173 -> 8000), so opt in explicitly or
  // every POST/PATCH fails the backend's double-submit CSRF check with 403.
  withXSRFToken: true,
});

// attach access token to each request
api.interceptors.request.use((config) => {
  config.withCredentials = true;
  return config
})
