const ACCESS_TOKEN_KEY = "gaokao_pilot_access_token";

export function getStoredAccessToken() {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (_error) {
    return null;
  }
}

export function persistAccessToken(token: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    if (token) {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
      return;
    }

    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch (_error) {
    return;
  }
}
