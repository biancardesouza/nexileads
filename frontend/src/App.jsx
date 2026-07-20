import { useEffect, useState } from "react";
import LoginPage from "./pages/LoginPage";
import LeadsPage from "./pages/LeadsPage";
import ProfilePage from "./pages/ProfilePage";
import AdminPage from "./pages/AdminPage";
import RedefinirSenhaPage from "./pages/RedefinirSenhaPage";
import Topbar from "./components/layout/Topbar";
import { api, ApiError, clearToken, getToken } from "./api/client";

export default function App() {
  const [perfil, setPerfil] = useState(null);
  const [restaurandoSessao, setRestaurandoSessao] = useState(true);
  const [tela, setTela] = useState("leads");
  const [tokenReset, setTokenReset] = useState(
    () => new URLSearchParams(window.location.search).get("token"),
  );

  function carregarPerfil() {
    return api.getMe().then(setPerfil);
  }

  // Se já existe um token salvo (login anterior), tenta restaurar a sessão em
  // vez de jogar a pessoa de volta pra tela de login a cada F5. Não faz isso
  // enquanto um link de redefinição de senha está sendo visto, pra uma
  // sessão antiga não se misturar com esse fluxo.
  useEffect(() => {
    if (tokenReset || !getToken()) {
      setRestaurandoSessao(false);
      return;
    }
    carregarPerfil()
      .catch((err) => {
        // Só desloga de verdade se o token for realmente inválido (401).
        // Um erro de rede/servidor não deve derrubar uma sessão válida.
        if (err instanceof ApiError && err.status === 401) clearToken();
      })
      .finally(() => setRestaurandoSessao(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleLogin() {
    setRestaurandoSessao(true);
    return carregarPerfil().finally(() => setRestaurandoSessao(false));
  }

  function handleLogout() {
    clearToken();
    setPerfil(null);
    setTela("leads");
  }

  function limparTokenReset() {
    window.history.replaceState({}, "", window.location.pathname);
    // Redefinir a senha invalida a sessão de quem quer que estivesse logado
    // nesse navegador — força um login novo em vez de deixar uma sessão
    // antiga (de um computador compartilhado, por exemplo) aparecer na tela.
    clearToken();
    setPerfil(null);
    setTokenReset(null);
  }

  if (tokenReset) {
    return <RedefinirSenhaPage token={tokenReset} onConcluido={limparTokenReset} />;
  }

  if (restaurandoSessao) {
    return (
      <div className="container">
        <p className="muted">Carregando...</p>
      </div>
    );
  }

  if (!perfil) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="container">
      <Topbar
        perfil={perfil}
        onLogout={handleLogout}
        onAbrirPerfil={() => setTela("perfil")}
        onAbrirAdmin={() => setTela("admin")}
      />

      {tela === "perfil" && (
        <ProfilePage
          perfil={perfil}
          onPerfilAtualizado={setPerfil}
          onVoltar={() => setTela("leads")}
          onContaExcluida={handleLogout}
          onSessionExpired={handleLogout}
        />
      )}
      {tela === "admin" && perfil.is_admin && (
        <AdminPage perfil={perfil} onVoltar={() => setTela("leads")} onSessionExpired={handleLogout} />
      )}
      {tela === "leads" && <LeadsPage onSessionExpired={handleLogout} />}
    </div>
  );
}
