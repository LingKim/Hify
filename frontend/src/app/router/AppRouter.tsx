import { Route, Routes } from "react-router-dom";
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

export function AppRouter(): JSX.Element {
  return (
    <Routes>
      <Route path="/landing" element={<LandingPage />} />
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/conversations" element={<ConversationLogPage />} />
        <Route path="/agents" element={<AgentConfigurationPage />} />
        <Route path="/providers" element={<ProviderManagementPage />} />
        <Route path="/playground/api-preview" element={<ApiPreviewPage />} />
        <Route path="/playground/common-components" element={<CommonComponentsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
