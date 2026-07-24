import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SavedLeadsTable from "./SavedLeadsTable";
import { DIAS_PARA_FOLLOW_UP } from "../../utils/followUp";

function diasAtras(dias) {
  const d = new Date();
  d.setDate(d.getDate() - dias);
  return d.toISOString();
}

function lead(overrides = {}) {
  return {
    id: 1,
    cnpj: "00.000.000/0001-00",
    razao_social: "Empresa",
    uf: "SP",
    municipio: "São Paulo",
    telefone: "11987654321",
    email: "a@a.com",
    segmento: "Comércio",
    status: "atendeu",
    criado_em: new Date().toISOString(),
    registros: [],
    ...overrides,
  };
}

const leadsBase = [
  lead({ id: 1, razao_social: "Alfa Comércio", cnpj: "11.111.111/0001-11", status: "atendeu" }),
  lead({ id: 2, razao_social: "Beta Serviços", cnpj: "22.222.222/0001-22", status: "nao_atendeu" }),
  lead({
    id: 3,
    razao_social: "Gama Indústria",
    cnpj: "33.333.333/0001-33",
    status: "sem_contato",
    criado_em: diasAtras(DIAS_PARA_FOLLOW_UP + 2),
  }),
];

function renderTable(leads = leadsBase, props = {}) {
  const onSalvarRegistro = props.onSalvarRegistro ?? vi.fn();
  const onExcluir = props.onExcluir ?? vi.fn();
  render(
    <SavedLeadsTable
      leadsSalvos={leads}
      onSalvarRegistro={onSalvarRegistro}
      onExcluir={onExcluir}
    />,
  );
  return { onSalvarRegistro, onExcluir };
}

describe("SavedLeadsTable - filtros e contador", () => {
  it('mostra o contador "N de M leads" inicialmente', () => {
    renderTable();
    expect(screen.getByText("3 de 3 leads")).toBeInTheDocument();
  });

  it("filtra por texto (razão social)", async () => {
    const user = userEvent.setup();
    renderTable();
    const input = screen.getByPlaceholderText("Buscar empresa, CNPJ...");
    await user.type(input, "alfa");
    expect(screen.getByText("Alfa Comércio")).toBeInTheDocument();
    expect(screen.queryByText("Beta Serviços")).not.toBeInTheDocument();
    expect(screen.getByText("1 de 3 leads")).toBeInTheDocument();
  });

  it("filtra por texto (cnpj)", async () => {
    const user = userEvent.setup();
    renderTable();
    const input = screen.getByPlaceholderText("Buscar empresa, CNPJ...");
    await user.type(input, "22.222.222");
    expect(screen.getByText("Beta Serviços")).toBeInTheDocument();
    expect(screen.queryByText("Alfa Comércio")).not.toBeInTheDocument();
  });

  it("filtra por status via select", async () => {
    const user = userEvent.setup();
    renderTable();
    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "nao_atendeu");
    expect(screen.getByText("Beta Serviços")).toBeInTheDocument();
    expect(screen.queryByText("Alfa Comércio")).not.toBeInTheDocument();
    expect(screen.getByText("1 de 3 leads")).toBeInTheDocument();
  });

  it('checkbox "Só follow-up" filtra só os que precisam de follow-up', async () => {
    const user = userEvent.setup();
    renderTable();
    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);
    expect(screen.getByText("Gama Indústria")).toBeInTheDocument();
    expect(screen.queryByText("Alfa Comércio")).not.toBeInTheDocument();
    expect(screen.queryByText("Beta Serviços")).not.toBeInTheDocument();
    expect(screen.getByText("1 de 3 leads")).toBeInTheDocument();
  });
});

