import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NewLeadsTable from "./NewLeadsTable";

function lead(overrides = {}) {
  return {
    cnpj: "00.000.000/0001-00",
    razao_social: "Empresa",
    uf: "SP",
    municipio: "São Paulo",
    telefone: "11987654321",
    email: "a@a.com",
    segmento: "Comércio",
    ...overrides,
  };
}

const leadsNovos = [
  lead({ cnpj: "1", razao_social: "Alfa", municipio: "São Paulo", uf: "SP", segmento: "Comércio" }),
  lead({ cnpj: "2", razao_social: "Beta", municipio: "Campinas", uf: "SP", segmento: "Indústria" }),
  lead({ cnpj: "3", razao_social: "Gama", municipio: "Salvador", uf: "BA", segmento: "Serviços" }),
];

function renderTable(leads = leadsNovos, props = {}) {
  const onBuscar = props.onBuscar ?? vi.fn();
  const onAdicionar = props.onAdicionar ?? vi.fn();
  const onOcultar = props.onOcultar ?? vi.fn();
  render(
    <NewLeadsTable
      leadsNovos={leads}
      onBuscar={onBuscar}
      onAdicionar={onAdicionar}
      onOcultar={onOcultar}
    />,
  );
  return { onBuscar, onAdicionar, onOcultar };
}

describe("NewLeadsTable", () => {
  it('mostra o contador "N leads encontrados" com todos os leads inicialmente', () => {
    renderTable();
    expect(screen.getByText("3 leads encontrados")).toBeInTheDocument();
  });

  it("filtra por texto (município) case-insensitive", async () => {
    const user = userEvent.setup();
    renderTable();
    const input = screen.getByPlaceholderText("Cidade, UF ou segmento...");
    await user.type(input, "campinas");
    expect(screen.getByText("Beta")).toBeInTheDocument();
    expect(screen.queryByText("Alfa")).not.toBeInTheDocument();
    expect(screen.queryByText("Gama")).not.toBeInTheDocument();
    expect(screen.getByText("1 leads encontrados")).toBeInTheDocument();
  });

  it("filtra por texto (uf) case-insensitive", async () => {
    const user = userEvent.setup();
    renderTable();
    const input = screen.getByPlaceholderText("Cidade, UF ou segmento...");
    await user.type(input, "ba");
    expect(screen.getByText("Gama")).toBeInTheDocument();
    expect(screen.queryByText("Alfa")).not.toBeInTheDocument();
  });

  it("filtra por texto (segmento) case-insensitive", async () => {
    const user = userEvent.setup();
    renderTable();
    const input = screen.getByPlaceholderText("Cidade, UF ou segmento...");
    await user.type(input, "SERVIÇOS".toLowerCase());
    expect(screen.getByText("Gama")).toBeInTheDocument();
    expect(screen.queryByText("Alfa")).not.toBeInTheDocument();
    expect(screen.queryByText("Beta")).not.toBeInTheDocument();
  });

  it("as opções de segmento vêm dos segmentos presentes na lista, ordenadas", () => {
    renderTable();
    const select = screen.getByRole("combobox");
    const options = within(select).getAllByRole("option").map((o) => o.textContent);
    expect(options).toEqual(["Todos os segmentos", "Comércio", "Indústria", "Serviços"]);
  });

  it("filtra por segmento via select", async () => {
    const user = userEvent.setup();
    renderTable();
    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Indústria");
    expect(screen.getByText("Beta")).toBeInTheDocument();
    expect(screen.queryByText("Alfa")).not.toBeInTheDocument();
    expect(screen.getByText("1 leads encontrados")).toBeInTheDocument();
  });

  it('botão "Buscar na API" limpa os filtros e chama onBuscar', async () => {
    const user = userEvent.setup();
    const { onBuscar } = renderTable();
    const input = screen.getByPlaceholderText("Cidade, UF ou segmento...");
    const select = screen.getByRole("combobox");

    await user.type(input, "campinas");
    await user.selectOptions(select, "Indústria");
    expect(input).toHaveValue("campinas");

    await user.click(screen.getByText("Buscar na API"));

    expect(input).toHaveValue("");
    expect(select).toHaveValue("");
    expect(onBuscar).toHaveBeenCalledTimes(1);
  });

  it("não quebra o filtro quando município/uf/segmento estão ausentes", async () => {
    const user = userEvent.setup();
    renderTable([
      lead({ cnpj: "9", razao_social: "Delta", municipio: null, uf: null, segmento: null }),
    ]);
    const input = screen.getByPlaceholderText("Cidade, UF ou segmento...");
    await user.type(input, "delta");
    // "delta" não aparece nos campos vazios, então o resultado deve ficar vazio.
    expect(screen.getByText("0 leads encontrados")).toBeInTheDocument();
  });

  it("lista vazia renderiza tabela sem linhas", () => {
    renderTable([]);
    expect(screen.getByText("0 leads encontrados")).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).queryAllByRole("row")).toHaveLength(1); // só o cabeçalho
  });
});
