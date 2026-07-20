import { useEffect, useState } from "react";
import SummaryCards from "../components/dashboard/SummaryCards";
import Tabs from "../components/dashboard/Tabs";
import SavedLeadsTable from "../components/leads/SavedLeadsTable";
import NewLeadsTable from "../components/leads/NewLeadsTable";
import AdicionarLeadPorCnpj from "../components/leads/AdicionarLeadPorCnpj";
import Toast from "../components/common/Toast";
import { useToast } from "../hooks/useToast";
import { api, ApiError } from "../api/client";

export default function LeadsPage({ onSessionExpired }) {
  const [leadsSalvos, setLeadsSalvos] = useState([]);
  const [carregandoSalvos, setCarregandoSalvos] = useState(true);
  const [leadsNovos, setLeadsNovos] = useState([]);
  const [activeTab, setActiveTab] = useState("salvos");
  const { toastMessage, showToast } = useToast();

  function tratarErro(err) {
    if (err instanceof ApiError && err.status === 401) {
      onSessionExpired();
      return;
    }
    showToast(err.message || "Ocorreu um erro. Tente novamente.");
  }

  async function buscarNovosLeads(silent = false) {
    try {
      const resultado = await api.getNovosLeads();
      setLeadsNovos(resultado);
      if (!silent) showToast(`${resultado.length} leads encontrados`);
    } catch (err) {
      tratarErro(err);
    }
  }

  // Carrega os leads salvos e a primeira leva de novos leads assim que o painel
  // abre, sem notificar com um toast (isso ficava aparecendo por cima da tela
  // de login no design original).
  useEffect(() => {
    (async () => {
      try {
        setLeadsSalvos(await api.getLeads());
      } catch (err) {
        tratarErro(err);
      } finally {
        setCarregandoSalvos(false);
      }
    })();
    buscarNovosLeads(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSalvarRegistro(id, status, nota) {
    try {
      const atualizado = await api.salvarRegistro(id, { status, nota });
      setLeadsSalvos((prev) => prev.map((l) => (l.id === id ? atualizado : l)));
      showToast("Registro da ligação salvo");
    } catch (err) {
      tratarErro(err);
    }
  }

  async function handleAdicionarAosSalvos(cnpj) {
    const lead = leadsNovos.find((l) => l.cnpj === cnpj);
    if (!lead) return;
    try {
      const { razao_social, uf, municipio, telefone, email, segmento } = lead;
      const novo = await api.addLead({ razao_social, cnpj, uf, municipio, telefone, email, segmento });
      setLeadsSalvos((prev) => [novo, ...prev]);
      setLeadsNovos((prev) => prev.filter((l) => l.cnpj !== cnpj));
      showToast("Lead adicionado aos seus leads salvos");
    } catch (err) {
      tratarErro(err);
    }
  }

  async function handleAdicionarPorCnpj(dadosLead) {
    const novo = await api.addLead(dadosLead);
    setLeadsSalvos((prev) => [novo, ...prev]);
    showToast("Lead adicionado aos seus leads salvos");
  }

  async function handleExcluirLead(id) {
    try {
      await api.deleteLead(id);
      setLeadsSalvos((prev) => prev.filter((lead) => lead.id !== id));
      showToast("Lead removido de meus leads");
    } catch (err) {
      tratarErro(err);
    }
  }

  async function handleOcultarLead(cnpj) {
    try {
      await api.ocultarLead(cnpj);
      setLeadsNovos((prev) => prev.filter((l) => l.cnpj !== cnpj));
      showToast("Lead não será mais exibido");
    } catch (err) {
      tratarErro(err);
    }
  }

  return (
    <>
      <header>
        <h1>Painel de leads</h1>
        <p>Acompanhe os leads que você já está trabalhando e descubra novas empresas para prospectar.</p>
      </header>

      {carregandoSalvos ? (
        <p className="muted">Carregando seus leads...</p>
      ) : (
        <>
          <SummaryCards leadsSalvos={leadsSalvos} />

          <Tabs
            activeTab={activeTab}
            onChange={setActiveTab}
            countSalvos={leadsSalvos.length}
            countNovos={leadsNovos.length}
          />

          <div className="tab-panel active" style={{ display: activeTab === "salvos" ? "block" : "none" }}>
            <AdicionarLeadPorCnpj onAdicionar={handleAdicionarPorCnpj} onSessionExpired={onSessionExpired} />
            <SavedLeadsTable
              leadsSalvos={leadsSalvos}
              onSalvarRegistro={handleSalvarRegistro}
              onExcluir={handleExcluirLead}
            />
          </div>

          <div className="tab-panel active" style={{ display: activeTab === "novos" ? "block" : "none" }}>
            <NewLeadsTable
              leadsNovos={leadsNovos}
              onBuscar={() => buscarNovosLeads(false)}
              onAdicionar={handleAdicionarAosSalvos}
              onOcultar={handleOcultarLead}
            />
          </div>
        </>
      )}

      <Toast message={toastMessage} />
    </>
  );
}
