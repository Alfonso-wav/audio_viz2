/**
 * Tests for React components — basic rendering.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Header from "../components/Header.tsx";
import StepIndicator from "../components/StepIndicator.tsx";
import VersionSelector from "../components/VersionSelector.tsx";

// Mock the api module so VersionSelector doesn't make real fetch calls
const mockCreateVersion = vi.fn();
vi.mock("../api", () => ({
  getVersions: vi.fn().mockResolvedValue({
    current: "0.1.0",
    versions: [
      {
        version: "0.1.0",
        date: "2026-03-02",
        description: "MVP release",
        changes: ["Feature A", "Feature B"],
      },
    ],
  }),
  createVersion: (...args: unknown[]) => mockCreateVersion(...args),
}));

describe("Header", () => {
  it("renders title text", () => {
    const onReset = vi.fn();
    render(<Header onReset={onReset} />);
    expect(screen.getByText("Audio Visualizer")).toBeInTheDocument();
    expect(screen.getByText("YouTube → MP4 in seconds")).toBeInTheDocument();
  });

  it("calls onReset when logo is clicked", () => {
    const onReset = vi.fn();
    render(<Header onReset={onReset} />);
    // The first button is the logo/title button
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[0]);
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it("renders version selector", async () => {
    const onReset = vi.fn();
    render(<Header onReset={onReset} />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });
  });
});

describe("VersionSelector", () => {
  it("renders current version badge", async () => {
    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });
  });

  it("opens dropdown on click", async () => {
    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });

    // Click the version badge
    fireEvent.click(screen.getByTitle("Version history"));
    expect(screen.getByText("Version History")).toBeInTheDocument();
    expect(screen.getByText("MVP release")).toBeInTheDocument();
    expect(screen.getByText("CURRENT")).toBeInTheDocument();
  });

  it("expands changelog on version click", async () => {
    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });

    // Open dropdown
    fireEvent.click(screen.getByTitle("Version history"));

    // Click the version entry to expand
    fireEvent.click(screen.getByText("MVP release"));
    expect(screen.getByText("Feature A")).toBeInTheDocument();
    expect(screen.getByText("Feature B")).toBeInTheDocument();
  });

  it("closes dropdown on X button", async () => {
    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });

    // Open
    fireEvent.click(screen.getByTitle("Version history"));
    expect(screen.getByText("Version History")).toBeInTheDocument();

    // Close via X button — find the close button inside the dropdown header
    const closeButtons = screen.getAllByRole("button");
    const xButton = closeButtons.find((btn) =>
      btn.querySelector("svg") && btn.classList.contains("text-gray-500")
    );
    if (xButton) {
      fireEvent.click(xButton);
      expect(screen.queryByText("Version History")).not.toBeInTheDocument();
    }
  });

  it("shows New button in dropdown header", async () => {
    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTitle("Version history"));
    expect(screen.getByText("New")).toBeInTheDocument();
  });

  it("opens create form when New is clicked", async () => {
    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTitle("Version history"));
    fireEvent.click(screen.getByText("New"));
    expect(screen.getByText("Create New Version")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. 0.2.0")).toBeInTheDocument();
    expect(screen.getByText("Save Version")).toBeInTheDocument();
  });

  it("calls createVersion on save", async () => {
    mockCreateVersion.mockResolvedValueOnce({
      current: "0.2.0",
      versions: [
        { version: "0.2.0", date: "2026-03-02", description: "V2", changes: ["New feature"] },
        { version: "0.1.0", date: "2026-03-02", description: "MVP release", changes: ["Feature A"] },
      ],
    });

    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTitle("Version history"));
    fireEvent.click(screen.getByText("New"));

    // Fill in form
    fireEvent.change(screen.getByPlaceholderText("e.g. 0.2.0"), { target: { value: "0.2.0" } });
    fireEvent.change(screen.getByPlaceholderText("e.g. Layer editor + presets"), { target: { value: "V2 release" } });
    fireEvent.change(screen.getByPlaceholderText("Change 1"), { target: { value: "New feature" } });

    fireEvent.click(screen.getByText("Save Version"));

    await waitFor(() => {
      expect(mockCreateVersion).toHaveBeenCalledWith({
        version: "0.2.0",
        description: "V2 release",
        changes: ["New feature"],
      });
    });
  });

  it("shows error when fields are empty", async () => {
    render(<VersionSelector />);
    await waitFor(() => {
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTitle("Version history"));
    fireEvent.click(screen.getByText("New"));
    fireEvent.click(screen.getByText("Save Version"));

    expect(screen.getByText("Version and description are required")).toBeInTheDocument();
  });
});

describe("StepIndicator", () => {
  it("renders all 5 step labels", () => {
    render(<StepIndicator currentStep="url" />);
    expect(screen.getByText("URL")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();
    expect(screen.getByText("Images")).toBeInTheDocument();
    expect(screen.getByText("Preview")).toBeInTheDocument();
    expect(screen.getByText("Export")).toBeInTheDocument();
  });

  it("highlights current step", () => {
    const { container } = render(<StepIndicator currentStep="images" />);
    // The 3rd step (Images) should have the active class
    const circles = container.querySelectorAll(".rounded-full");
    // circles[2] should be the images step (index 2)
    expect(circles[2].textContent).toBe("3");
    expect(circles[2].className).toContain("bg-accent-purple");
  });

  it("shows checkmarks for completed steps", () => {
    const { container } = render(<StepIndicator currentStep="preview" />);
    const circles = container.querySelectorAll(".rounded-full");
    // Steps 0,1,2 should be done (show ✓)
    expect(circles[0].textContent).toBe("✓");
    expect(circles[1].textContent).toBe("✓");
    expect(circles[2].textContent).toBe("✓");
  });
});
