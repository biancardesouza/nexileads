import StatusBadge from "../common/StatusBadge";
import TrashIcon from "../common/TrashIcon";
import LeadDetail from "./LeadDetail";
import { diasSemContato, precisaFollowUp } from "../../utils/followUp";

export default function SavedLeadRow({ lead, isOpen, onToggle, onSalvarRegistro, onExcluir }) {
  const ultimaNota = lead.registros?.[0] ? lead.registros[0].nota : "—";

  return (
    <>
      <tr>
        <td><strong>{lead.razao_social}</strong></td>
        <td className="cnpj">{lead.cnpj}</td>
        <td>{lead.uf} / {lead.municipio}</td>
        <td className="tel">{lead.telefone || "—"}</td>
        <td>
          <StatusBadge status={lead.status} />
          {precisaFollowUp(lead) && (
            <span className="pill orange follow-up-pill" title={`Sem contato há ${diasSemContato(lead)} dias`}>
              Follow-up
            </span>
          )}
        </td>
        <td className="muted">{ultimaNota}</td>
        <td className="actions-cell">
          <button className="btn" onClick={() => onToggle(lead.id)}>
            {isOpen ? "Fechar" : "Ver mais"}
          </button>
          <button
            className="btn btn-icon"
            onClick={() => onExcluir(lead.id)}
            title="Excluir lead"
            aria-label="Excluir lead"
          >
            <TrashIcon />
          </button>
        </td>
      </tr>
      {isOpen && <LeadDetail lead={lead} onSalvarRegistro={onSalvarRegistro} />}
    </>
  );
}
