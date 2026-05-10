export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUserResponse {
  id: number;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
}
