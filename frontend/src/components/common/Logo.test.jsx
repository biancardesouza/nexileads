import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Logo from "./Logo";

describe("Logo", () => {
  it("renderiza sem lançar erro", () => {
    expect(() => render(<Logo />)).not.toThrow();
    expect(screen.getByText("NexiLeads")).toBeInTheDocument();
  });
});
