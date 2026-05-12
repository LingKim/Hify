import { authApi } from "@/domain/auth/api";
import type { CurrentUser, LoginResult, LoginValues } from "@/domain/auth/types";
import { request } from "@/shared/api";

export async function login(values: LoginValues): Promise<LoginResult> {
  return request<LoginResult>({
    request: authApi.login,
    body: {
      account: values.account.trim(),
      password: values.password,
    },
  });
}

export async function fetchCurrentUser(
  signal?: AbortSignal,
): Promise<CurrentUser> {
  return request<CurrentUser>({
    request: authApi.me,
    signal,
  });
}
