import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ProfilePage from "./ProfilePage";

vi.mock("../api/client", () => ({
  api: {
    login: vi.fn(),
    getMe: vi.fn(),
    getLeads: vi.fn(),
    getNovosLeads: vi.fn(),
    addLead: vi.fn(),
    deleteLead: vi.fn(),
    salvarRegistro: vi.fn(),
    ocultarLead: vi.fn(),
    consultarCnpj: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(msg, status) {
      super(msg);
      this.status = status;
    }
  },
  fotoSrc: (x) => x,
}));

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("com foto_url preenchido, renderiza uma img com o caminho no src", () => {
    const perfil = { nome: "Ana Silva", foto_url: "/uploads/foto.jpg" };
    const { container } = render(<ProfilePage perfil={perfil} onVoltar={vi.fn()} />);
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    expect(img.src).toContain("/uploads/foto.jpg");
  });

  it("sem foto_url, renderiza as iniciais do nome", () => {
    const perfil = { nome: "Ana Silva" };
    const { container } = render(<ProfilePage perfil={perfil} onVoltar={vi.fn()} />);
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("AS")).toBeInTheDocument();
  });

  it("mostra nome, email e telefone quando presentes", () => {
    const perfil = { nome: "Ana Silva", email: "ana@empresa.com", telefone: "11987654321" };
    render(<ProfilePage perfil={perfil} onVoltar={vi.fn()} />);
    expect(screen.getByText("Ana Silva")).toBeInTheDocument();
    expect(screen.getByText("ana@empresa.com")).toBeInTheDocument();
    expect(screen.getByText("11987654321")).toBeInTheDocument();
  });

  it('mostra "—" quando email e telefone são null', () => {
    const perfil = { nome: "Ana Silva", email: null, telefone: null };
    render(<ProfilePage perfil={perfil} onVoltar={vi.fn()} />);
    expect(screen.getAllByText("—")).toHaveLength(2);
  });

  it('mostra "—" quando email e telefone estão ausentes', () => {
    const perfil = { nome: "Ana Silva" };
    render(<ProfilePage perfil={perfil} onVoltar={vi.fn()} />);
    expect(screen.getAllByText("—")).toHaveLength(2);
  });

  it('botão "← Voltar" chama onVoltar', () => {
    const onVoltar = vi.fn();
    const perfil = { nome: "Ana Silva" };
    render(<ProfilePage perfil={perfil} onVoltar={onVoltar} />);
    fireEvent.click(screen.getByRole("button", { name: "← Voltar" }));
    expect(onVoltar).toHaveBeenCalledTimes(1);
  });
});
