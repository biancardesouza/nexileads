import { precisaFollowUp } from "../../utils/followUp";

export default function SummaryCards({ leadsSalvos }) {
  const total = leadsSalvos.length;
  const atendeu = leadsSalvos.filter((l) => l.status === "atendeu").length;
  const naoAtendeu = leadsSalvos.filter((l) => l.status === "nao_atendeu").length;
  const invalido = leadsSalvos.filter((l) => l.status === "invalido").length;
  const semContato = leadsSalvos.filter((l) => l.status === "sem_contato").length;
  const followUp = leadsSalvos.filter(precisaFollowUp).length;

  const cards = [
    { cls: "", num: total, lbl: "Leads salvos" },
    { cls: "green", num: atendeu, lbl: "Atenderam" },
    { cls: "warn", num: naoAtendeu, lbl: "Não atenderam" },
    { cls: "danger", num: invalido, lbl: "Número inválido" },
    { cls: "info", num: semContato, lbl: "Ainda sem contato" },
    { cls: "warn", num: followUp, lbl: "Aguardando follow-up" },
  ];

  return (
    <section className="cards">
      {cards.map((c) => (
        <div className={`card ${c.cls}`.trim()} key={c.lbl}>
          <div className="num">{c.num}</div>
          <div className="lbl">{c.lbl}</div>
        </div>
      ))}
    </section>
  );
}
