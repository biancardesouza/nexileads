import { useMemo, useState } from "react";
import NewLeadRow from "./NewLeadRow";

export default function NewLeadsTable({ leadsNovos, onBuscar, onAdicionar, onOcultar }) {
  const [query, setQuery] = useState("");
  const [segmentoFiltro, setSegmentoFiltro] = useState("");

  // Os segmentos vêm da descrição real do CNAE de cada empresa (dado da
  // Receita Federal), então não dá pra usar uma lista fixa — montamos as
  // opções do filtro a partir do que a própria busca trouxe.
  const segmentosDisponiveis = useMemo(
    () => [...new Set(leadsNovos.map((l) => l.segmento).filter(Boolean))].sort(),
    [leadsNovos],
  );

  const dataFiltrada = useMemo(() => {
    const q = query.toLowerCase();
    return leadsNovos.filter((l) => {
      const hay = `${l.municipio || ""} ${l.uf || ""} ${l.segmento || ""}`.toLowerCase();
      if (q && !hay.includes(q)) return false;
      if (segmentoFiltro && l.segmento !== segmentoFiltro) return false;
      return true;
    });
  }, [leadsNovos, query, segmentoFiltro]);

  function handleBuscar() {
    setQuery("");
    setSegmentoFiltro("");
    onBuscar();
  }

  return (
    <section className="wrap">
      <h2>Buscar novos leads</h2>
      <div className="toolbar">
        <input
          placeholder="Cidade, UF ou segmento..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={segmentoFiltro} onChange={(e) => setSegmentoFiltro(e.target.value)}>
          <option value="">Todos os segmentos</option>
          {segmentosDisponiveis.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button className="btn-buscar" onClick={handleBuscar}>Buscar na API</button>
        <span className="count">{dataFiltrada.length} leads encontrados</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Empresa</th>
            <th>CNPJ</th>
            <th>UF/Município</th>
            <th>Telefone</th>
            <th>E-mail</th>
            <th>Segmento</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {dataFiltrada.map((lead) => (
            <NewLeadRow
              key={lead.cnpj}
              lead={lead}
              onAdicionar={onAdicionar}
              onOcultar={onOcultar}
            />
          ))}
        </tbody>
      </table>
    </section>
  );
}
