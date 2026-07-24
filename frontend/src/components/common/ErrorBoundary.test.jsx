import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ErrorBoundary from "./ErrorBoundary";

function Bomba() {
  throw new Error("boom");
}

describe("ErrorBoundary", () => {
  let consoleErrorSpy;

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("renderiza os children normalmente quando não há erro", () => {
    render(
      <ErrorBoundary>
        <div>ok</div>
      </ErrorBoundary>
    );
    expect(screen.getByText("ok")).toBeInTheDocument();
  });

  it("mostra a tela de fallback quando um filho lança um erro no render", () => {
    render(
      <ErrorBoundary>
        <Bomba />
      </ErrorBoundary>
    );

    expect(screen.getByText("Algo deu errado")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /recarregar/i })).toBeInTheDocument();
  });

  it('clicar em "Recarregar" recarrega a página', () => {
    const reloadSpy = vi.fn();
    const localizacaoOriginal = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...localizacaoOriginal, reload: reloadSpy },
    });

    render(
      <ErrorBoundary>
        <Bomba />
      </ErrorBoundary>
    );
    screen.getByRole("button", { name: /recarregar/i }).click();

    expect(reloadSpy).toHaveBeenCalledTimes(1);

    Object.defineProperty(window, "location", { configurable: true, value: localizacaoOriginal });
  });
});
