import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import LeadsPage from "./LeadsPage";
import { api, ApiError } from "../api/client";

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

const leadSalvo = {
  id: 1,
  razao_social: "Empresa Salva LTDA",
  cnpj: "11.111.111/0001-11",
  uf: "SP",
  municipio: "São Paulo",
  telefone: "11987654321",
  email: "salva@empresa.com",
  segmento: "Comércio",
  status: "sem_contato",
  registros: [],
};

const leadNovo = {
  cnpj: "22.222.222/0001-22",
  razao_social: "Empresa Nova LTDA",
  uf: "RJ",
  municipio: "Rio de Janeiro",
  telefone: "21987654321",
  email: "nova@empresa.com",
  segmento: "Indústria",
};

async function aguardarCarregamento() {
  await waitFor(() => expect(screen.queryByText("Carregando seus leads...")).not.toBeInTheDocument());
}

describe("LeadsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getLeads.mockResolvedValue([]);
    api.getNovosLeads.mockResolvedValue([]);
  });

  it("no mount, chama api.getLeads e api.getNovosLeads, mostra loading e depois os dados", async () => {
    api.getLeads.mockResolvedValueOnce([leadSalvo]);
    api.getNovosLeads.mockResolvedValueOnce([leadNovo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);

    expect(screen.getByText("Carregando seus leads...")).toBeInTheDocument();

    await aguardarCarregamento();

    expect(api.getLeads).toHaveBeenCalledTimes(1);
    expect(api.getNovosLeads).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Empresa Salva LTDA")).toBeInTheDocument();
  });

  it("erro ao carregar leads (não-401) mostra um toast com a mensagem de erro", async () => {
    api.getLeads.mockRejectedValueOnce(new Error("Falha ao carregar"));

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    await waitFor(() => {
      const toast = document.querySelector(".toast.show");
      expect(toast).not.toBeNull();
      expect(toast.textContent).toBe("Falha ao carregar");
    });
  });

  it("erro 401 ao carregar leads chama onSessionExpired em vez de mostrar toast", async () => {
    const onSessionExpired = vi.fn();
    api.getLeads.mockRejectedValueOnce(new ApiError("Não autorizado", 401));

    render(<LeadsPage onSessionExpired={onSessionExpired} />);
    await aguardarCarregamento();

    await waitFor(() => expect(onSessionExpired).toHaveBeenCalledTimes(1));
    expect(document.querySelector(".toast.show")).toBeNull();
  });

  it('trocar de aba "Meus leads" / "Novos leads" alterna o que é exibido', async () => {
    api.getLeads.mockResolvedValueOnce([leadSalvo]);
    api.getNovosLeads.mockResolvedValueOnce([leadNovo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    const painelSalvos = screen.getByRole("heading", { name: "Leads salvos" }).closest(".tab-panel");
    const painelNovos = screen.getByText("Buscar novos leads").closest(".tab-panel");

    expect(painelSalvos).toHaveStyle({ display: "block" });
    expect(painelNovos).toHaveStyle({ display: "none" });

    fireEvent.click(screen.getByRole("button", { name: /Novos leads/ }));

    expect(painelSalvos).toHaveStyle({ display: "none" });
    expect(painelNovos).toHaveStyle({ display: "block" });

    fireEvent.click(screen.getByRole("button", { name: /Meus leads/ }));

    expect(painelSalvos).toHaveStyle({ display: "block" });
    expect(painelNovos).toHaveStyle({ display: "none" });
  });

  it("salvar registro de ligação atualiza a lista de leads salvos com o retorno da API", async () => {
    api.getLeads.mockResolvedValueOnce([leadSalvo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    fireEvent.click(screen.getByRole("button", { name: "Ver mais" }));

    const leadAtualizado = {
      ...leadSalvo,
      status: "atendeu",
      registros: [{ status: "atendeu", nota: "Cliente interessado", criado_em: "2026-07-24T10:00:00Z" }],
    };
    api.salvarRegistro.mockResolvedValueOnce(leadAtualizado);

    fireEvent.click(screen.getAllByText("Atendeu").find((el) => el.className.includes("vbtn")));
    fireEvent.change(screen.getByPlaceholderText("Como foi a ligação? Anote aqui..."), {
      target: { value: "Cliente interessado" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar registro" }));

    await waitFor(() =>
      expect(api.salvarRegistro).toHaveBeenCalledWith(leadSalvo.id, {
        status: "atendeu",
        nota: "Cliente interessado",
      }),
    );

    await waitFor(() => expect(screen.getAllByText("Cliente interessado").length).toBeGreaterThan(0));
  });

  it("adicionar um lead novo aos salvos remove o CNPJ da lista de novos e adiciona na de salvos", async () => {
    api.getNovosLeads.mockResolvedValueOnce([leadNovo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    fireEvent.click(screen.getByRole("button", { name: /Novos leads/ }));
    const painelNovos = screen.getByText("Buscar novos leads").closest(".tab-panel");
    expect(within(painelNovos).getByText("Empresa Nova LTDA")).toBeInTheDocument();

    const novoSalvo = { id: 99, ...leadNovo, status: "sem_contato", registros: [] };
    api.addLead.mockResolvedValueOnce(novoSalvo);

    fireEvent.click(screen.getByText("+ Adicionar"));

    await waitFor(() =>
      expect(api.addLead).toHaveBeenCalledWith({
        razao_social: leadNovo.razao_social,
        cnpj: leadNovo.cnpj,
        uf: leadNovo.uf,
        municipio: leadNovo.municipio,
        telefone: leadNovo.telefone,
        email: leadNovo.email,
        segmento: leadNovo.segmento,
      }),
    );

    await waitFor(() => expect(within(painelNovos).queryByText("Empresa Nova LTDA")).not.toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /Meus leads/ }));
    const painelSalvos = screen.getByRole("heading", { name: "Leads salvos" }).closest(".tab-panel");
    expect(within(painelSalvos).getByText("Empresa Nova LTDA")).toBeInTheDocument();
  });

  it("excluir lead remove da lista de leads salvos", async () => {
    api.getLeads.mockResolvedValueOnce([leadSalvo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    expect(screen.getByText("Empresa Salva LTDA")).toBeInTheDocument();
    api.deleteLead.mockResolvedValueOnce(null);

    fireEvent.click(screen.getByRole("button", { name: "Excluir lead" }));

    await waitFor(() => expect(api.deleteLead).toHaveBeenCalledWith(leadSalvo.id));
    await waitFor(() => expect(screen.queryByText("Empresa Salva LTDA")).not.toBeInTheDocument());
  });

  it("ocultar lead novo remove da lista de novos leads", async () => {
    api.getNovosLeads.mockResolvedValueOnce([leadNovo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    fireEvent.click(screen.getByRole("button", { name: /Novos leads/ }));
    expect(screen.getByText("Empresa Nova LTDA")).toBeInTheDocument();

    api.ocultarLead.mockResolvedValueOnce(null);
    fireEvent.click(screen.getByText("Não mostrar"));

    await waitFor(() => expect(api.ocultarLead).toHaveBeenCalledWith(leadNovo.cnpj));
    await waitFor(() => expect(screen.queryByText("Empresa Nova LTDA")).not.toBeInTheDocument());
  });

  it("erro ao adicionar lead novo aos salvos mostra toast de erro", async () => {
    api.getNovosLeads.mockResolvedValueOnce([leadNovo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    fireEvent.click(screen.getByRole("button", { name: /Novos leads/ }));
    api.addLead.mockRejectedValueOnce(new Error("Não foi possível adicionar"));

    fireEvent.click(screen.getByText("+ Adicionar"));

    await waitFor(() => {
      const toast = document.querySelector(".toast.show");
      expect(toast).not.toBeNull();
      expect(toast.textContent).toBe("Não foi possível adicionar");
    });
  });

  it("erro ao excluir lead mostra toast de erro", async () => {
    api.getLeads.mockResolvedValueOnce([leadSalvo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    api.deleteLead.mockRejectedValueOnce(new Error("Não foi possível excluir"));
    fireEvent.click(screen.getByRole("button", { name: "Excluir lead" }));

    await waitFor(() => {
      const toast = document.querySelector(".toast.show");
      expect(toast).not.toBeNull();
      expect(toast.textContent).toBe("Não foi possível excluir");
    });
  });

  it("erro ao ocultar lead novo mostra toast de erro", async () => {
    api.getNovosLeads.mockResolvedValueOnce([leadNovo]);

    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    fireEvent.click(screen.getByRole("button", { name: /Novos leads/ }));
    api.ocultarLead.mockRejectedValueOnce(new Error("Não foi possível ocultar"));

    fireEvent.click(screen.getByText("Não mostrar"));

    await waitFor(() => {
      const toast = document.querySelector(".toast.show");
      expect(toast).not.toBeNull();
      expect(toast.textContent).toBe("Não foi possível ocultar");
    });
  });

  it("adicionar lead por CNPJ (formulário) adiciona aos leads salvos", async () => {
    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    const dadosEncontrados = {
      razao_social: "Empresa Via CNPJ LTDA",
      cnpj: "33.333.333/0001-33",
      uf: "MG",
      municipio: "Belo Horizonte",
      telefone: "31987654321",
      email: "cnpj@empresa.com",
      segmento: "Serviços",
      situacao_cadastral: "ATIVA",
      fonte: "brasilapi",
    };
    api.consultarCnpj.mockResolvedValueOnce(dadosEncontrados);

    fireEvent.change(screen.getByPlaceholderText("00.000.000/0001-91"), {
      target: { value: dadosEncontrados.cnpj },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    await waitFor(() => expect(screen.getByText("Empresa Via CNPJ LTDA")).toBeInTheDocument());

    const novoSalvo = { id: 55, ...dadosEncontrados, status: "sem_contato", registros: [] };
    api.addLead.mockResolvedValueOnce(novoSalvo);

    fireEvent.click(screen.getByRole("button", { name: "+ Adicionar aos meus leads" }));

    await waitFor(() =>
      expect(api.addLead).toHaveBeenCalledWith({
        razao_social: dadosEncontrados.razao_social,
        cnpj: dadosEncontrados.cnpj,
        uf: dadosEncontrados.uf,
        municipio: dadosEncontrados.municipio,
        telefone: dadosEncontrados.telefone,
        email: dadosEncontrados.email,
        segmento: dadosEncontrados.segmento,
      }),
    );

    const painelSalvos = screen.getByRole("heading", { name: "Leads salvos" }).closest(".tab-panel");
    await waitFor(() => expect(within(painelSalvos).getByText("Empresa Via CNPJ LTDA")).toBeInTheDocument());
  });

  it('clicar em "Buscar na API" busca novos leads de novo e mostra toast com o total', async () => {
    render(<LeadsPage onSessionExpired={vi.fn()} />);
    await aguardarCarregamento();

    fireEvent.click(screen.getByRole("button", { name: /Novos leads/ }));
    api.getNovosLeads.mockResolvedValueOnce([leadNovo]);

    fireEvent.click(screen.getByRole("button", { name: "Buscar na API" }));

    await waitFor(() => expect(api.getNovosLeads).toHaveBeenCalledTimes(2));
    await waitFor(() => {
      const toast = document.querySelector(".toast.show");
      expect(toast).not.toBeNull();
      expect(toast.textContent).toBe("1 leads encontrados");
    });
  });
});
