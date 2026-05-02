import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/app/layouts/AppLayout";
import { HomePage } from "@/pages/home/HomePage";
import { NotFoundPage } from "@/pages/not-found/NotFoundPage";
import { ApiPreviewPage } from "@/pages/playground-api-preview/ApiPreviewPage";

export function AppRouter(): JSX.Element {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="/playground/api-preview" element={<ApiPreviewPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
