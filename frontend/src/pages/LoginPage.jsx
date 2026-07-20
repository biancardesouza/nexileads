import { useState } from "react";
import { api, setToken } from "../api/client";
import EyeIcon from "../components/common/EyeIcon";

export default function LoginPage({ onLogin }) {
  const [modo, setModo] = useState("login"); // "login" | "esqueci"

  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  const [identificador, setIdentificador] = useState("");
  const [enviandoReset, setEnviandoReset] = useState(false);
  const [mensagemReset, setMensagemReset] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");
    setCarregando(true);
    try {
      const { access_token } = await api.login(usuario, senha);
      setToken(access_token);
      await onLogin();
    } catch (err) {
      setErro(err.message || "Não foi possível entrar. Tente novamente.");
    } finally {
      setCarregando(false);
    }
  }

  function abrirEsqueciSenha() {
    setModo("esqueci");
    setIdentificador("");
    setMensagemReset("");
  }

  function voltarParaLogin() {
    setModo("login");
    setMensagemReset("");
  }

  async function handleEsqueciSenha(e) {
    e.preventDefault();
    setEnviandoReset(true);
    try {
      const { detail } = await api.esqueciSenha(identificador);
      setMensagemReset(detail);
    } catch (err) {
      setMensagemReset(err.message || "Não foi possível processar o pedido agora. Tente novamente.");
    } finally {
      setEnviandoReset(false);
    }
  }

  if (modo === "esqueci") {
    return (
      <div className="login-screen">
        <form className="login-card" onSubmit={handleEsqueciSenha}>
          <div className="login-brand">
            <div className="logo-mark">Faro<span className="logo-suffix">CRM</span></div>
          </div>
          <div className="login-title">Recuperar senha</div>
          <div className="login-sub">
            Informe seu usuário ou e-mail cadastrado. Se existir, enviamos um link para redefinir a senha.
          </div>

          {!mensagemReset ? (
            <>
              <div className="field">
                <label>Usuário ou e-mail</label>
                <input
                  type="text"
                  placeholder="seu.usuario ou seu@email.com"
                  value={identificador}
                  onChange={(e) => setIdentificador(e.target.value)}
                  required
                />
              </div>
              <button className="btn-primary" type="submit" disabled={enviandoReset}>
                {enviandoReset ? "Enviando..." : "Enviar link de redefinição"}
              </button>
            </>
          ) : (
            <div className="login-sub">{mensagemReset}</div>
          )}

          <div className="login-foot">
            <a onClick={voltarParaLogin}>← Voltar para o login</a>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">
          <div className="logo-mark">Faro<span className="logo-suffix">CRM</span></div>
        </div>
        <div className="login-title">Entrar na sua conta</div>
        <div className="login-sub">Acesse seus leads salvos e busque novas empresas para prospectar.</div>

        <div className="field">
          <label>Usuário</label>
          <input
            type="text"
            placeholder="Seu usuário"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
          />
        </div>
        <div className="field">
          <label>Senha</label>
          <div className="input-com-icone">
            <input
              type={mostrarSenha ? "text" : "password"}
              placeholder="••••••••"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
            />
            <button
              type="button"
              className="btn-olho"
              tabIndex={-1}
              onClick={() => setMostrarSenha((v) => !v)}
              title={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
            >
              <EyeIcon visivel={mostrarSenha} />
            </button>
          </div>
        </div>
        <div className="login-row">
          <a onClick={abrirEsqueciSenha}>Esqueci minha senha</a>
        </div>
        {erro && <div className="login-erro">{erro}</div>}
        <button className="btn-primary" type="submit" disabled={carregando}>
          {carregando ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
