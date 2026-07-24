import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import EyeIcon from "./EyeIcon";

describe("EyeIcon", () => {
  it("renderiza sem lançar erro quando visivel=true", () => {
    expect(() => render(<EyeIcon visivel />)).not.toThrow();
  });

  it("renderiza sem lançar erro quando visivel=false", () => {
    expect(() => render(<EyeIcon visivel={false} />)).not.toThrow();
  });

  it("renderiza um svg diferente para cada estado de visivel", () => {
    const { container: comVisivel } = render(<EyeIcon visivel />);
    const { container: semVisivel } = render(<EyeIcon visivel={false} />);
    expect(comVisivel.querySelector("circle")).not.toBeNull();
    expect(semVisivel.querySelector("circle")).toBeNull();
    expect(semVisivel.querySelector("line")).not.toBeNull();
  });
});
