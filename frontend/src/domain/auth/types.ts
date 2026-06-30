export interface AuthRoleRef {
  id: number;
  code: string;
  name: string;
  status: string;
  isSystem: boolean;
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  roles: AuthRoleRef[];
  permissions: string[];
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
