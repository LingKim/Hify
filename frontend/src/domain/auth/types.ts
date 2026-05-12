export type AuthUserRole = "admin" | "member";

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  role: AuthUserRole;
  roleLabel: string;
}

export interface LoginValues {
  account: string;
  password: string;
}

export interface LoginResult {
  accessToken: string;
  tokenType: "Bearer";
  expiresIn: number;
  user: CurrentUser;
}
