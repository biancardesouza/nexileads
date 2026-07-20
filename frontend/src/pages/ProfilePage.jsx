import { useRef, useState } from "react";
import { api, ApiError, BASE_URL, setToken } from "../api/client";
import { useToast } from "../hooks/useToast";
import Toast from "../components/common/Toast";
import EyeIcon from "../components/common/EyeIcon";

const SENHA_FORM_VAZIO = { senha_atual: "", nova_senha: "", confirmar: "" };

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function telefoneValido(telefone) {
  const digitos = telefone.replace(/\D/g, "");
  return digitos.length === 10 || digitos.length === 11;
}

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function validar(form) {
  if (!form.username.trim()) return "Informe um usuário.";
  if (!form.nome.trim()) return "Informe um nome.";
  if (form.email && !EMAIL_REGEX.test(form.email)) return "E-mail inválido.";
  if (form.telefone && !telefoneValido(form.telefone)) {
    return "Telefone inválido. Use o formato (11) 91234-5678 ou apenas os números.";
  }
  return null;
}

export default function ProfilePage({ perfil, onPerfilAtualizado, onVoltar, onContaExcluida, onSessionExpired }) {
  const [editando, setEditando] = useState(false);
  const [form, setForm] = useState({
    username: perfil.username,
    nome: perfil.nome,
    email: perfil.email || "",
    telefone: perfil.telefone || "",
  });
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [fotoEnviando, setFotoEnviando] = useState(false);
  const [excluir, setExcluir] = useState({ aberto: false, senha: "", enviando: false, erro: "" });
  const { toastMessage, showToast } = useToast();
  const fileInputRef = useRef(null);

  const [senhaAberta, setSenhaAberta] = useState(false);
  const [senhaForm, setSenhaForm] = useState(SENHA_FORM_VAZIO);
  const [senhaEnviando, setSenhaEnviando] = useState(false);
  const [senhaErro, setSenhaErro] = useState("");
  const [verSenhaAtual, setVerSenhaAtual] = useState(false);
  const [verNovaSenha, setVerNovaSenha] = useState(false);

  function iniciarEdicao() {
    setForm({
      username: perfil.username,
      nome: perfil.nome,
      email: perfil.email || "",
      telefone: perfil.telefone || "",
    });
    setErro("");
    setEditando(true);
  }

  function cancelarEdicao() {
    setEditando(false);
    setErro("");
  }

  async function salvar(e) {
    e.preventDefault();
    const mensagemValidacao = validar(form);
    if (mensagemValidacao) {
      setErro(mensagemValidacao);
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const { access_token, ...perfilAtualizado } = await api.updatePerfil(form);
      setToken(access_token);
      onPerfilAtualizado(perfilAtualizado);
      setEditando(false);
      showToast("Perfil atualizado");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onSessionExpired();
        return;
      }
      setErro(err.message || "Não foi possível salvar. Tente novamente.");
    } finally {
      setSalvando(false);
    }
  }

  async function handleFotoSelecionada(e) {
    const file = e.target.files[0];
    if (!file) return;
    setFotoEnviando(true);
    try {
      const atualizado = await api.uploadFoto(file);
      onPerfilAtualizado(atualizado);
      showToast("Foto atualizada");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onSessionExpired();
        return;
      }
      showToast(err.message || "Não foi possível enviar a foto.");
    } finally {
      setFotoEnviando(false);
      e.target.value = "";
    }
  }

  function iniciarAlterarSenha() {
    setSenhaForm(SENHA_FORM_VAZIO);
    setSenhaErro("");
    setVerSenhaAtual(false);
    setVerNovaSenha(false);
    setSenhaAberta(true);
  }

  function cancelarAlterarSenha() {
    setSenhaAberta(false);
    setSenhaErro("");
  }

  async function salvarNovaSenha(e) {
    e.preventDefault();
    if (senhaForm.nova_senha.length < 6) {
      setSenhaErro("A nova senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (senhaForm.nova_senha !== senhaForm.confirmar) {
      setSenhaErro("As senhas não coincidem.");
      return;
    }
    setSenhaEnviando(true);
    setSenhaErro("");
    try {
      await api.alterarSenha({ senha_atual: senhaForm.senha_atual, nova_senha: senhaForm.nova_senha });
      setSenhaAberta(false);
      // Trocar a senha invalida a sessão atual no servidor — em vez de deixar
      // a próxima ação qualquer falhar com um 401 sem explicação, avisamos e
      // já levamos pro login de novo.
      showToast("Senha alterada. Faça login novamente.");
      setTimeout(onSessionExpired, 2200);
    } catch (err) {
      setSenhaErro(err.message || "Não foi possível alterar a senha.");
    } finally {
      setSenhaEnviando(false);
    }
  }

  async function confirmarExclusao() {
    setExcluir((prev) => ({ ...prev, enviando: true, erro: "" }));
    try {
      await api.deleteAccount(excluir.senha);
      onContaExcluida();
    } catch (err) {
      setExcluir((prev) => ({ ...prev, enviando: false, erro: err.message || "Não foi possível excluir a conta." }));
    }
  }

  return (
    <>
      <header>
        <button type="button" className="btn perfil-voltar" onClick={onVoltar}>← Voltar</button>
        <h1>Meu perfil</h1>
        <p>Veja e edite os dados da sua conta.</p>
      </header>

      <section className="wrap">
        <h2>Dados da conta</h2>
        <div className="perfil-body">
          <div className="perfil-foto-col">
            <div className="avatar avatar-lg">
              {perfil.foto_url ? <img src={`${BASE_URL}${perfil.foto_url}`} alt="" /> : initials(perfil.nome)}
            </div>
            <button
              type="button"
              className="btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={fotoEnviando}
            >
              {fotoEnviando ? "Enviando..." : "Trocar foto"}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              style={{ display: "none" }}
              onChange={handleFotoSelecionada}
            />
          </div>

          <form className="perfil-form" onSubmit={salvar}>
            <div className="field">
              <label>Nome</label>
              {editando ? (
                <input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
              ) : (
                <div className="perfil-valor">{perfil.nome}</div>
              )}
            </div>
            <div className="field">
              <label>Usuário</label>
              {editando ? (
                <input
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                />
              ) : (
                <div className="perfil-valor muted">{perfil.username}</div>
              )}
            </div>
            <div className="field">
              <label>E-mail</label>
              {editando ? (
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="seu@email.com"
                />
              ) : (
                <div className="perfil-valor">{perfil.email || "—"}</div>
              )}
            </div>
            <div className="field">
              <label>Telefone</label>
              {editando ? (
                <input
                  value={form.telefone}
                  onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                  placeholder="(11) 90000-0000"
                />
              ) : (
                <div className="perfil-valor">{perfil.telefone || "—"}</div>
              )}
            </div>

            {erro && <div className="login-erro">{erro}</div>}

            <div className="perfil-acoes">
              {!editando && (
                <button type="button" className="btn-salvar" onClick={iniciarEdicao}>Editar</button>
              )}
              {editando && (
                <>
                  <button type="button" className="btn" onClick={cancelarEdicao} disabled={salvando}>
                    Cancelar
                  </button>
                  <button type="submit" className="btn-salvar" disabled={salvando}>
                    {salvando ? "Salvando..." : "Salvar"}
                  </button>
                </>
              )}
            </div>
          </form>
        </div>
      </section>

      <section className="wrap">
        <h2>Alterar senha</h2>
        <div className="secao-body">
          {!senhaAberta ? (
            <>
              <p className="muted">Defina uma nova senha para acessar sua conta.</p>
              <button className="btn-salvar" onClick={iniciarAlterarSenha}>Alterar senha</button>
            </>
          ) : (
            <form className="perfil-form" onSubmit={salvarNovaSenha}>
              <div className="field">
                <label>Senha atual</label>
                <div className="input-com-icone">
                  <input
                    type={verSenhaAtual ? "text" : "password"}
                    value={senhaForm.senha_atual}
                    onChange={(e) => setSenhaForm({ ...senhaForm, senha_atual: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    className="btn-olho"
                    tabIndex={-1}
                    onClick={() => setVerSenhaAtual((v) => !v)}
                    title={verSenhaAtual ? "Ocultar senha" : "Mostrar senha"}
                  >
                    <EyeIcon visivel={verSenhaAtual} />
                  </button>
                </div>
              </div>
              <div className="field">
                <label>Nova senha</label>
                <div className="input-com-icone">
                  <input
                    type={verNovaSenha ? "text" : "password"}
                    value={senhaForm.nova_senha}
                    onChange={(e) => setSenhaForm({ ...senhaForm, nova_senha: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    className="btn-olho"
                    tabIndex={-1}
                    onClick={() => setVerNovaSenha((v) => !v)}
                    title={verNovaSenha ? "Ocultar senha" : "Mostrar senha"}
                  >
                    <EyeIcon visivel={verNovaSenha} />
                  </button>
                </div>
              </div>
              <div className="field">
                <label>Confirmar nova senha</label>
                <input
                  type={verNovaSenha ? "text" : "password"}
                  value={senhaForm.confirmar}
                  onChange={(e) => setSenhaForm({ ...senhaForm, confirmar: e.target.value })}
                  required
                />
              </div>

              {senhaErro && <div className="login-erro">{senhaErro}</div>}

              <div className="perfil-acoes">
                <button type="button" className="btn" onClick={cancelarAlterarSenha} disabled={senhaEnviando}>
                  Cancelar
                </button>
                <button type="submit" className="btn-salvar" disabled={senhaEnviando}>
                  {senhaEnviando ? "Salvando..." : "Salvar nova senha"}
                </button>
              </div>
            </form>
          )}
        </div>
      </section>

      <section className="wrap perigo">
        <h2>Excluir conta</h2>
        <div className="perigo-body">
          <p className="muted">
            Essa ação é permanente e remove todos os seus leads salvos. Não é possível desfazer.
          </p>
          {!excluir.aberto ? (
            <button
              className="btn-perigo"
              onClick={() => setExcluir({ aberto: true, senha: "", enviando: false, erro: "" })}
            >
              Excluir minha conta
            </button>
          ) : (
            <div className="perigo-confirmar">
              <div className="field">
                <label>Confirme sua senha para excluir</label>
                <input
                  type="password"
                  value={excluir.senha}
                  onChange={(e) => setExcluir((prev) => ({ ...prev, senha: e.target.value }))}
                  placeholder="••••••••"
                />
              </div>
              {excluir.erro && <div className="login-erro">{excluir.erro}</div>}
              <div className="perfil-acoes">
                <button
                  className="btn"
                  onClick={() => setExcluir({ aberto: false, senha: "", enviando: false, erro: "" })}
                  disabled={excluir.enviando}
                >
                  Cancelar
                </button>
                <button
                  className="btn-perigo"
                  onClick={confirmarExclusao}
                  disabled={excluir.enviando || !excluir.senha}
                >
                  {excluir.enviando ? "Excluindo..." : "Confirmar exclusão"}
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      <Toast message={toastMessage} />
    </>
  );
}
