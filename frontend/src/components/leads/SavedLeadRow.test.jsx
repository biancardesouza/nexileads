import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SavedLeadRow from "./SavedLeadRow";
import { DIAS_PARA_FOLLOW_UP } from "../../utils/followUp";

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
  criado_em: new Date().toISOString(),
  registros: [],
};

function renderRow(lead, props = {}) {
  const onToggle = props.onToggle ?? vi.fn();
  const onSalvarRegistro = props.onSalvarRegistro ?? vi.fn();
  const onExcluir = props.onExcluir ?? vi.fn();
  const isOpen = props.isOpen ?? false;
  render(
    <table>
      <tbody>
        <SavedLeadRow
          lead={lead}
          isOpen={isOpen}
          onToggle={onToggle}
          onSalvarRegistro={onSalvarRegistro}
          onExcluir={onExcluir}
        />
      </tbody>
    </table>,
  );
  return { onToggle, onSalvarRegistro, onExcluir };
}

function diasAtras(dias) {
  const d = new Date();
  d.setDate(d.getDate() - dias);
  return d.toISOString();
}

describe("SavedLeadRow", () => {
  it("renderiza razão social, cnpj, uf/município, telefone e status", () => {
    renderRow(leadBase);
    expect(screen.getByText("Empresa Teste LTDA")).toBeInTheDocument();
    expect(screen.getByText("12.345.678/0001-99")).toBeInTheDocument();
    expect(screen.getByText("SP / São Paulo")).toBeInTheDocument();
    expect(screen.getByText("11987654321")).toBeInTheDocument();
    expect(screen.getByText("Atendeu")).toBeInTheDocument();
  });

  it('mostra "—" quando telefone está ausente', () => {
    renderRow({ ...leadBase, telefone: null, registros: [{ nota: "ok", status: "atendeu", criado_em: new Date().toISOString() }] });
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("mostra a última nota quando há registros", () => {
    renderRow({
      ...leadBase,
      registros: [
        { nota: "Nota mais recente", status: "atendeu", criado_em: new Date().toISOString() },
        { nota: "Nota antiga", status: "nao_atendeu", criado_em: new Date().toISOString() },
      ],
    });
    expect(screen.getByText("Nota mais recente")).toBeInTheDocument();
    expect(screen.queryByText("Nota antiga")).not.toBeInTheDocument();
  });

  it('mostra "—" na última nota quando não há registros', () => {
    renderRow({ ...leadBase, registros: [] });
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it('mostra a pill "Follow-up" quando precisaFollowUp é verdadeiro', () => {
    renderRow({
      ...leadBase,
      status: "sem_contato",
      criado_em: diasAtras(DIAS_PARA_FOLLOW_UP + 1),
    });
    expect(screen.getByText("Follow-up")).toBeInTheDocument();
  });

  it('não mostra a pill "Follow-up" quando não precisa de follow-up', () => {
    renderRow({ ...leadBase, status: "atendeu" });
    expect(screen.queryByText("Follow-up")).not.toBeInTheDocument();
  });

  it('mostra "Ver mais" quando isOpen é false e chama onToggle ao clicar', async () => {
    const user = userEvent.setup();
    const { onToggle } = renderRow(leadBase, { isOpen: false });
    const btn = screen.getByText("Ver mais");
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(onToggle).toHaveBeenCalledWith(leadBase.id);
  });

  it('mostra "Fechar" quando isOpen é true e chama onToggle ao clicar', async () => {
    const user = userEvent.setup();
    const { onToggle } = renderRow(leadBase, { isOpen: true });
    const btn = screen.getByText("Fechar");
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(onToggle).toHaveBeenCalledWith(leadBase.id);
  });

  it("renderiza o LeadDetail quando isOpen é true", () => {
    renderRow(leadBase, { isOpen: true });
    expect(screen.getByText("Dados da empresa")).toBeInTheDocument();
  });

  it("não renderiza o LeadDetail quando isOpen é false", () => {
    renderRow(leadBase, { isOpen: false });
    expect(screen.queryByText("Dados da empresa")).not.toBeInTheDocument();
  });

  it('chama onExcluir(lead.id) ao clicar no botão "Excluir lead"', async () => {
    const user = userEvent.setup();
    const { onExcluir } = renderRow(leadBase);
    await user.click(screen.getByLabelText("Excluir lead"));
    expect(onExcluir).toHaveBeenCalledWith(leadBase.id);
  });
});
