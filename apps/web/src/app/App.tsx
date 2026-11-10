import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "../lib/query-client";
import { RouterProvider, Routes, Route } from "./router/Router";
import { RootLayout } from "./layouts/RootLayout";
import { GamesCatalogPage } from "../pages/GamesCatalogPage";
import { GameOverviewPage } from "../pages/GameOverviewPage";
import { GameReviewsPage } from "../pages/GameReviewsPage";
import { GameComparisonPage } from "../pages/GameComparisonPage";
import { MethodologyPage } from "../pages/MethodologyPage";
import { SystemStatusPage } from "../pages/SystemStatusPage";
import { NotFoundPage } from "../pages/NotFoundPage";

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
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
          </Routes>
        </RootLayout>
      </RouterProvider>
    </QueryClientProvider>
  );
};