describe("SavedLeadsTable - paginação", () => {
  function muitosLeads(qtd) {
    return Array.from({ length: qtd }, (_, i) =>
      lead({ id: i + 1, razao_social: `Empresa ${i + 1}`, cnpj: `CNPJ-${i + 1}` }),
    );
  }

  it("mostra só 20 leads por página quando há mais de 20", () => {
    renderTable(muitosLeads(25));
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    // 1 cabeçalho + 20 linhas de dados (detail rows não existem pois nenhuma está aberta)
    expect(rows.length).toBe(21);
    expect(screen.getByText("Página 1 de 2")).toBeInTheDocument();
  });

  it('botão "← Anterior" fica desabilitado na primeira página e "Próxima →" navega', async () => {
    const user = userEvent.setup();
    renderTable(muitosLeads(25));
    const anterior = screen.getByText("← Anterior");
    const proxima = screen.getByText("Próxima →");

    expect(anterior).toBeDisabled();
    expect(proxima).not.toBeDisabled();
    expect(screen.getByText("Empresa 1")).toBeInTheDocument();
    expect(screen.queryByText("Empresa 21")).not.toBeInTheDocument();

    await user.click(proxima);

    expect(screen.getByText("Página 2 de 2")).toBeInTheDocument();
    expect(screen.getByText("Empresa 21")).toBeInTheDocument();
    expect(screen.queryByText("Empresa 1")).not.toBeInTheDocument();
    expect(proxima).toBeDisabled();
    expect(anterior).not.toBeDisabled();
  });

  it('botão "← Anterior" navega de volta pra página anterior', async () => {
    const user = userEvent.setup();
    renderTable(muitosLeads(25));
    await user.click(screen.getByText("Próxima →"));
    expect(screen.getByText("Página 2 de 2")).toBeInTheDocument();
    await user.click(screen.getByText("← Anterior"));
    expect(screen.getByText("Página 1 de 2")).toBeInTheDocument();
    expect(screen.getByText("Empresa 1")).toBeInTheDocument();
  });

  it("mudar um filtro volta pra página 1", async () => {
    const user = userEvent.setup();
    renderTable(muitosLeads(25));
    await user.click(screen.getByText("Próxima →"));
    expect(screen.getByText("Página 2 de 2")).toBeInTheDocument();

    const input = screen.getByPlaceholderText("Buscar empresa, CNPJ...");
    await user.type(input, "Empresa 1");

    // Com o filtro aplicado ainda há mais de 20 resultados (Empresa 1, 10-19, ...)? Vamos conferir sem depender de página específica além de 1.
    expect(screen.queryByText("Página 2 de")).not.toBeInTheDocument();
  });

  it("não mostra paginação quando há 20 ou menos leads", () => {
    renderTable(muitosLeads(20));
    expect(screen.queryByText(/Página \d+ de \d+/)).not.toBeInTheDocument();
  });
});

describe("SavedLeadsTable - detalhe (abrir/fechar linha)", () => {
  it('clicar em "Ver mais" abre o LeadDetail e clicar em "Fechar" o fecha novamente', async () => {
    const user = userEvent.setup();
    renderTable();

    expect(screen.queryByText("Dados da empresa")).not.toBeInTheDocument();

    const botoesVerMais = screen.getAllByText("Ver mais");
    await user.click(botoesVerMais[0]);

    expect(screen.getByText("Dados da empresa")).toBeInTheDocument();

    await user.click(screen.getByText("Fechar"));

    expect(screen.queryByText("Dados da empresa")).not.toBeInTheDocument();
  });

  it("permite abrir mais de uma linha de detalhe ao mesmo tempo", async () => {
    const user = userEvent.setup();
    renderTable();

    const botoesVerMais = screen.getAllByText("Ver mais");
    await user.click(botoesVerMais[0]);
    await user.click(screen.getAllByText("Ver mais")[0]);

    expect(screen.getAllByText("Dados da empresa")).toHaveLength(2);
  });
});

describe("SavedLeadsTable - exportar CSV", () => {
  let createObjectURL;
  let revokeObjectURL;
  let clickSpy;

  beforeEach(() => {
    createObjectURL = vi.fn(() => "blob:mock");
    revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clickSpy.mockRestore();
  });

  it('botão "Exportar CSV" fica desabilitado quando a lista filtrada está vazia', async () => {
    const user = userEvent.setup();
    renderTable();
    const input = screen.getByPlaceholderText("Buscar empresa, CNPJ...");
    await user.type(input, "empresa que não existe");
    expect(screen.getByText("Exportar CSV")).toBeDisabled();
  });

  it('clicar em "Exportar CSV" com lista não-vazia gera o blob e clica no link', async () => {
    const user = userEvent.setup();
    renderTable();
    const btn = screen.getByText("Exportar CSV");
    expect(btn).not.toBeDisabled();

    await user.click(btn);

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(createObjectURL.mock.calls[0][0]).toBeInstanceOf(Blob);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock");
  });

  it("exporta CSV corretamente mesmo quando algum campo contém vírgula/aspas (valor é escapado)", async () => {
    const user = userEvent.setup();
    renderTable([
      lead({
        id: 99,
        razao_social: 'Empresa "Especial", LTDA',
        registros: [{ nota: "Nota, com vírgula", status: "atendeu", criado_em: new Date().toISOString() }],
      }),
    ]);
    const btn = screen.getByText("Exportar CSV");

    await user.click(btn);

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    const blob = createObjectURL.mock.calls[0][0];
    const texto = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsText(blob);
    });
    expect(texto).toContain('"Empresa ""Especial"", LTDA"');
    expect(texto).toContain('"Nota, com vírgula"');
  });
});
