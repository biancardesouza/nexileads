import { useState } from "react";
import { api, setToken } from "../api/client";
import EyeIcon from "../components/common/EyeIcon";
import Logo from "../components/common/Logo";

export default function LoginPage({ onLogin }) {
  const [modo, setModo] = useState("login"); // "login" | "esqueci"

  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");
    setCarregando(true);
    try {
      const { access_token } = await api.login(email, senha);
      setToken(access_token);
      await onLogin();
    } catch (err) {
      setErro(err.message || "Não foi possível entrar. Tente novamente.");
    } finally {
      setCarregando(false);
    }
  }

  if (modo === "esqueci") {
    return (
      <div className="login-screen">
        <div className="login-card">
          <div className="login-brand">
            <Logo />
          </div>
          <div className="login-title">Recuperar senha</div>
          <div className="login-sub">
            Sua senha é gerenciada pela empresa (login integrado ao Bubble). Fale com o administrador
            para redefini-la.
          </div>

          <div className="login-foot">
            <a onClick={() => setModo("login")}>← Voltar para o login</a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">
          <Logo />
        </div>
        <div className="login-title">Entrar na sua conta</div>
        <div className="login-sub">Acesse seus leads salvos e busque novas empresas para prospectar.</div>

        <div className="field">
          <label>E-mail</label>
          <input
            type="email"
            placeholder="seu@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
          <a onClick={() => setModo("esqueci")}>Esqueci minha senha</a>
        </div>
        {erro && <div className="login-erro">{erro}</div>}
        <button className="btn-primary" type="submit" disabled={carregando}>
          {carregando ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
