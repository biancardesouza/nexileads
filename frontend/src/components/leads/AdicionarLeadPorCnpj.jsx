import { useState } from "react";
import { api, ApiError } from "../../api/client";

export default function AdicionarLeadPorCnpj({ onAdicionar, onSessionExpired }) {
  const [cnpjInput, setCnpjInput] = useState("");
  const [buscando, setBuscando] = useState(false);
  const [erro, setErro] = useState("");
  const [encontrado, setEncontrado] = useState(null);
  const [adicionando, setAdicionando] = useState(false);

  async function buscar(e) {
    e.preventDefault();
    if (buscando || !cnpjInput.trim()) return;
    setBuscando(true);
    setErro("");
    setEncontrado(null);
    try {
      const dados = await api.consultarCnpj(cnpjInput);
      setEncontrado(dados);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onSessionExpired();
        return;
      }
      setErro(err.message || "Não foi possível buscar esse CNPJ.");
    } finally {
      setBuscando(false);
    }
  }

  async function adicionar() {
    setAdicionando(true);
    setErro("");
    try {
      const { situacao_cadastral, fonte, ...dadosLead } = encontrado;
      await onAdicionar(dadosLead);
      setEncontrado(null);
      setCnpjInput("");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onSessionExpired();
        return;
      }
      setErro(err.message || "Não foi possível adicionar esse lead.");
    } finally {
      setAdicionando(false);
    }
  }

  return (
    <section className="wrap">
      <h2>Adicionar lead por CNPJ</h2>
      <div className="secao-body">
        <form className="cnpj-busca-form" onSubmit={buscar}>
          <input
            placeholder="00.000.000/0001-91"
            value={cnpjInput}
            onChange={(e) => setCnpjInput(e.target.value)}
          />
          <button className="btn-buscar" type="submit" disabled={buscando || !cnpjInput.trim()}>
            {buscando ? "Buscando..." : "Buscar"}
          </button>
        </form>

        {erro && <div className="login-erro">{erro}</div>}

        {encontrado && (
          <div className="cnpj-encontrado">
            <div className="cnpj-encontrado-info">
              <strong>{encontrado.razao_social}</strong>
              <span className="muted">{encontrado.cnpj} · {encontrado.uf}/{encontrado.municipio}</span>
              <span className="muted">{encontrado.segmento}</span>
              {encontrado.situacao_cadastral && encontrado.situacao_cadastral !== "ATIVA" && (
                <span className="pill red">Situação: {encontrado.situacao_cadastral}</span>
              )}
            </div>
            <button className="btn-salvar" onClick={adicionar} disabled={adicionando}>
              {adicionando ? "Adicionando..." : "+ Adicionar aos meus leads"}
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
