import axios from 'axios';
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from 'react';
import type { User } from '../features/account/types';
import { api } from './api';
import { submitAuthFlow } from './authFlow';

interface AuthContextType {
  user: User | null | undefined;
  mockLogin: (userData: User) => void;
  login: (redirPage: string) => void;
  logout: (redirPage: string) => void;
  /** Refetches /profile/@me; call after actions that change the profile
   *  (e.g. creating an organization) so membership-dependent UI updates. */
  refreshUser: () => Promise<void>;
}

// https://react.dev/reference/react/createContext
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  // get user profile; only a 401 proves we're signed out. Any other failure
  // means "unknown", so we stay undefined rather than showing a Sign in button
  // that may be lying (backend down, timeout, proxy error, etc.).
  const refreshUser = useCallback(() => {
    return api
      .get<User>(`/profile/@me`)
      .then((res) => {
        setUser(res.data);
      })
      .catch((err) => {
        if (axios.isAxiosError(err) && err.response?.status === 401) {
          setUser(null);
        } else {
          console.warn('auth check failed — staying in unknown state', err);
        }
      });
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const [user, setUser] = useState<User | null | undefined>(undefined);

  const mockLogin = (userData: User) => {
    api.get('/auth/login');
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const login = (redirPage: string) => {
    submitAuthFlow('login', redirPage);
  };

  const logout = (redirPage: string) => {
    submitAuthFlow('logout', redirPage);
  };

  // react 19, do not need .Provider anymore. Removed!
  return <AuthContext value={{ user, mockLogin, login, logout, refreshUser }}>{children}</AuthContext>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
