import React from "react";
import { Link } from "../app/router/Router";
import { ROUTES } from "../app/router/routes";
import { EmptyState } from "../components/feedback/EmptyState";
import { Compass } from "lucide-react";

export const NotFoundPage: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto px-4 py-20">
      <EmptyState
        title="Page Not Found (404)"
        description="The page or resource you requested could not be located. It may have moved or been retired."
        icon={<Compass className="w-8 h-8 text-sky-400" aria-hidden="true" />}
        actionLabel="Return to Games Catalog"
        onAction={() => {
          window.location.href = ROUTES.HOME;
        }}
      />
      <div className="text-center mt-4">
        <Link to={ROUTES.HOME} className="text-xs text-sky-400 hover:underline">
          &larr; Back to Catalog
        </Link>
      </div>
    </div>
  );
};

