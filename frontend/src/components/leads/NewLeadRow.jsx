import WarningIcon from "../common/WarningIcon";

// A Receita não valida telefone (é autodeclarado) — números com todos os
// dígitos iguais ou com quantidade de dígitos errada são claramente lixo,
// não um telefone real. Avisamos em vez de deixar parecer um dado confiável.
function telefoneSuspeito(telefone) {
  if (!telefone) return false;
  const digitos = telefone.replace(/\D/g, "");
  if (digitos.length < 10 || digitos.length > 11) return true;
  return /^(\d)\1+$/.test(digitos);
}

export default function NewLeadRow({ lead, onAdicionar, onOcultar }) {
  return (
    <tr>
      <td><strong>{lead.razao_social}</strong></td>
      <td className="cnpj">{lead.cnpj}</td>
      <td>{lead.uf} / {lead.municipio}</td>
      <td className="tel">
        {lead.telefone || "—"}
        {telefoneSuspeito(lead.telefone) && (
          <span className="dado-suspeito" title="Telefone autodeclarado à Receita — pode não ser confiável">
            <WarningIcon />
          </span>
        )}
      </td>
      <td className="muted">{lead.email || "—"}</td>
      <td><span className="pill blue">{lead.segmento}</span></td>
      <td className="actions-cell">
        <span className="act-add" onClick={() => onAdicionar(lead.cnpj)}>+ Adicionar</span>
        <span className="act-hide" onClick={() => onOcultar(lead.cnpj)}>Não mostrar</span>
      </td>
    </tr>
  );
}
