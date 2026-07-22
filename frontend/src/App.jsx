import { useEffect, useState } from "react";
import LoginPage from "./pages/LoginPage";
import LeadsPage from "./pages/LeadsPage";
import ProfilePage from "./pages/ProfilePage";
import Topbar from "./components/layout/Topbar";
import { api, ApiError, clearToken, getToken } from "./api/client";

export default function App() {
  const [perfil, setPerfil] = useState(null);
  const [restaurandoSessao, setRestaurandoSessao] = useState(true);
  const [tela, setTela] = useState("leads");

  function carregarPerfil() {
    return api.getMe().then(setPerfil);
  }

  // Se já existe um token salvo (login anterior), tenta restaurar a sessão em
  // vez de jogar a pessoa de volta pra tela de login a cada F5.
  useEffect(() => {
    if (!getToken()) {
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
      />

      {tela === "perfil" && <ProfilePage perfil={perfil} onVoltar={() => setTela("leads")} />}
      {tela === "leads" && <LeadsPage onSessionExpired={handleLogout} />}
    </div>
  );
}
