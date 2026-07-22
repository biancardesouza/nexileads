import { fotoSrc } from "../api/client";

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

export default function ProfilePage({ perfil, onVoltar }) {
  return (
    <>
      <header>
        <button type="button" className="btn perfil-voltar" onClick={onVoltar}>← Voltar</button>
        <h1>Meu perfil</h1>
        <p>Veja os dados da sua conta.</p>
      </header>

      <section className="wrap">
        <h2>Dados da conta</h2>
        <div className="perfil-body">
          <div className="perfil-foto-col">
            <div className="avatar avatar-lg">
              {perfil.foto_url ? <img src={fotoSrc(perfil.foto_url)} alt="" /> : initials(perfil.nome)}
            </div>
          </div>

          <div className="perfil-form">
            <div className="field">
              <label>Nome</label>
              <div className="perfil-valor">{perfil.nome}</div>
            </div>
            <div className="field">
              <label>E-mail</label>
              <div className="perfil-valor">{perfil.email || "—"}</div>
            </div>
            <div className="field">
              <label>Telefone</label>
              <div className="perfil-valor">{perfil.telefone || "—"}</div>
            </div>
            <p className="muted">
              Nome, e-mail, telefone e foto vêm da conta da empresa e não podem ser editados aqui.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
