/**
 * Starts a backend auth flow (sign in / sign out) by form-POSTing to it.
 * Lives outside auth.tsx so non-React modules (the api interceptor) can
 * trigger the same flow without importing React context.
 *
 * Computes the API base from the env directly: importing it from api.ts
 * would be a cycle (api.ts imports this helper).
 */
const API_URL = import.meta.env.VITE_API_URL ?? '';

export const submitAuthFlow = (flow: 'login' | 'logout', redirPage: string) => {
  const form = document.createElement('form');
  form.method = 'post';
  form.action = `${API_URL}/auth/${flow}?redirect_uri=${encodeURIComponent(redirPage)}`;
  document.body.appendChild(form);
  form.submit();
};
