import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import HamburgerIcon from "./HamburgerIcon";

describe("HamburgerIcon", () => {
  it("renderiza sem lançar erro", () => {
    const { container } = render(<HamburgerIcon />);
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
