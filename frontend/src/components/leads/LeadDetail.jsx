import { useState } from "react";
import StatusBadge from "../common/StatusBadge";
import { formatarDataHora } from "../../utils/formatDate";

const STATUS_OPTIONS = [
  { value: "atendeu", label: "Atendeu", selCls: "sel-ok" },
  { value: "nao_atendeu", label: "Não atendeu", selCls: "sel-warn" },
  { value: "invalido", label: "Número inválido", selCls: "sel-danger" },
];

export default function LeadDetail({ lead, onSalvarRegistro }) {
  const [pendingStatus, setPendingStatus] = useState(lead.status);
  const [nota, setNota] = useState("");
  const registros = lead.registros ?? [];

  function handleSalvar() {
    onSalvarRegistro(lead.id, pendingStatus, nota.trim());
    setNota("");
  }

  return (
    <tr className="detail-row">
      <td colSpan={7}>
        <div className="detail">
          <section className="detail-box">
            <div className="detail-title"><span>Dados da empresa</span></div>
            <div className="info-list">
              <div className="info-item"><span className="k">Razão social</span><span className="v">{lead.razao_social}</span></div>
              <div className="info-item"><span className="k">CNPJ</span><span className="v">{lead.cnpj}</span></div>
              <div className="info-item"><span className="k">UF/Município</span><span className="v">{lead.uf} / {lead.municipio}</span></div>
              <div className="info-item"><span className="k">Telefone</span><span className="v">{lead.telefone || "—"}</span></div>
              <div className="info-item"><span className="k">E-mail</span><span className="v">{lead.email || "—"}</span></div>
              <div className="info-item"><span className="k">Segmento</span><span className="v">{lead.segmento}</span></div>
            </div>
          </section>

          <section className="detail-box">
            <div className="detail-title">
              <span>Registro de ligações</span>
              <span className="detail-total">{registros.length} registro(s)</span>
            </div>
            <div className="reg-box">
              <div className="vbar">
                {STATUS_OPTIONS.map((opt) => (
                  <div
                    key={opt.value}
                    className={`vbtn ${pendingStatus === opt.value ? opt.selCls : ""}`.trim()}
                    onClick={() => setPendingStatus(opt.value)}
                  >
                    {opt.label}
                  </div>
                ))}
              </div>
              <textarea
                className="vnota"
                placeholder="Como foi a ligação? Anote aqui..."
                value={nota}
                onChange={(e) => setNota(e.target.value)}
              />
              <button className="btn-salvar" onClick={handleSalvar}>Salvar registro</button>
            </div>
            <div className="tx-list">
              {registros.length ? (
                registros.map((r, i) => (
                  <div className="tx-item" key={i}>
                    <div className="tx-head">
                      <StatusBadge status={r.status} />
                      <span className="tx-data">{formatarDataHora(r.criado_em)}</span>
                    </div>
                    <div className="tx-obs">{r.nota}</div>
                  </div>
                ))
              ) : (
                <div className="empty">Nenhuma ligação registrada ainda.</div>
              )}
            </div>
          </section>
        </div>
      </td>
    </tr>
  );
}
