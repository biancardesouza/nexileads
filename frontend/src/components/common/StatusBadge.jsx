const STATUS_MAP = {
  atendeu: { cls: "ok", lbl: "Atendeu" },
  nao_atendeu: { cls: "warnb", lbl: "Não atendeu" },
  invalido: { cls: "dangerb", lbl: "Número inválido" },
  sem_contato: { cls: "grayb", lbl: "Sem contato ainda" },
};

export default function StatusBadge({ status }) {
  const { cls, lbl } = STATUS_MAP[status] || STATUS_MAP.sem_contato;
  return <span className={`badge ${cls}`}>{lbl}</span>;
}
