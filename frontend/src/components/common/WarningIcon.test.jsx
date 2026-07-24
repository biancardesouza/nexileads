import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import WarningIcon from "./WarningIcon";

describe("WarningIcon", () => {
  it("renderiza sem lançar erro", () => {
    const { container } = render(<WarningIcon />);
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
