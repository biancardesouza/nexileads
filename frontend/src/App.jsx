import { useEffect, useState } from "react";
import LoginPage from "./pages/LoginPage";
import LeadsPage from "./pages/LeadsPage";
import ProfilePage from "./pages/ProfilePage";
import Topbar from "./components/layout/Topbar";
import { api } from "./api/client";

export default function App() {
  const [perfil, setPerfil] = useState(null);
  const [restaurandoSessao, setRestaurandoSessao] = useState(true);
  const [tela, setTela] = useState("leads");

  function carregarPerfil() {
    return api.getMe().then(setPerfil);
  }

  // A sessão é um cookie httpOnly — o JS não consegue ler se ele existe, então
  // sempre tentamos restaurar o perfil ao carregar a página; sem sessão válida
  // o backend só responde 401 e a gente cai na tela de login normalmente.
  useEffect(() => {
    carregarPerfil()
      .catch(() => {})
      .finally(() => setRestaurandoSessao(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleLogin() {
    setRestaurandoSessao(true);
    return carregarPerfil().finally(() => setRestaurandoSessao(false));
  }

  function handleLogout() {
    // Sendo httpOnly, o front não pode apagar o cookie por conta própria —
    // precisa desse endpoint pra fazer o backend invalidá-lo de verdade. Se a
    // chamada falhar (rede fora, etc), desloga a UI mesmo assim.
    api.logout()
      .catch(() => {})
      .finally(() => {
        setPerfil(null);
        setTela("leads");
      });
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
