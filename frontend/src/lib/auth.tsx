import { createContext, useContext, useState, type ReactNode } from "react";
import type { User } from "../features/account/types";

interface AuthContextType {
  user: User | null;
  login: (userData: User) => void;
  logout: () => void;
}

// https://react.dev/reference/react/createContext
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {

  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  const login = (userData: User) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  // react 19, do not need .Provider anymore. Removed!
  return (
    <AuthContext value={{ user, login, logout }
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
