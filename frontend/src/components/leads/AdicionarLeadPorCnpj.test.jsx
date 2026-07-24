import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AdicionarLeadPorCnpj from "./AdicionarLeadPorCnpj";
import { api, ApiError } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: { consultarCnpj: vi.fn() },
  ApiError: class ApiError extends Error {
    constructor(msg, status) {
      super(msg);
      this.status = status;
    }
  },
}));

const dadosEncontrados = {
  razao_social: "Empresa Encontrada LTDA",
  cnpj: "12.345.678/0001-99",
  uf: "SP",
  municipio: "São Paulo",
  segmento: "Comércio",
  situacao_cadastral: "ATIVA",
  fonte: "receita",
};

function renderComp(props = {}) {
  const onAdicionar = props.onAdicionar ?? vi.fn();
  const onSessionExpired = props.onSessionExpired ?? vi.fn();
  render(<AdicionarLeadPorCnpj onAdicionar={onAdicionar} onSessionExpired={onSessionExpired} />);
  return { onAdicionar, onSessionExpired };
}

async function buscarCnpj(user, valor = "12345678000199") {
  const input = screen.getByPlaceholderText("00.000.000/0001-91");
  await user.type(input, valor);
  await user.click(screen.getByText("Buscar"));
}

beforeEach(() => {
  api.consultarCnpj.mockReset();
});

