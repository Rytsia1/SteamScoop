import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { RouterProvider, Routes, Route, Link } from "../src/app/router/Router";
import { useParams, useRouter } from "../src/app/router/RouterContext";

const HomePage = () => (
  <div>
    <h1>Home Page</h1>
    <Link to="/games/game-123">Go to Game 123</Link>
  </div>
);

const GamePage = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const { navigate } = useRouter();
  return (
    <div>
      <h1>Game Detail: {gameId}</h1>
      <button onClick={() => navigate("/")}>Go Home</button>
    </div>
  );
};

const NotFound = () => <div>404 Not Found</div>;

describe("Application Router", () => {
  it("renders the matched route component based on path", () => {
    render(
      <RouterProvider initialPath="/">
        <Routes fallback={<NotFound />}>
          <Route path="/" component={HomePage} />
          <Route path="/games/:gameId" component={GamePage} />
        </Routes>
      </RouterProvider>
    );

    expect(screen.getByText("Home Page")).toBeInTheDocument();
  });

  it("extracts path parameters correctly for parameterized routes", () => {
    render(
      <RouterProvider initialPath="/games/elden-ring-456">
        <Routes fallback={<NotFound />}>
          <Route path="/" component={HomePage} />
          <Route path="/games/:gameId" component={GamePage} />
        </Routes>
      </RouterProvider>
    );

    expect(screen.getByText("Game Detail: elden-ring-456")).toBeInTheDocument();
  });

  it("navigates on Link click", () => {
    render(
      <RouterProvider initialPath="/">
        <Routes fallback={<NotFound />}>
          <Route path="/" component={HomePage} />
          <Route path="/games/:gameId" component={GamePage} />
        </Routes>
      </RouterProvider>
    );

    const link = screen.getByText("Go to Game 123");
    fireEvent.click(link);

    expect(screen.getByText("Game Detail: game-123")).toBeInTheDocument();
  });

  it("renders fallback when no route matches", () => {
    render(
      <RouterProvider initialPath="/unknown/route/path">
        <Routes fallback={<NotFound />}>
          <Route path="/" component={HomePage} />
          <Route path="/games/:gameId" component={GamePage} />
        </Routes>
      </RouterProvider>
    );

    expect(screen.getByText("404 Not Found")).toBeInTheDocument();
  });
});

