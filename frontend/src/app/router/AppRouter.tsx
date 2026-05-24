import { Spin } from "antd";
import { Route, Routes, Navigate, useLocation } from "react-router-dom";
import { currentUserQueryOptions } from "@/domain/auth/queries";
import { AppLayout } from "@/app/layouts/AppLayout";
import { HomePage } from "@/pages/home/HomePage";
import { NotFoundPage } from "@/pages/not-found/NotFoundPage";
import { CommonComponentsPage } from "@/pages/playground-common-components/CommonComponentsPage";
import { ApiPreviewPage } from "@/pages/playground-api-preview/ApiPreviewPage";
import { ProviderManagementPage } from "@/pages/provider-management/ProviderManagementPage";
import { AgentConfigurationPage } from "@/pages/agent-configuration/AgentConfigurationPage";
import { LandingPage } from "@/pages/landing/LandingPage";
import { ChatPage } from "@/pages/chat/ChatPage";
import { ConversationLogPage } from "@/pages/conversation/ConversationLogPage";
import { KnowledgePage } from "@/pages/knowledge/KnowledgePage";
import { ToolIntegrationPage } from "@/pages/tool-integration/ToolIntegrationPage";
import { UserManagementPage } from "@/pages/user-management/UserManagementPage";
import { LoginPage } from "@/pages/login/LoginPage";
import { clearAccessToken, getAccessToken } from "@/shared/auth/token";
import { useQuery } from "@tanstack/react-query";

export function AppRouter(): JSX.Element {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/landing" element={<LandingPage />} />
      <Route element={<RequireAuth />}>
        <Route index element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/conversations" element={<ConversationLogPage />} />
        <Route path="/agents" element={<AgentConfigurationPage />} />
        <Route path="/tools" element={<ToolIntegrationPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/users" element={<UserManagementPage />} />
        <Route path="/providers" element={<ProviderManagementPage />} />
        <Route path="/playground/api-preview" element={<ApiPreviewPage />} />
        <Route path="/playground/common-components" element={<CommonComponentsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

function RequireAuth(): JSX.Element {
  const location = useLocation();
  const accessToken = getAccessToken();
  const currentUserQuery = useQuery(currentUserQueryOptions(accessToken !== null));

  if (accessToken === null) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location }}
      />
    );
  }

  if (currentUserQuery.isError) {
    clearAccessToken();
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location }}
      />
    );
  }

  if (currentUserQuery.isLoading) {
    return (
      <div className="app-auth-loading">
        <Spin />
      </div>
    );
  }

  return <AppLayout />;
}