describe("AdicionarLeadPorCnpj", () => {
  it("busca com sucesso mostra os dados encontrados e o botão de adicionar", async () => {
    api.consultarCnpj.mockResolvedValueOnce(dadosEncontrados);
    const user = userEvent.setup();
    renderComp();

    await buscarCnpj(user);

    expect(await screen.findByText("Empresa Encontrada LTDA")).toBeInTheDocument();
    expect(screen.getByText(/12\.345\.678\/0001-99/)).toBeInTheDocument();
    expect(screen.getByText(/SP\/São Paulo/)).toBeInTheDocument();
    expect(screen.getByText("Comércio")).toBeInTheDocument();
    expect(screen.getByText("+ Adicionar aos meus leads")).toBeInTheDocument();
  });

  it('situação cadastral diferente de "ATIVA" mostra a pill vermelha de aviso', async () => {
    api.consultarCnpj.mockResolvedValueOnce({ ...dadosEncontrados, situacao_cadastral: "BAIXADA" });
    const user = userEvent.setup();
    renderComp();

    await buscarCnpj(user);

    expect(await screen.findByText("Situação: BAIXADA")).toBeInTheDocument();
  });

  it('situação cadastral "ATIVA" não mostra a pill de aviso', async () => {
    api.consultarCnpj.mockResolvedValueOnce(dadosEncontrados);
    const user = userEvent.setup();
    renderComp();

    await buscarCnpj(user);

    await screen.findByText("Empresa Encontrada LTDA");
    expect(screen.queryByText(/Situação:/)).not.toBeInTheDocument();
  });

  it("busca com erro (não-401) mostra a mensagem de erro", async () => {
    api.consultarCnpj.mockRejectedValueOnce(new Error("CNPJ inválido"));
    const user = userEvent.setup();
    renderComp();

    await buscarCnpj(user);

    expect(await screen.findByText("CNPJ inválido")).toBeInTheDocument();
  });

  it("busca com erro sem mensagem mostra o texto padrão de erro", async () => {
    api.consultarCnpj.mockRejectedValueOnce(new Error());
    const user = userEvent.setup();
    renderComp();

    await buscarCnpj(user);

    expect(await screen.findByText("Não foi possível buscar esse CNPJ.")).toBeInTheDocument();
  });

  it("busca com erro 401 chama onSessionExpired em vez de mostrar erro", async () => {
    api.consultarCnpj.mockRejectedValueOnce(new ApiError("Não autorizado", 401));
    const user = userEvent.setup();
    const { onSessionExpired } = renderComp();

    await buscarCnpj(user);

    await waitFor(() => expect(onSessionExpired).toHaveBeenCalledTimes(1));
    expect(screen.queryByText("Não autorizado")).not.toBeInTheDocument();
  });

  it("botão de busca fica desabilitado com input vazio", () => {
    renderComp();
    expect(screen.getByText("Buscar")).toBeDisabled();
  });

  it("botão de busca fica desabilitado enquanto buscando", async () => {
    let resolveFn;
    api.consultarCnpj.mockImplementationOnce(
      () => new Promise((resolve) => { resolveFn = resolve; }),
    );
    const user = userEvent.setup();
    renderComp();

    const input = screen.getByPlaceholderText("00.000.000/0001-91");
    await user.type(input, "12345678000199");
    await user.click(screen.getByText("Buscar"));

    expect(screen.getByText("Buscando...")).toBeDisabled();

    resolveFn(dadosEncontrados);
    await screen.findByText("Empresa Encontrada LTDA");
  });

  it("submeter o formulário novamente enquanto já está buscando não chama a API de novo", async () => {
    let resolveFn;
    api.consultarCnpj.mockImplementationOnce(
      () => new Promise((resolve) => { resolveFn = resolve; }),
    );
    const user = userEvent.setup();
    renderComp();
    const input = screen.getByPlaceholderText("00.000.000/0001-91");
    await user.type(input, "12345678000199");
    const form = input.closest("form");

    fireEvent.submit(form);
    fireEvent.submit(form);

    expect(api.consultarCnpj).toHaveBeenCalledTimes(1);
    resolveFn(dadosEncontrados);
    await screen.findByText("Empresa Encontrada LTDA");
  });

  it("submeter o formulário com input vazio não chama a API", () => {
    renderComp();
    const input = screen.getByPlaceholderText("00.000.000/0001-91");
    const form = input.closest("form");

    fireEvent.submit(form);

    expect(api.consultarCnpj).not.toHaveBeenCalled();
  });

  it('clicar em "+ Adicionar aos meus leads" chama onAdicionar sem situacao_cadastral/fonte e limpa o formulário', async () => {
    api.consultarCnpj.mockResolvedValueOnce(dadosEncontrados);
    const onAdicionar = vi.fn().mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderComp({ onAdicionar });

    await buscarCnpj(user);
    await screen.findByText("Empresa Encontrada LTDA");

    await user.click(screen.getByText("+ Adicionar aos meus leads"));

    await waitFor(() => expect(onAdicionar).toHaveBeenCalledTimes(1));
    expect(onAdicionar).toHaveBeenCalledWith({
      razao_social: "Empresa Encontrada LTDA",
      cnpj: "12.345.678/0001-99",
      uf: "SP",
      municipio: "São Paulo",
      segmento: "Comércio",
    });

    await waitFor(() => {
      expect(screen.queryByText("Empresa Encontrada LTDA")).not.toBeInTheDocument();
    });
    const input = screen.getByPlaceholderText("00.000.000/0001-91");
    expect(input).toHaveValue("");
  });

  it("se onAdicionar rejeitar, mostra mensagem de erro sem limpar o formulário", async () => {
    api.consultarCnpj.mockResolvedValueOnce(dadosEncontrados);
    const onAdicionar = vi.fn().mockRejectedValueOnce(new Error("Falha ao salvar"));
    const user = userEvent.setup();
    renderComp({ onAdicionar });

    await buscarCnpj(user);
    await screen.findByText("Empresa Encontrada LTDA");

    await user.click(screen.getByText("+ Adicionar aos meus leads"));

    expect(await screen.findByText("Falha ao salvar")).toBeInTheDocument();
    expect(screen.getByText("Empresa Encontrada LTDA")).toBeInTheDocument();
  });

  it("se onAdicionar rejeitar com erro sem mensagem, mostra o texto padrão de erro", async () => {
    api.consultarCnpj.mockResolvedValueOnce(dadosEncontrados);
    const onAdicionar = vi.fn().mockRejectedValueOnce(new Error());
    const user = userEvent.setup();
    renderComp({ onAdicionar });

    await buscarCnpj(user);
    await screen.findByText("Empresa Encontrada LTDA");

    await user.click(screen.getByText("+ Adicionar aos meus leads"));

    expect(await screen.findByText("Não foi possível adicionar esse lead.")).toBeInTheDocument();
  });

  it("se o erro do onAdicionar for 401, chama onSessionExpired", async () => {
    api.consultarCnpj.mockResolvedValueOnce(dadosEncontrados);
    const onAdicionar = vi.fn().mockRejectedValueOnce(new ApiError("Não autorizado", 401));
    const user = userEvent.setup();
    const { onSessionExpired } = renderComp({ onAdicionar });

    await buscarCnpj(user);
    await screen.findByText("Empresa Encontrada LTDA");

    await user.click(screen.getByText("+ Adicionar aos meus leads"));

    await waitFor(() => expect(onSessionExpired).toHaveBeenCalledTimes(1));
  });
});
