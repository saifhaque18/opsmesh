"use client";

import {
  createContext,
  useContext,
  useEffect,
  useCallback,
  useState,
  type ReactNode,
} from "react";
import api, {
  login as apiLogin,
  refreshTokens,
  type AuthUser,
} from "./api";

interface AuthContextType {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  logout: () => {},
  isAuthenticated: false,
});

// Storage keys
const USER_KEY = "user";
const TOKEN_KEY = "access_token";

function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem(TOKEN_KEY);
  const storedUser = localStorage.getItem(USER_KEY);
  if (token && storedUser) {
    try {
      return JSON.parse(storedUser) as AuthUser;
    } catch {
      return null;
    }
  }
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  // Hydrate user from localStorage on mount
  useEffect(() => {
    setUser(getStoredUser());
    setIsHydrated(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setUser(null);
  }, []);

  // Set up axios interceptor for auth headers
  useEffect(() => {
    const requestInterceptor = api.interceptors.request.use((config) => {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    return () => {
      api.interceptors.request.eject(requestInterceptor);
    };
  }, []);

  // Set up response interceptor for token refresh
  useEffect(() => {
    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          localStorage.getItem("refresh_token")
        ) {
          originalRequest._retry = true;
          try {
            const refresh = localStorage.getItem("refresh_token")!;
            const tokens = await refreshTokens(refresh);
            localStorage.setItem("access_token", tokens.access_token);
            localStorage.setItem("refresh_token", tokens.refresh_token);
            localStorage.setItem("user", JSON.stringify(tokens.user));
            setUser(tokens.user);
            originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
            return api(originalRequest);
          } catch {
            logout();
          }
        }
        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.response.eject(responseInterceptor);
    };
  }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await apiLogin(email, password);
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    localStorage.setItem("user", JSON.stringify(tokens.user));
    setUser(tokens.user);
  }, []);

  // Don't render children until hydrated to avoid hydration mismatch
  if (!isHydrated) {
    return null;
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
