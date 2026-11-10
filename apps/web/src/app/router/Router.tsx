import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { RouterContext, RouterContextType, useRouter } from "./RouterContext";

function matchRoute(
  pattern: string,
  pathname: string
): { matches: boolean; params: Record<string, string> } {
  const patternSegments = pattern.split("/").filter(Boolean);
  const pathSegments = pathname.split("/").filter(Boolean);

  if (patternSegments.length !== pathSegments.length) {
    return { matches: false, params: {} };
  }

  const params: Record<string, string> = {};

  for (let i = 0; i < patternSegments.length; i++) {
    const p = patternSegments[i];
    const actual = pathSegments[i];

    if (p.startsWith(":")) {
      const paramName = p.slice(1);
      params[paramName] = decodeURIComponent(actual);
    } else if (p.toLowerCase() !== actual.toLowerCase()) {
      return { matches: false, params: {} };
    }
  }

  return { matches: true, params };
}

export interface RouterProviderProps {
  children: React.ReactNode;
  initialPath?: string;
}

export const RouterProvider: React.FC<RouterProviderProps> = ({
  children,
  initialPath,
}) => {
  const [currentUrl, setCurrentUrl] = useState<string>(() => {
    if (initialPath) return initialPath;
    if (typeof window !== "undefined") {
      return window.location.pathname + window.location.search;
    }
    return "/";
  });

  useEffect(() => {
    const handlePopState = () => {
      setCurrentUrl(window.location.pathname + window.location.search);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = useCallback(
    (to: string, options?: { replace?: boolean }) => {
      if (typeof window !== "undefined") {
        if (options?.replace) {
          window.history.replaceState({}, "", to);
        } else {
          window.history.pushState({}, "", to);
        }
        window.scrollTo({ top: 0, behavior: "instant" });
      }
      setCurrentUrl(to);
    },
    []
  );

  const [pathname, search] = currentUrl.split("?");
  const searchParams = useMemo(() => new URLSearchParams(search || ""), [search]);

  const setSearchParams = useCallback(
    (newParams: Record<string, string | number | undefined | null>) => {
      const current = new URLSearchParams(searchParams);
      for (const [key, value] of Object.entries(newParams)) {
        if (value === undefined || value === null || value === "") {
          current.delete(key);
        } else {
          current.set(key, String(value));
        }
      }
      const qs = current.toString();
      const newUrl = qs ? `${pathname}?${qs}` : pathname;
      navigate(newUrl, { replace: true });
    },
    [pathname, searchParams, navigate]
  );

  const contextValue = useMemo<RouterContextType>(() => {
    return {
      currentPath: pathname || "/",
      navigate,
      params: {},
      searchParams,
      setSearchParams,
    };
  }, [pathname, navigate, searchParams, setSearchParams]);

  return (
    <RouterContext.Provider value={contextValue}>{children}</RouterContext.Provider>
  );
};

export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  to: string;
  replace?: boolean;
  activeClassName?: string;
}

export const Link: React.FC<LinkProps> = ({
  to,
  replace,
  className,
  activeClassName,
  children,
  onClick,
  ...rest
}) => {
  const { currentPath, navigate } = useRouter();
  const isActive = currentPath === to || (to !== "/" && currentPath.startsWith(to));

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    onClick?.(e);
    if (
      !e.defaultPrevented &&
      e.button === 0 &&
      !e.metaKey &&
      !e.altKey &&
      !e.ctrlKey &&
      !e.shiftKey
    ) {
      e.preventDefault();
      navigate(to, { replace });
    }
  };

  const combinedClassName = [
    className,
    isActive && activeClassName ? activeClassName : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <a
      href={to}
      onClick={handleClick}
      className={combinedClassName}
      aria-current={isActive ? "page" : undefined}
      {...rest}
    >
      {children}
    </a>
  );
};

export interface RouteProps {
  path: string;
  component: React.ComponentType;
}

export const Routes: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null,
}) => {
  const { currentPath, searchParams, setSearchParams, navigate } = useRouter();

  const childArray = React.Children.toArray(children);

  for (const child of childArray) {
    if (React.isValidElement<RouteProps>(child) && child.props.path) {
      const { path, component: Component } = child.props;
      const { matches, params } = matchRoute(path, currentPath);

      if (matches) {
        return (
          <RouterContext.Provider
            value={{
              currentPath,
              navigate,
              params,
              searchParams,
              setSearchParams,
            }}
          >
            <Component />
          </RouterContext.Provider>
        );
      }
    }
  }

  return <>{fallback}</>;
};

export const Route: React.FC<RouteProps> = () => {
  return null;
};
