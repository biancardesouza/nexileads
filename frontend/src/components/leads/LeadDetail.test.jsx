import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LeadDetail from "./LeadDetail";
import { formatarDataHora } from "../../utils/formatDate";

const leadBase = {
  id: 1,
  cnpj: "12.345.678/0001-99",
  razao_social: "Empresa Teste LTDA",
  uf: "SP",
  municipio: "São Paulo",
  telefone: "11987654321",
  email: "contato@teste.com",
  segmento: "Comércio",
  status: "atendeu",
  registros: [],
};

function renderDetail(lead, onSalvarRegistro = vi.fn()) {
  render(
    <table>
      <tbody>
        <LeadDetail lead={lead} onSalvarRegistro={onSalvarRegistro} />
      </tbody>
    </table>,
  );
  return { onSalvarRegistro };
}

describe("LeadDetail", () => {
  it("mostra os dados da empresa", () => {
    renderDetail(leadBase);
    expect(screen.getByText("Dados da empresa")).toBeInTheDocument();
    expect(screen.getByText("Empresa Teste LTDA")).toBeInTheDocument();
    expect(screen.getByText("12.345.678/0001-99")).toBeInTheDocument();
    expect(screen.getByText("SP / São Paulo")).toBeInTheDocument();
    expect(screen.getByText("11987654321")).toBeInTheDocument();
    expect(screen.getByText("contato@teste.com")).toBeInTheDocument();
    expect(screen.getByText("Comércio")).toBeInTheDocument();
  });

  it('mostra "Nenhuma ligação registrada ainda." quando não há registros', () => {
    renderDetail({ ...leadBase, registros: [] });
    expect(screen.getByText("Nenhuma ligação registrada ainda.")).toBeInTheDocument();
  });

  it('mostra "Nenhuma ligação registrada ainda." quando lead.registros é undefined', () => {
    const { registros, ...leadSemRegistros } = leadBase;
    renderDetail(leadSemRegistros);
    expect(screen.getByText("Nenhuma ligação registrada ainda.")).toBeInTheDocument();
    expect(screen.getByText("0 registro(s)")).toBeInTheDocument();
  });

  it("lista cada registro com status, data formatada e nota", () => {
    const registros = [
      { status: "atendeu", criado_em: "2026-01-15T10:30:00Z", nota: "Cliente confirmou interesse" },
      { status: "nao_atendeu", criado_em: "2026-01-10T08:00:00Z", nota: "Ninguém atendeu" },
    ];
    renderDetail({ ...leadBase, registros });

    expect(screen.getByText("Cliente confirmou interesse")).toBeInTheDocument();
    expect(screen.getByText("Ninguém atendeu")).toBeInTheDocument();
    expect(screen.getByText(formatarDataHora(registros[0].criado_em))).toBeInTheDocument();
    expect(screen.getByText(formatarDataHora(registros[1].criado_em))).toBeInTheDocument();
    expect(screen.getByText("2 registro(s)")).toBeInTheDocument();
  });

  it("o status inicial selecionado é lead.status", () => {
    renderDetail({ ...leadBase, status: "nao_atendeu" });
    const btn = screen.getByText("Não atendeu");
    expect(btn).toHaveClass("sel-warn");
  });

  it("clicar num botão de status muda a seleção visual", async () => {
    const user = userEvent.setup();
    renderDetail({ ...leadBase, status: "atendeu" });

    const atendeuBtn = screen.getByText("Atendeu");
    const invalidoBtn = screen.getByText("Número inválido");

    expect(atendeuBtn).toHaveClass("sel-ok");
    expect(invalidoBtn).not.toHaveClass("sel-danger");

    await user.click(invalidoBtn);

    expect(invalidoBtn).toHaveClass("sel-danger");
    expect(atendeuBtn).not.toHaveClass("sel-ok");
  });

  it("digitar no textarea de nota atualiza o valor do campo", async () => {
    const user = userEvent.setup();
    renderDetail(leadBase);
    const textarea = screen.getByPlaceholderText("Como foi a ligação? Anote aqui...");
    await user.type(textarea, "Ligação de teste");
    expect(textarea).toHaveValue("Ligação de teste");
  });

  it("clicar em Salvar registro chama onSalvarRegistro com id, status e nota.trim(), e limpa o textarea", async () => {
    const user = userEvent.setup();
    const { onSalvarRegistro } = renderDetail(leadBase);
    const textarea = screen.getByPlaceholderText("Como foi a ligação? Anote aqui...");

    await user.click(screen.getByText("Número inválido"));
    await user.type(textarea, "  Nota com espaços  ");
    await user.click(screen.getByText("Salvar registro"));

    expect(onSalvarRegistro).toHaveBeenCalledWith(leadBase.id, "invalido", "Nota com espaços");
    expect(textarea).toHaveValue("");
  });
});
