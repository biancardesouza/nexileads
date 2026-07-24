import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import TrashIcon from "./TrashIcon";

describe("TrashIcon", () => {
  it("renderiza sem lançar erro", () => {
    const { container } = render(<TrashIcon />);
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
