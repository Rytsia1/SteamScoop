import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "../lib/query-client";
import { RouterProvider, Routes, Route } from "./router/Router";
import { RootLayout } from "./layouts/RootLayout";
import { AuthProvider } from "../features/auth/context/AuthContext";
import { AuthModal } from "../features/auth/components/AuthModal";
import { GamesCatalogPage } from "../pages/GamesCatalogPage";
import { GameOverviewPage } from "../pages/GameOverviewPage";
import { GameReviewsPage } from "../pages/GameReviewsPage";
import { GameComparisonPage } from "../pages/GameComparisonPage";
import { MethodologyPage } from "../pages/MethodologyPage";
import { SystemStatusPage } from "../pages/SystemStatusPage";
import { WorkspaceProjectsPage } from "../pages/WorkspaceProjectsPage";
import { ProjectDetailPage } from "../pages/ProjectDetailPage";
import { AdminDashboardPage } from "../pages/AdminDashboardPage";
import { NotFoundPage } from "../pages/NotFoundPage";

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider>
          <RootLayout>
            <Routes fallback={<NotFoundPage />}>
              <Route path="/" component={GamesCatalogPage} />
              <Route path="/games" component={GamesCatalogPage} />
              <Route path="/games/:gameId" component={GameOverviewPage} />
              <Route path="/games/:gameId/reviews" component={GameReviewsPage} />
              <Route path="/compare" component={GameComparisonPage} />
              <Route path="/methodology" component={MethodologyPage} />
              <Route path="/status" component={SystemStatusPage} />
              <Route path="/workspace" component={WorkspaceProjectsPage} />
              <Route path="/workspace/projects/:projectId" component={ProjectDetailPage} />
              <Route path="/admin" component={AdminDashboardPage} />
            </Routes>
          </RootLayout>
          <AuthModal />
        </RouterProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};
