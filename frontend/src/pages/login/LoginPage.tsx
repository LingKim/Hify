import { App } from "antd";
import { useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";
import { LoginPanel } from "@/domain/auth/components";
import {
  authQueryKeys,
  currentUserQueryOptions,
  loginMutationOptions,
} from "@/domain/auth/queries";
import type { LoginValues } from "@/domain/auth/types";
import { getErrorMessage } from "@/shared/api";
import { getAccessToken, setAccessToken } from "@/shared/auth/token";

interface LoginLocationState {
  from?: {
    pathname?: string;
    search?: string;
  };
}

function getRedirectPath(state: unknown): string {
  const locationState = state as LoginLocationState | null;
  const from = locationState?.from;
  if (from?.pathname === undefined || from.pathname === "/login") {
    return "/";
  }
  return `${from.pathname}${from.search ?? ""}`;
}

export function LoginPage(): JSX.Element {
  const { message } = App.useApp();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const redirectPath = getRedirectPath(location.state);
  const loginMutation = useMutation({
    ...loginMutationOptions(),
    onSuccess: async (result) => {
      setAccessToken(result.accessToken);
      queryClient.setQueryData(authQueryKeys.currentUser(), result.user);
      await queryClient.invalidateQueries({
        queryKey: currentUserQueryOptions(true).queryKey,
      });
      navigate(redirectPath, { replace: true });
    },
    onError: (error) => {
      message.error(getErrorMessage(error));
    },
  });

  useEffect(() => {
    if (getAccessToken() !== null) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const handleSubmit = (values: LoginValues) => {
    loginMutation.mutate(values);
  };

  return (
    <LoginPanel
      loading={loginMutation.isPending}
      onSubmit={handleSubmit}
    />
  );
}
