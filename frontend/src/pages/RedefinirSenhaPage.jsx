import { useState } from "react";
import { api } from "../api/client";
import EyeIcon from "../components/common/EyeIcon";

export default function RedefinirSenhaPage({ token, onConcluido }) {
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [verSenha, setVerSenha] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (novaSenha.length < 6) {
      setErro("A nova senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (novaSenha !== confirmar) {
      setErro("As senhas não coincidem.");
      return;
    }
    setEnviando(true);
    setErro("");
    try {
      await api.redefinirSenha({ token, nova_senha: novaSenha });
      setSucesso(true);
    } catch (err) {
      setErro(err.message || "Não foi possível redefinir a senha. O link pode ter expirado.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-brand">
          <div className="logo-mark">Faro<span className="logo-suffix">CRM</span></div>
        </div>
        <div className="login-title">Redefinir senha</div>

        {sucesso ? (
          <>
            <div className="login-sub">Sua senha foi alterada. Já pode entrar com a nova senha.</div>
            <button className="btn-primary" type="button" onClick={onConcluido}>Ir para o login</button>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="login-sub">Escolha uma nova senha para sua conta.</div>
            <div className="field">
              <label>Nova senha</label>
              <div className="input-com-icone">
                <input
                  type={verSenha ? "text" : "password"}
                  value={novaSenha}
                  onChange={(e) => setNovaSenha(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="btn-olho"
                  tabIndex={-1}
                  onClick={() => setVerSenha((v) => !v)}
                  title={verSenha ? "Ocultar senha" : "Mostrar senha"}
                >
                  <EyeIcon visivel={verSenha} />
                </button>
              </div>
            </div>
            <div className="field">
              <label>Confirmar nova senha</label>
              <input
                type={verSenha ? "text" : "password"}
                value={confirmar}
                onChange={(e) => setConfirmar(e.target.value)}
                required
              />
            </div>
            {erro && <div className="login-erro">{erro}</div>}
            <button className="btn-primary" type="submit" disabled={enviando}>
              {enviando ? "Salvando..." : "Salvar nova senha"}
            </button>
          </form>
        )}

        <div className="login-foot">
          <a onClick={onConcluido}>← Voltar para o login</a>
        </div>
      </div>
    </div>
  );
}
