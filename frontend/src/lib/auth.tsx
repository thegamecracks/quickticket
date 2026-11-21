import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { User } from "../features/account/types";
import axios from "axios";
import { api, API_URL } from "./api";

interface AuthContextType {
  user: User | null | undefined;
  mockLogin: (userData: User) => void;
  login: (redirPage: string) => void;
  logout: () => void;
}

// https://react.dev/reference/react/createContext
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {

  // get user profile; only a 401 proves we're signed out. Any other failure
  // means "unknown", so we stay undefined rather than showing a Sign in button
  // that may be lying (backend down, timeout, proxy error, etc.).
  useEffect(() => {
    api.get<User>(`/profile/@me`)
      .then((res) => { setUser(res.data) })
      .catch((err) => {
        if (axios.isAxiosError(err) && err.response?.status === 401) {
          setUser(null);
        } else {
          console.warn("auth check failed — staying in unknown state", err);
        }
      });
  }, [])

  const [user, setUser] = useState<User | null | undefined>(undefined)

  const mockLogin = (userData: User) => {
    axios.get(`${API_URL}/auth/login`);
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const login = (redirPage: string) => {
    // need to use form unless we change backend to send the url back to the front end to use
    /* e.g. - something like this.
    if "application/json" in request.headers.get("accept", ""):
       return JSONResponse({"authorize_url": str(url)})
    return cookies.force_redirect(url, 303)
    */
    const form = document.createElement("form");
    form.method = "post";
    form.action = `${API_URL}/auth/login?redirect_uri=${encodeURIComponent(redirPage)}`;
    document.body.appendChild(form);
    form.submit();
  }


  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  // react 19, do not need .Provider anymore. Removed!
  return (
    <AuthContext value={{ user, mockLogin, login, logout }
    }>
      {children}
    </AuthContext>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
