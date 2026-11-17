import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authMe } from './api';

interface User {
  id: string;
  email: string;
  full_name: string;
  is_demo: boolean;
  age?: number;
  income_band?: string;
  employment_type?: string;
  kyc_status: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: Partial<User>) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => {},
  logout: () => {},
  loading: true,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('hindsight_token'),
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      authMe()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('hindsight_token');
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = (newToken: string, userData: Partial<User>) => {
    localStorage.setItem('hindsight_token', newToken);
    setToken(newToken);
    setUser(userData as User);
  };

  const logout = () => {
    localStorage.removeItem('hindsight_token');
    localStorage.removeItem('hindsight_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
