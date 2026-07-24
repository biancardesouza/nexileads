import { describe, expect, it } from "vitest";
import { DIAS_PARA_FOLLOW_UP, diasSemContato, precisaFollowUp } from "./followUp";

describe("diasSemContato", () => {
  it("retorna 0 quando não há criado_em", () => {
    expect(diasSemContato({})).toBe(0);
  });

  it("calcula quantos dias inteiros passaram desde criado_em", () => {
    const dezDiasAtras = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString();
    expect(diasSemContato({ criado_em: dezDiasAtras })).toBe(10);
  });
});

describe("precisaFollowUp", () => {
  it("é falso quando o status não é sem_contato", () => {
    const antigo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
    expect(precisaFollowUp({ status: "atendeu", criado_em: antigo })).toBe(false);
  });

  it("é falso quando ainda não passou o prazo", () => {
    const recente = new Date(Date.now() - (DIAS_PARA_FOLLOW_UP - 1) * 24 * 60 * 60 * 1000).toISOString();
    expect(precisaFollowUp({ status: "sem_contato", criado_em: recente })).toBe(false);
  });

  it("é verdadeiro exatamente no limite de dias", () => {
    const noLimite = new Date(Date.now() - DIAS_PARA_FOLLOW_UP * 24 * 60 * 60 * 1000).toISOString();
    expect(precisaFollowUp({ status: "sem_contato", criado_em: noLimite })).toBe(true);
  });
});
