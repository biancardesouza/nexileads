import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import SummaryCards from "./SummaryCards";

function diasAtras(dias) {
  return new Date(Date.now() - dias * 24 * 60 * 60 * 1000).toISOString();
}

function getCard(container, label) {
  const cards = Array.from(container.querySelectorAll(".card"));
  const card = cards.find((c) => c.querySelector(".lbl").textContent === label);
  return card;
}

describe("SummaryCards", () => {
  it("mostra a contagem certa para cada card com uma lista mista de leads", () => {
    const leads = [
      { status: "atendeu" },
      { status: "atendeu" },
      { status: "nao_atendeu" },
      { status: "invalido" },
      { status: "sem_contato", criado_em: diasAtras(1) }, // não elegível ainda p/ follow-up
      { status: "sem_contato", criado_em: diasAtras(10) }, // elegível p/ follow-up
    ];

    const { container } = render(<SummaryCards leadsSalvos={leads} />);

    expect(getCard(container, "Leads salvos").querySelector(".num").textContent).toBe("6");
    expect(getCard(container, "Atenderam").querySelector(".num").textContent).toBe("2");
    expect(getCard(container, "Não atenderam").querySelector(".num").textContent).toBe("1");
    expect(getCard(container, "Número inválido").querySelector(".num").textContent).toBe("1");
    expect(getCard(container, "Ainda sem contato").querySelector(".num").textContent).toBe("2");
    expect(getCard(container, "Aguardando follow-up").querySelector(".num").textContent).toBe("1");
  });

  it("com lista vazia todos os cards mostram 0", () => {
    const { container } = render(<SummaryCards leadsSalvos={[]} />);
    const nums = Array.from(container.querySelectorAll(".card .num")).map((n) => n.textContent);
    expect(nums).toEqual(["0", "0", "0", "0", "0", "0"]);
  });
});
