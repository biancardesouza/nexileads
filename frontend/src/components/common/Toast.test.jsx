import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import Toast from "./Toast";

describe("Toast", () => {
  it("sem message renderiza a div sem a classe show e sem texto", () => {
    const { container } = render(<Toast message={null} />);
    const div = container.querySelector(".toast");
    expect(div).not.toBeNull();
    expect(div.className).toBe("toast");
    expect(div.textContent).toBe("");
  });

  it("com message renderiza com a classe show e o texto visível", () => {
    const { container, getByText } = render(<Toast message="oi" />);
    const div = container.querySelector(".toast");
    expect(div.className).toBe("toast show");
    expect(getByText("oi")).toBeInTheDocument();
  });
});
