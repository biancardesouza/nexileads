import { describe, expect, it } from "vitest";
import { formatarDataHora } from "./formatDate";

describe("formatarDataHora", () => {
  it("formata uma data ISO conhecida em data e hora pt-BR", () => {
    const isoString = "2026-01-15T13:45:00Z";
    const data = new Date(isoString);
    const dataEsperada = data.toLocaleDateString("pt-BR");
    const horaEsperada = data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

    const resultado = formatarDataHora(isoString);

    expect(resultado).toBe(`${dataEsperada} ${horaEsperada}`);
    expect(resultado).toMatch(/^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$/);
  });

  it("lida com outra data ISO diferente", () => {
    const isoString = "2020-07-04T23:05:30Z";
    const data = new Date(isoString);
    const esperado =
      data.toLocaleDateString("pt-BR") +
      " " +
      data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

    expect(formatarDataHora(isoString)).toBe(esperado);
  });
});
