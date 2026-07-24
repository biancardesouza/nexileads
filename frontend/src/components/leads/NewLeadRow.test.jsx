import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NewLeadRow from "./NewLeadRow";

const leadBase = {
  cnpj: "12.345.678/0001-99",
  razao_social: "Empresa Teste LTDA",
  uf: "SP",
  municipio: "São Paulo",
  telefone: "11987654321",
  email: "contato@teste.com",
  segmento: "Comércio",
};

function renderRow(lead, handlers = {}) {
  const onAdicionar = handlers.onAdicionar ?? vi.fn();
  const onOcultar = handlers.onOcultar ?? vi.fn();
  render(
    <table>
      <tbody>
        <NewLeadRow lead={lead} onAdicionar={onAdicionar} onOcultar={onOcultar} />
      </tbody>
    </table>,
  );
  return { onAdicionar, onOcultar };
}

describe("NewLeadRow", () => {
  it("renderiza os campos do lead", () => {
    renderRow(leadBase);
    expect(screen.getByText("Empresa Teste LTDA")).toBeInTheDocument();
    expect(screen.getByText("12.345.678/0001-99")).toBeInTheDocument();
    expect(screen.getByText("SP / São Paulo")).toBeInTheDocument();
    expect(screen.getByText("11987654321")).toBeInTheDocument();
    expect(screen.getByText("contato@teste.com")).toBeInTheDocument();
    expect(screen.getByText("Comércio")).toBeInTheDocument();
  });

  it('mostra "—" quando telefone e email estão ausentes', () => {
    renderRow({ ...leadBase, telefone: null, email: null });
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBe(2);
  });

  it("não mostra aviso para telefone normal com 11 dígitos variados", () => {
    renderRow({ ...leadBase, telefone: "11987654321" });
    expect(screen.queryByTitle("Telefone autodeclarado à Receita — pode não ser confiável")).not.toBeInTheDocument();
  });

  it("mostra aviso quando telefone tem menos de 10 dígitos", () => {
    renderRow({ ...leadBase, telefone: "123456789" });
    expect(screen.getByTitle("Telefone autodeclarado à Receita — pode não ser confiável")).toBeInTheDocument();
  });

  it("mostra aviso quando telefone tem mais de 11 dígitos", () => {
    renderRow({ ...leadBase, telefone: "123456789012" });
    expect(screen.getByTitle("Telefone autodeclarado à Receita — pode não ser confiável")).toBeInTheDocument();
  });

  it("mostra aviso quando todos os dígitos do telefone são iguais", () => {
    renderRow({ ...leadBase, telefone: "11111111111" });
    expect(screen.getByTitle("Telefone autodeclarado à Receita — pode não ser confiável")).toBeInTheDocument();
  });

  it('chama onAdicionar(lead.cnpj) ao clicar em "+ Adicionar"', async () => {
    const user = userEvent.setup();
    const { onAdicionar } = renderRow(leadBase);
    await user.click(screen.getByText("+ Adicionar"));
    expect(onAdicionar).toHaveBeenCalledWith(leadBase.cnpj);
  });

  it('chama onOcultar(lead.cnpj) ao clicar em "Não mostrar"', async () => {
    const user = userEvent.setup();
    const { onOcultar } = renderRow(leadBase);
    await user.click(screen.getByText("Não mostrar"));
    expect(onOcultar).toHaveBeenCalledWith(leadBase.cnpj);
  });
});
