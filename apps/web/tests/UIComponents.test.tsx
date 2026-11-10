import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button } from "../src/components/ui/Button";
import { Badge } from "../src/components/ui/Badge";
import { Modal } from "../src/components/ui/Modal";
import { Tabs } from "../src/components/ui/Tabs";
import { Input } from "../src/components/ui/Input";
import { Select } from "../src/components/ui/Select";

describe("UI Components", () => {
  describe("Button", () => {
    it("renders children and handles click", () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click Me</Button>);

      const btn = screen.getByRole("button", { name: "Click Me" });
      fireEvent.click(btn);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("displays loading indicator and aria-busy when isLoading is true", () => {
      render(<Button isLoading>Submitting</Button>);
      const btn = screen.getByRole("button");
      expect(btn).toHaveAttribute("aria-busy", "true");
      expect(btn).toBeDisabled();
    });
  });

  describe("Badge", () => {
    it("renders positive and negative badges", () => {
      render(
        <div>
          <Badge variant="positive">INDEXED</Badge>
          <Badge variant="negative">FAILED</Badge>
        </div>
      );
      expect(screen.getByText("INDEXED")).toBeInTheDocument();
      expect(screen.getByText("FAILED")).toBeInTheDocument();
    });
  });

  describe("Modal", () => {
    it("renders dialog when isOpen is true and dismisses on Escape", () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen={true} onClose={handleClose} title="Test Modal">
          <p>Modal body content</p>
        </Modal>
      );

      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("Test Modal")).toBeInTheDocument();
      expect(screen.getByText("Modal body content")).toBeInTheDocument();

      fireEvent.keyDown(document, { key: "Escape" });
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it("does not render when isOpen is false", () => {
      render(
        <Modal isOpen={false} onClose={() => {}} title="Hidden Modal">
          <p>Hidden</p>
        </Modal>
      );

      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  describe("Tabs", () => {
    it("renders tabs with accessible tablist role and responds to clicks", () => {
      const handleChange = vi.fn();
      const tabs = [
        { id: "tab1", label: "Overview" },
        { id: "tab2", label: "Aspects", count: 8 },
      ];

      render(<Tabs tabs={tabs} activeTab="tab1" onChange={handleChange} />);

      expect(screen.getByRole("tablist")).toBeInTheDocument();
      const tab2 = screen.getByRole("tab", { name: /Aspects/i });
      fireEvent.click(tab2);

      expect(handleChange).toHaveBeenCalledWith("tab2");
    });
  });

  describe("Input and Select", () => {
    it("associates label and renders error message with aria-invalid", () => {
      render(
        <Input
          label="Search Game"
          error="Title must be at least 2 characters"
          placeholder="Type here..."
        />
      );

      const input = screen.getByLabelText("Search Game");
      expect(input).toHaveAttribute("aria-invalid", "true");
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Title must be at least 2 characters"
      );
    });

    it("renders Select options correctly", () => {
      const options = [
        { value: "action", label: "Action" },
        { value: "rpg", label: "RPG" },
      ];
      render(<Select label="Genre" options={options} defaultValue="rpg" />);

      const select = screen.getByLabelText("Genre");
      expect(select).toHaveValue("rpg");
    });
  });
});

