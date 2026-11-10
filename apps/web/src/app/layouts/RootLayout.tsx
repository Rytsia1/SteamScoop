import React from "react";
import { Header } from "./Header";
import { Link } from "../router/Router";
import { ROUTES } from "../router/routes";

export interface RootLayoutProps {
  children: React.ReactNode;
}

export const RootLayout: React.FC<RootLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-sky-500/30 selection:text-sky-200">
      {/* Accessible Skip Link */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Top Application Header */}
      <Header />

      {/* Main Content Area */}
      <main id="main-content" tabIndex={-1} className="flex-1 w-full focus:outline-none">
        {children}
      </main>

      {/* Global Application Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-10 mt-16 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-1.5 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2">
              <span className="font-bold text-slate-300">SteamScoop</span>
              <span>&copy; 2026</span>
              <span>&bull;</span>
              <span>Public Game Intelligence Platform</span>
            </div>
            <p className="text-[11px] text-slate-500 max-w-xl">
              Data collected and aggregated from the Steam Store Customer Reviews API.
              Steam and the Steam logo are trademarks and/or registered trademarks of Valve Corporation.
              SteamScoop is an independent research project not affiliated with or endorsed by Valve.
            </p>
          </div>

          <div className="flex items-center gap-5 text-slate-400">
            <Link to={ROUTES.METHODOLOGY} className="hover:text-slate-200 transition-colors">
              Methodology & Models
            </Link>
            <Link to={ROUTES.STATUS} className="hover:text-slate-200 transition-colors">
              System Health
            </Link>
            <a
              href="https://store.steampowered.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-200 transition-colors"
            >
              Steam Store &nearr;
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

