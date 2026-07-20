import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { useToast } from "../hooks/useToast";
import Toast from "../components/common/Toast";
import TrashIcon from "../components/common/TrashIcon";
import { formatarDataHora } from "../utils/formatDate";

const FORM_VAZIO = { username: "", nome: "", password: "", is_admin: false };
const SENHA_MINIMA = 6;

const ACOES = {
  criar_usuario: "Criou usuário",
  resetar_senha: "Resetou senha",
  excluir_usuario: "Excluiu usuário",
};

export default function AdminPage({ perfil, onVoltar, onSessionExpired }) {
  const [usuarios, setUsuarios] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erroLista, setErroLista] = useState("");

  const [form, setForm] = useState(FORM_VAZIO);
  const [criando, setCriando] = useState(false);
  const [erroForm, setErroForm] = useState("");

  const [senhaGerada, setSenhaGerada] = useState(null); // { userId, senha }
  const [resetandoId, setResetandoId] = useState(null);
  const [excluirAlvo, setExcluirAlvo] = useState(null); // { id, nome }
  const [excluindo, setExcluindo] = useState(false);

  const [auditoria, setAuditoria] = useState([]);
  const [carregandoAuditoria, setCarregandoAuditoria] = useState(true);
  const [erroAuditoria, setErroAuditoria] = useState("");

  const { toastMessage, showToast } = useToast();

  function ehSessaoExpirada(err) {
    if (err instanceof ApiError && err.status === 401) {
      onSessionExpired();
      return true;
    }
    return false;
  }

  function carregarUsuarios() {
    setCarregando(true);
    return api
      .listarUsuariosAdmin()
      .then(setUsuarios)
      .catch((err) => {
        if (ehSessaoExpirada(err)) return;
        setErroLista(err.message || "Não foi possível carregar os usuários.");
      })
      .finally(() => setCarregando(false));
  }

  function carregarAuditoria() {
    setCarregandoAuditoria(true);
    return api
      .listarAuditoriaAdmin()
      .then(setAuditoria)
      .catch((err) => {
        if (ehSessaoExpirada(err)) return;
        setErroAuditoria(err.message || "Não foi possível carregar o histórico.");
      })
      .finally(() => setCarregandoAuditoria(false));
  }

  useEffect(() => {
    carregarUsuarios();
    carregarAuditoria();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function criarUsuario(e) {
    e.preventDefault();
    if (criando) return;
    if (!form.username.trim() || !form.nome.trim() || !form.password) {
      setErroForm("Preencha usuário, nome e senha.");
      return;
    }
    if (form.password.length < SENHA_MINIMA) {
      setErroForm(`A senha deve ter pelo menos ${SENHA_MINIMA} caracteres.`);
      return;
    }
    setCriando(true);
    setErroForm("");
    try {
      const novo = await api.criarUsuarioAdmin(form);
      setUsuarios((prev) => [...prev, novo]);
      setForm(FORM_VAZIO);
      showToast("Usuário criado");
      carregarAuditoria();
    } catch (err) {
      if (ehSessaoExpirada(err)) return;
      setErroForm(err.message || "Não foi possível criar o usuário.");
    } finally {
      setCriando(false);
    }
  }

  async function resetarSenha(usuario) {
    setResetandoId(usuario.id);
    setSenhaGerada(null);
    try {
      const { nova_senha } = await api.resetarSenhaAdmin(usuario.id);
      setSenhaGerada({ userId: usuario.id, senha: nova_senha });
      carregarAuditoria();
    } catch (err) {
      if (ehSessaoExpirada(err)) return;
      showToast(err.message || "Não foi possível resetar a senha.");
    } finally {
      setResetandoId(null);
    }
  }

  async function confirmarExclusao() {
    setExcluindo(true);
    try {
      await api.excluirUsuarioAdmin(excluirAlvo.id);
      setUsuarios((prev) => prev.filter((u) => u.id !== excluirAlvo.id));
      showToast("Usuário excluído");
      setExcluirAlvo(null);
      carregarAuditoria();
    } catch (err) {
      if (ehSessaoExpirada(err)) return;
      showToast(err.message || "Não foi possível excluir o usuário.");
    } finally {
      setExcluindo(false);
    }
  }

  return (
    <>
      <header>
        <button type="button" className="btn perfil-voltar" onClick={onVoltar}>← Voltar</button>
        <h1>Administração</h1>
        <p>Gerencie as contas de usuário do sistema.</p>
      </header>

      <section className="wrap">
        <h2>Novo usuário</h2>
        <form className="perfil-form admin-form" onSubmit={criarUsuario}>
          <div className="field">
            <label>Nome</label>
            <input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          </div>
          <div className="field">
            <label>Usuário</label>
            <input
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Senha</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <div className="field field-checkbox">
            <label>
              <input
                type="checkbox"
                checked={form.is_admin}
                onChange={(e) => setForm({ ...form, is_admin: e.target.checked })}
              />
              {" "}Também é administrador
            </label>
          </div>

          {erroForm && <div className="login-erro">{erroForm}</div>}

          <div className="perfil-acoes">
            <button type="submit" className="btn-salvar" disabled={criando}>
              {criando ? "Criando..." : "Criar usuário"}
            </button>
          </div>
        </form>
      </section>

      <section className="wrap">
        <h2>Usuários</h2>
        {carregando && <p className="muted">Carregando...</p>}
        {erroLista && <div className="login-erro">{erroLista}</div>}

        {!carregando && !erroLista && (
          <table>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Usuário</th>
                <th>E-mail</th>
                <th>Telefone</th>
                <th>Leads</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => {
                const ehVoce = u.username === perfil.username;
                return (
                  <tr key={u.id}>
                    <td>
                      {u.nome}
                      {u.is_admin && <span className="badge-admin">admin</span>}
                    </td>
                    <td className="muted">{u.username}</td>
                    <td className="muted">{u.email || "—"}</td>
                    <td className="muted">{u.telefone || "—"}</td>
                    <td>{u.total_leads}</td>
                    <td className="admin-acoes">
                      <button
                        type="button"
                        className="btn"
                        onClick={() => resetarSenha(u)}
                        disabled={resetandoId === u.id}
                      >
                        {resetandoId === u.id ? "Gerando..." : "Resetar senha"}
                      </button>
                      <button
                        type="button"
                        className="btn btn-icon"
                        title={ehVoce ? "Você não pode excluir sua própria conta por aqui" : "Excluir usuário"}
                        onClick={() => setExcluirAlvo({ id: u.id, nome: u.nome })}
                        disabled={ehVoce}
                      >
                        <TrashIcon />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {senhaGerada && (
          <div className="admin-senha-gerada">
            Nova senha para {usuarios.find((u) => u.id === senhaGerada.userId)?.nome}:{" "}
            <code>{senhaGerada.senha}</code>
            <button type="button" className="btn" onClick={() => setSenhaGerada(null)}>Ok</button>
          </div>
        )}
      </section>

      <section className="wrap">
        <h2>Histórico de ações</h2>
        {carregandoAuditoria && <p className="muted">Carregando...</p>}
        {erroAuditoria && <div className="login-erro">{erroAuditoria}</div>}

        {!carregandoAuditoria && !erroAuditoria && (
          auditoria.length === 0 ? (
            <p className="empty">Nenhuma ação registrada ainda.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Quando</th>
                  <th>Admin</th>
                  <th>Ação</th>
                  <th>Alvo</th>
                  <th>Detalhes</th>
                </tr>
              </thead>
              <tbody>
                {auditoria.map((log) => (
                  <tr key={log.id}>
                    <td className="muted">{formatarDataHora(log.criado_em)}</td>
                    <td>{log.admin_username}</td>
                    <td>{ACOES[log.acao] || log.acao}</td>
                    <td className="muted">{log.alvo_username}</td>
                    <td className="muted">{log.detalhes || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}
      </section>

      {excluirAlvo && (
        <section className="wrap perigo">
          <h2>Excluir usuário</h2>
          <div className="perigo-body">
            <p className="muted">
              Tem certeza que deseja excluir <strong>{excluirAlvo.nome}</strong>? Essa ação é permanente e remove
              todos os leads dessa conta.
            </p>
            <div className="perfil-acoes">
              <button className="btn" onClick={() => setExcluirAlvo(null)} disabled={excluindo}>
                Cancelar
              </button>
              <button className="btn-perigo" onClick={confirmarExclusao} disabled={excluindo}>
                {excluindo ? "Excluindo..." : "Confirmar exclusão"}
              </button>
            </div>
          </div>
        </section>
      )}

      <Toast message={toastMessage} />
    </>
  );
}
