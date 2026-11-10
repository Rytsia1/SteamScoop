import { createContext, useContext } from "react";

export interface RouterContextType {
  currentPath: string;
  navigate: (to: string, options?: { replace?: boolean }) => void;
  params: Record<string, string>;
  searchParams: URLSearchParams;
  setSearchParams: (params: Record<string, string | number | undefined | null>) => void;
}

export const RouterContext = createContext<RouterContextType | null>(null);

export function useRouter(): RouterContextType {
  const context = useContext(RouterContext);
  if (!context) {
    throw new Error("useRouter must be used within a RouterProvider");
  }
  return context;
}

export function useParams<T extends Record<string, string>>(): T {
  const { params } = useRouter();
  return params as T;
}

export function useSearchParams(): [
  URLSearchParams,
  (params: Record<string, string | number | undefined | null>) => void,
] {
  const { searchParams, setSearchParams } = useRouter();
  return [searchParams, setSearchParams];
}

