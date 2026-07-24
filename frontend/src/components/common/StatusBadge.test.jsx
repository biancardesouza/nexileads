import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StatusBadge from "./StatusBadge";

describe("StatusBadge", () => {
  it.each([
    ["atendeu", "Atendeu"],
    ["nao_atendeu", "Não atendeu"],
    ["invalido", "Número inválido"],
    ["sem_contato", "Sem contato ainda"],
  ])("renderiza o label certo para status=%s", (status, label) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("cai no fallback sem_contato quando o status é desconhecido", () => {
    render(<StatusBadge status="algo_nao_mapeado" />);
    expect(screen.getByText("Sem contato ainda")).toBeInTheDocument();
  });
});
