import { createContext, useContext, useState, useEffect } from 'react';
import { setCsrfToken } from '../api/backend/chat.ts';
import { useApiKeys } from './ApiKeyContext';
import { getApiUrl } from '../config/api/config';

interface User {
  user_id: string;
  username: string;
  email: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<{ email: string }>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { clearKeys } = useApiKeys();

  const checkAuth = async () => {
    try {
      const response = await fetch(getApiUrl('/me'), {
        credentials: 'include'
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (usernameOrEmail: string, password: string) => {
    const response = await fetch(getApiUrl('/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        username_or_email: usernameOrEmail,
        password
      })
    });

    if (!response.ok) {
      const error = await response.json();

      // Check for email not verified (403)
      if (response.status === 403) {
        const verificationError = new Error(error.detail || 'Email not verified');
        (verificationError as any).isEmailNotVerified = true;
        throw verificationError;
      }

      throw new Error(error.detail || 'Login failed');
    }

    // Extract and store CSRF token
    const csrfToken = response.headers.get('X-CSRF-Token');
    if (csrfToken) {
      setCsrfToken(csrfToken);
    }

    const userData = await response.json();
    setUser({
      user_id: userData.user_id,
      username: userData.username,
      email: userData.email,
      is_active: true
    });
  };

  const register = async (username: string, email: string, password: string) => {
    const response = await fetch(getApiUrl('/register'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    // Return email for verification flow, do NOT auto-login
    return { email: data.email };
  };

  const logout = async () => {
    try {
      await fetch(getApiUrl('/logout'), {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      // Clear CSRF token
      setCsrfToken(null);
      setUser(null);
      // Clear API keys from memory (lite mode security)
      clearKeys();
      // Clear all localStorage to prevent data leakage between users
      localStorage.clear();
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};