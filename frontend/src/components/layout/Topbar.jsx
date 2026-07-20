import { useEffect, useRef, useState } from "react";
import { BASE_URL } from "../../api/client";
import HamburgerIcon from "../common/HamburgerIcon";

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

export default function Topbar({ perfil, onLogout, onAbrirPerfil, onAbrirAdmin }) {
  const [menuAberto, setMenuAberto] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!menuAberto) return;
    function handleClickFora(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuAberto(false);
      }
    }
    document.addEventListener("mousedown", handleClickFora);
    return () => document.removeEventListener("mousedown", handleClickFora);
  }, [menuAberto]);

  function irPara(acao) {
    setMenuAberto(false);
    acao();
  }

  const avatar = (
    <div className="avatar">
      {perfil.foto_url ? <img src={`${BASE_URL}${perfil.foto_url}`} alt="" /> : initials(perfil.nome)}
    </div>
  );

  return (
    <nav className="topbar">
      <div className="brand">
        <div className="logo-mark">Faro<span className="logo-suffix">CRM</span></div>
      </div>

      {/* Telas maiores: tudo visível lado a lado */}
      <div className="userbox userbox-desktop">
        {perfil.is_admin && (
          <span className="admin-link" onClick={onAbrirAdmin}>Administração</span>
        )}
        <button className="perfil-trigger" onClick={onAbrirPerfil} title="Ver perfil">
          {avatar}
          <span>{perfil.nome}</span>
        </button>
        <span className="sair" onClick={onLogout}>Sair</span>
      </div>

      {/* Telas pequenas: só a foto + um menu hambúrguer com as mesmas ações */}
      <div className="userbox-mobile" ref={menuRef}>
        {avatar}
        <button
          type="button"
          className="hamburguer"
          onClick={() => setMenuAberto((v) => !v)}
          aria-label="Abrir menu"
        >
          <HamburgerIcon />
        </button>
        {menuAberto && (
          <div className="menu-mobile">
            <button type="button" onClick={() => irPara(onAbrirPerfil)}>Ver perfil</button>
            {perfil.is_admin && (
              <button type="button" onClick={() => irPara(onAbrirAdmin)}>Administração</button>
            )}
            <button type="button" className="sair" onClick={() => irPara(onLogout)}>Sair</button>
          </div>
        )}
      </div>
    </nav>
  );
}
