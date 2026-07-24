import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "./LoginPage";
import { api, ApiError } from "../api/client";

vi.mock("../api/client", () => ({
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

function preencherFormulario(email, senha) {
  fireEvent.change(screen.getByPlaceholderText("seu@email.com"), { target: { value: email } });
  fireEvent.change(screen.getByPlaceholderText("••••••••"), { target: { value: senha } });
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza os campos de e-mail e senha e o botão Entrar", () => {
    render(<LoginPage onLogin={vi.fn()} />);
    expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
  });

  it("submeter com sucesso chama api.login e depois onLogin, na ordem", async () => {
    const chamadas = [];
    api.login.mockImplementation(async (email, senha) => {
      chamadas.push(["login", email, senha]);
      // O backend seta o cookie httpOnly na resposta — o corpo não traz mais
      // o token, então não há nada pro front guardar aqui.
      return { nome: "Ana Silva" };
    });
    const onLogin = vi.fn(async () => {
      chamadas.push(["onLogin"]);
    });

    render(<LoginPage onLogin={onLogin} />);
    preencherFormulario("ana@empresa.com", "senha123");
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(onLogin).toHaveBeenCalledTimes(1));

    expect(api.login).toHaveBeenCalledWith("ana@empresa.com", "senha123");
    expect(chamadas.map((c) => c[0])).toEqual(["login", "onLogin"]);
  });

  it('mostra "Entrando..." e desabilita o botão enquanto o login está em andamento', async () => {
    api.login.mockResolvedValueOnce({ nome: "Ana Silva" });
    let resolveOnLogin;
    const onLogin = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveOnLogin = resolve;
        }),
    );

    render(<LoginPage onLogin={onLogin} />);
    preencherFormulario("ana@empresa.com", "senha123");
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      const botao = screen.getByRole("button", { name: "Entrando..." });
      expect(botao).toBeDisabled();
    });

    resolveOnLogin();
    await waitFor(() => expect(screen.getByRole("button", { name: "Entrar" })).not.toBeDisabled());
  });

  it("login com erro mostra a mensagem de erro e não chama onLogin", async () => {
    api.login.mockRejectedValueOnce(new ApiError("Credenciais inválidas", 401));
    const onLogin = vi.fn();

    render(<LoginPage onLogin={onLogin} />);
    preencherFormulario("ana@empresa.com", "senhaerrada");
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(screen.getByText("Credenciais inválidas")).toBeInTheDocument());
    expect(onLogin).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Entrar" })).not.toBeDisabled();
  });

  it("login com erro sem mensagem mostra o texto padrão", async () => {
    api.login.mockRejectedValueOnce(new Error());

    render(<LoginPage onLogin={vi.fn()} />);
    preencherFormulario("ana@empresa.com", "senha123");
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() =>
      expect(screen.getByText("Não foi possível entrar. Tente novamente.")).toBeInTheDocument(),
    );
  });

  it("botão de olho alterna o type do campo de senha entre password e text", () => {
    render(<LoginPage onLogin={vi.fn()} />);
    const inputSenha = screen.getByPlaceholderText("••••••••");
    expect(inputSenha).toHaveAttribute("type", "password");

    fireEvent.click(screen.getByTitle("Mostrar senha"));
    expect(inputSenha).toHaveAttribute("type", "text");

    fireEvent.click(screen.getByTitle("Ocultar senha"));
    expect(inputSenha).toHaveAttribute("type", "password");
  });

  it('"Esqueci minha senha" mostra a tela de recuperação, e "Voltar para o login" retorna', () => {
    render(<LoginPage onLogin={vi.fn()} />);

    fireEvent.click(screen.getByText("Esqueci minha senha"));

    expect(screen.getByText(/gerenciada pela empresa/)).toBeInTheDocument();
    expect(screen.getByText(/login integrado ao Bubble/)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("seu@email.com")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("← Voltar para o login"));

    expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument();
    expect(screen.queryByText(/gerenciada pela empresa/)).not.toBeInTheDocument();
  });
});
