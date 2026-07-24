import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Tabs from "./Tabs";

describe("Tabs", () => {
  it("renderiza os 2 botões com as contagens certas", () => {
    render(<Tabs activeTab="salvos" onChange={() => {}} countSalvos={3} countNovos={7} />);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("o botão da aba ativa (salvos) tem a classe active e o outro não", () => {
    render(<Tabs activeTab="salvos" onChange={() => {}} countSalvos={1} countNovos={2} />);
    const salvosBtn = screen.getByRole("button", { name: /meus leads/i });
    const novosBtn = screen.getByRole("button", { name: /novos leads/i });
    expect(salvosBtn.className).toContain("active");
    expect(novosBtn.className).not.toContain("active");
  });

  it("o botão da aba ativa (novos) tem a classe active e o outro não", () => {
    render(<Tabs activeTab="novos" onChange={() => {}} countSalvos={1} countNovos={2} />);
    const salvosBtn = screen.getByRole("button", { name: /meus leads/i });
    const novosBtn = screen.getByRole("button", { name: /novos leads/i });
    expect(novosBtn.className).toContain("active");
    expect(salvosBtn.className).not.toContain("active");
  });

  it("clicar no botão inativo chama onChange com o nome certo da aba", () => {
    const onChange = vi.fn();
    render(<Tabs activeTab="salvos" onChange={onChange} countSalvos={1} countNovos={2} />);
    fireEvent.click(screen.getByRole("button", { name: /novos leads/i }));
    expect(onChange).toHaveBeenCalledWith("novos");
  });

  it("clicar no botão inativo (salvos) chama onChange com 'salvos'", () => {
    const onChange = vi.fn();
    render(<Tabs activeTab="novos" onChange={onChange} countSalvos={1} countNovos={2} />);
    fireEvent.click(screen.getByRole("button", { name: /meus leads/i }));
    expect(onChange).toHaveBeenCalledWith("salvos");
  });
});
