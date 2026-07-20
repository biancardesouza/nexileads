import { useEffect, useMemo, useState } from "react";
import SavedLeadRow from "./SavedLeadRow";
import { precisaFollowUp } from "../../utils/followUp";

const STATUS_FILTROS = [
  { value: "", label: "Todos os status" },
  { value: "atendeu", label: "Atendeu" },
  { value: "nao_atendeu", label: "Não atendeu" },
  { value: "invalido", label: "Número inválido" },
  { value: "sem_contato", label: "Ainda sem contato" },
];

const ITENS_POR_PAGINA = 20;

function escaparCsv(valor) {
  const str = String(valor ?? "");
  if (/[",\r\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function exportarCsv(leads) {
  const cabecalho = ["Razão Social", "CNPJ", "UF", "Município", "Telefone", "E-mail", "Segmento", "Status", "Última anotação"];
  const linhas = leads.map((l) => [
    l.razao_social,
    l.cnpj,
    l.uf,
    l.municipio,
    l.telefone,
    l.email,
    l.segmento,
    STATUS_FILTROS.find((s) => s.value === l.status)?.label || l.status,
    l.registros?.[0]?.nota || "",
  ]);
  const csv = [cabecalho, ...linhas].map((linha) => linha.map(escaparCsv).join(",")).join("\r\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `leads_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function SavedLeadsTable({ leadsSalvos, onSalvarRegistro, onExcluir }) {
  const [query, setQuery] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("");
  const [soFollowUp, setSoFollowUp] = useState(false);
  const [openRows, setOpenRows] = useState(new Set());
  const [pagina, setPagina] = useState(1);

  const dataFiltrada = useMemo(() => {
    const q = query.toLowerCase();
    return leadsSalvos.filter((l) => {
      const hay = `${l.razao_social} ${l.cnpj}`.toLowerCase();
      if (q && !hay.includes(q)) return false;
      if (statusFiltro && l.status !== statusFiltro) return false;
      if (soFollowUp && !precisaFollowUp(l)) return false;
      return true;
    });
  }, [leadsSalvos, query, statusFiltro, soFollowUp]);

  // Sempre que o filtro muda o resultado, volta pra primeira página — senão
  // dá pra ficar "presa" numa página que não existe mais no novo filtro.
  useEffect(() => {
    setPagina(1);
  }, [query, statusFiltro, soFollowUp]);

  const totalPaginas = Math.max(1, Math.ceil(dataFiltrada.length / ITENS_POR_PAGINA));
  const paginaAtual = Math.min(pagina, totalPaginas);
  const dataPagina = useMemo(
    () => dataFiltrada.slice((paginaAtual - 1) * ITENS_POR_PAGINA, paginaAtual * ITENS_POR_PAGINA),
    [dataFiltrada, paginaAtual],
  );

  function toggleRow(id) {
    setOpenRows((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  return (
    <section className="wrap">
      <h2>Leads salvos</h2>
      <div className="toolbar">
        <input
          placeholder="Buscar empresa, CNPJ..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)}>
          {STATUS_FILTROS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <div className="field-checkbox">
          <label>
            <input
              type="checkbox"
              checked={soFollowUp}
              onChange={(e) => setSoFollowUp(e.target.checked)}
            />
            {" "}Só follow-up
          </label>
        </div>
        <button
          type="button"
          className="btn"
          onClick={() => exportarCsv(dataFiltrada)}
          disabled={dataFiltrada.length === 0}
        >
          Exportar CSV
        </button>
        <span className="count">{dataFiltrada.length} de {leadsSalvos.length} leads</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Empresa</th>
            <th>CNPJ</th>
            <th>UF/Município</th>
            <th>Telefone</th>
            <th>Status da ligação</th>
            <th>Última anotação</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {dataPagina.map((lead) => (
            <SavedLeadRow
              key={lead.id}
              lead={lead}
              isOpen={openRows.has(lead.id)}
              onToggle={toggleRow}
              onSalvarRegistro={onSalvarRegistro}
              onExcluir={onExcluir}
            />
          ))}
        </tbody>
      </table>
      {totalPaginas > 1 && (
        <div className="paginacao">
          <button
            type="button"
            className="btn"
            onClick={() => setPagina((p) => Math.max(1, p - 1))}
            disabled={paginaAtual === 1}
          >
            ← Anterior
          </button>
          <span className="muted">Página {paginaAtual} de {totalPaginas}</span>
          <button
            type="button"
            className="btn"
            onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
            disabled={paginaAtual === totalPaginas}
          >
            Próxima →
          </button>
        </div>
      )}
    </section>
  );
}
