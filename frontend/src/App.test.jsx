import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "./App";
import { api, ApiError } from "./api/client";

vi.mock("./api/client", () => ({
  api: {
    login: vi.fn(),
    logout: vi.fn(),
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

const perfilBase = { nome: "Ana Silva", email: "ana@empresa.com", telefone: "11987654321" };

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getLeads.mockResolvedValue([]);
    api.getNovosLeads.mockResolvedValue([]);
  });

  it("sem sessão ativa (cookie ausente/inválido), api.getMe rejeita com 401 e mostra LoginPage", async () => {
    api.getMe.mockRejectedValueOnce(new ApiError("Não autorizado", 401));

    render(<App />);
    expect(screen.getByText("Carregando...")).toBeInTheDocument();

    await waitFor(() => expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument());
    // Como a sessão é um cookie httpOnly (o JS não sabe se existe), o app
    // sempre tenta restaurar o perfil ao montar — não há mais um "getToken"
    // client-side pra decidir isso de antemão.
    expect(api.getMe).toHaveBeenCalledTimes(1);
  });

  it("com sessão válida, getMe resolve e mostra a tela de leads após o Carregando... inicial", async () => {
    api.getMe.mockResolvedValueOnce(perfilBase);

    render(<App />);

    expect(screen.getByText("Carregando...")).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("Painel de leads")).toBeInTheDocument());
    expect(screen.getByText("Ana Silva")).toBeInTheDocument();
    expect(screen.queryByText("Carregando...")).not.toBeInTheDocument();
  });

  it("erro de rede (não 401) ao restaurar a sessão também cai na tela de login, sem travar no Carregando...", async () => {
    api.getMe.mockRejectedValueOnce(new Error("Falha de rede"));

    render(<App />);

    await waitFor(() => expect(screen.queryByText("Carregando...")).not.toBeInTheDocument());
    expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument();
  });

  it('logout a partir da tela de leads (clicar em "Sair" na Topbar) chama api.logout e volta ao login', async () => {
    api.getMe.mockResolvedValueOnce(perfilBase);
    api.logout.mockResolvedValueOnce(null);

    render(<App />);
    await waitFor(() => expect(screen.getByText("Painel de leads")).toBeInTheDocument());

    fireEvent.click(screen.getAllByText("Sair")[0]);

    await waitFor(() => expect(api.logout).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument());
  });

  it("logout ainda desloga a UI mesmo se a chamada a api.logout falhar (cookie expirado, rede fora, etc)", async () => {
    api.getMe.mockResolvedValueOnce(perfilBase);
    api.logout.mockRejectedValueOnce(new Error("Falha de rede"));

    render(<App />);
    await waitFor(() => expect(screen.getByText("Painel de leads")).toBeInTheDocument());

    fireEvent.click(screen.getAllByText("Sair")[0]);

    await waitFor(() => expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument());
  });

  it("fazer login pelo formulário chama api.login e depois carrega o perfil", async () => {
    api.getMe.mockRejectedValueOnce(new ApiError("Não autorizado", 401)); // tentativa de restaurar sessão no mount
    api.login.mockResolvedValueOnce({ nome: "Ana Silva" });
    api.getMe.mockResolvedValueOnce(perfilBase); // carregarPerfil() chamado por onLogin

    render(<App />);
    await waitFor(() => expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument());

    fireEvent.change(screen.getByPlaceholderText("seu@email.com"), { target: { value: "ana@empresa.com" } });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), { target: { value: "senha123" } });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(screen.getByText("Painel de leads")).toBeInTheDocument());
    expect(api.login).toHaveBeenCalledWith("ana@empresa.com", "senha123");
    expect(api.getMe).toHaveBeenCalledTimes(2);
  });

  it('abrir o perfil pela Topbar mostra ProfilePage, e "Voltar" retorna à tela de leads', async () => {
    api.getMe.mockResolvedValueOnce(perfilBase);

    render(<App />);
    await waitFor(() => expect(screen.getByText("Painel de leads")).toBeInTheDocument());

    fireEvent.click(screen.getByTitle("Ver perfil"));

    expect(await screen.findByText("Meu perfil")).toBeInTheDocument();
    expect(screen.queryByText("Painel de leads")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Voltar/ }));

    await waitFor(() => expect(screen.getByText("Painel de leads")).toBeInTheDocument());
  });
});
