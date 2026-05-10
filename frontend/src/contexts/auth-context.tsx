import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getCurrentUser } from "../api/auth";
import type { CurrentUserResponse } from "../types/auth";
import { getStoredAccessToken, persistAccessToken } from "./auth-storage";

interface AuthContextValue {
  accessToken: string | null;
  currentUser: CurrentUserResponse | null;
  loadingUser: boolean;
  isAuthenticated: boolean;
  setAccessToken: (token: string | null) => void;
  refreshCurrentUser: () => Promise<CurrentUserResponse | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessTokenState] = useState<string | null>(() => getStoredAccessToken());
  const [currentUser, setCurrentUser] = useState<CurrentUserResponse | null>(null);
  const [loadingUser, setLoadingUser] = useState(Boolean(accessToken));

  const setAccessToken = (token: string | null) => {
    persistAccessToken(token);
    setAccessTokenState(token);
    if (!token) {
      setCurrentUser(null);
      setLoadingUser(false);
    }
  };

  const refreshCurrentUser = async () => {
    if (!getStoredAccessToken()) {
      setCurrentUser(null);
      setLoadingUser(false);
      return null;
    }

    setLoadingUser(true);
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
      return user;
    } catch (_error) {
      persistAccessToken(null);
      setAccessTokenState(null);
      setCurrentUser(null);
      return null;
    } finally {
      setLoadingUser(false);
    }
  };

  const logout = () => {
    persistAccessToken(null);
    setAccessTokenState(null);
    setCurrentUser(null);
    setLoadingUser(false);
  };

  useEffect(() => {
    if (!accessToken) {
      setCurrentUser(null);
      setLoadingUser(false);
      return;
    }
    void refreshCurrentUser();
  }, [accessToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      currentUser,
      loadingUser,
      isAuthenticated: Boolean(accessToken && currentUser),
      setAccessToken,
      refreshCurrentUser,
      logout,
    }),
    [accessToken, currentUser, loadingUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}
