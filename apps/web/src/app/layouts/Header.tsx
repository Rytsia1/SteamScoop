import React, { useState } from "react";
import { Link } from "../router/Router";
import { useRouter } from "../router/RouterContext";
import { ROUTES } from "../router/routes";
import { Menu, X, BarChart3, GitCompare, BookOpen, Activity, Search } from "lucide-react";
import { clsx } from "clsx";

export const Header: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { currentPath } = useRouter();

  const navLinks = [
    { label: "Games Catalog", to: ROUTES.HOME, icon: BarChart3 },
    { label: "Compare Games", to: ROUTES.COMPARE, icon: GitCompare },
    { label: "Methodology", to: ROUTES.METHODOLOGY, icon: BookOpen },
    { label: "System Health", to: ROUTES.STATUS, icon: Activity },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <Link
          to={ROUTES.HOME}
          className="flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 rounded-lg p-1"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-sky-400 flex items-center justify-center font-bold text-white shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
            S
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight text-white group-hover:text-sky-300 transition-colors">
                SteamScoop
              </span>
              <span className="hidden md:inline-block px-1.5 py-0.5 text-[10px] uppercase font-mono font-bold tracking-wider rounded bg-sky-950 text-sky-400 border border-sky-800/60">
                Research
              </span>
            </div>
            <p className="hidden sm:block text-[11px] text-slate-400 leading-none">
              Game Intelligence Platform
            </p>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav aria-label="Main navigation" className="hidden md:flex items-center gap-1">
          {navLinks.map(({ label, to, icon: Icon }) => {
            const isActive =
              to === "/"
                ? currentPath === "/" || currentPath === "/games"
                : currentPath.startsWith(to);

            return (
              <Link
                key={to}
                to={to}
                className={clsx(
                  "flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400",
                  isActive
                    ? "bg-slate-800 text-sky-400 font-semibold shadow-inner"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                )}
              >
                <Icon className={clsx("w-4 h-4", isActive ? "text-sky-400" : "text-slate-400")} aria-hidden="true" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Action & Mobile Toggle */}
        <div className="flex items-center gap-3">
          <Link
            to={ROUTES.HOME}
            aria-label="Quick search games"
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-700/80 bg-slate-800/40 hover:bg-slate-800 text-xs text-slate-400 hover:text-slate-200 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
          >
            <Search className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <span>Search games...</span>
            <kbd className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
              /
            </kbd>
          </Link>

          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation"
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5" aria-hidden="true" />
            ) : (
              <Menu className="w-5 h-5" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div
          id="mobile-navigation"
          className="md:hidden border-t border-slate-800 bg-slate-900 px-4 pt-3 pb-5 space-y-1 animate-in slide-in-from-top-2 duration-150"
        >
          {navLinks.map(({ label, to, icon: Icon }) => {
            const isActive =
              to === "/"
                ? currentPath === "/" || currentPath === "/games"
                : currentPath.startsWith(to);

            return (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileMenuOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-slate-800 text-sky-400 font-semibold"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                )}
              >
                <Icon className={clsx("w-4 h-4", isActive ? "text-sky-400" : "text-slate-400")} aria-hidden="true" />
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
};
