import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ErrorAlert } from "../src/components/feedback/ErrorAlert";
import { EmptyState } from "../src/components/feedback/EmptyState";
import { PartialDataNotice } from "../src/components/feedback/PartialDataNotice";
import { ChartContainer } from "../src/components/charts/ChartContainer";

describe("Feedback and State Components", () => {
  it("renders ErrorAlert with title, message, code, and triggers onRetry", () => {
    const handleRetry = vi.fn();
    render(
      <ErrorAlert
        title="Failed Query"
        message="Could not reach database"
        code="DB_UNREACHABLE"
        requestId="req_test_err"
        onRetry={handleRetry}
      />
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Failed Query")).toBeInTheDocument();
    expect(screen.getByText("Could not reach database")).toBeInTheDocument();
    expect(screen.getByText("Code: DB_UNREACHABLE")).toBeInTheDocument();
    expect(screen.getByText("Request ID: req_test_err")).toBeInTheDocument();

    const retryBtn = screen.getByRole("button", { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it("renders EmptyState with action button", () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="No Reviews"
        description="No reviews found matching the selected sentiment filter."
        actionLabel="Clear Filters"
        onAction={handleAction}
      />
    );

    expect(screen.getByText("No Reviews")).toBeInTheDocument();
    expect(
      screen.getByText("No reviews found matching the selected sentiment filter.")
    ).toBeInTheDocument();

    const actionBtn = screen.getByRole("button", { name: "Clear Filters" });
    fireEvent.click(actionBtn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it("renders PartialDataNotice with statistical sampling disclaimer and coverage", () => {
    render(
      <PartialDataNotice
        coveragePercent={85.5}
        sampleCount={2500}
        totalAvailable={3000}
      />
    );

    expect(screen.getByRole("note")).toBeInTheDocument();
    expect(screen.getByText(/Provisional Analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/Coverage:\s*85\.5%/i)).toBeInTheDocument();
    expect(screen.getByText(/Analyzed:\s*2[.,]500\s*\/\s*3[.,]000\s*reviews/i)).toBeInTheDocument();
  });

  it("ChartContainer toggles accessible data table when requested", () => {
    const tabularData = [
      { label: "Positive", value: "75%" },
      { label: "Negative", value: "25%" },
    ];

    render(
      <ChartContainer
        title="Sentiment Breakdown"
        option={{}}
        tabularData={tabularData}
        tabularHeaders={["Class", "Rate"]}
      />
    );

    // Initial state: Chart visible, toggle button present
    const toggleBtn = screen.getByRole("button", { name: /Switch to accessible data table/i });
    expect(toggleBtn).toBeInTheDocument();

    // Click toggle to show table
    fireEvent.click(toggleBtn);

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("Positive")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("Negative")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
  });
});
