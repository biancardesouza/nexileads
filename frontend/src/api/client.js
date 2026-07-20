export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "faro_token";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // resposta sem corpo JSON
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return null;
  return res.json();
}

async function requestMultipart(path, formData) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { method: "POST", headers, body: formData });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // resposta sem corpo JSON
    }
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

export const api = {
  login(username, password) {
    return request("/auth/login", { method: "POST", body: { username, password }, auth: false });
  },
  getMe() {
    return request("/auth/me");
  },
  updatePerfil({ username, nome, email, telefone }) {
    return request("/auth/me", { method: "PATCH", body: { username, nome, email, telefone } });
  },
  alterarSenha({ senha_atual, nova_senha }) {
    return request("/auth/me/senha", { method: "PATCH", body: { senha_atual, nova_senha } });
  },
  esqueciSenha(identificador) {
    return request("/auth/esqueci-senha", { method: "POST", body: { identificador }, auth: false });
  },
  redefinirSenha({ token, nova_senha }) {
    return request("/auth/redefinir-senha", { method: "POST", body: { token, nova_senha }, auth: false });
  },
  uploadFoto(file) {
    const formData = new FormData();
    formData.append("foto", file);
    return requestMultipart("/auth/me/foto", formData);
  },
  deleteAccount(password) {
    return request("/auth/me", { method: "DELETE", body: { password } });
  },
  getLeads() {
    return request("/leads");
  },
  addLead(lead) {
    return request("/leads", { method: "POST", body: lead });
  },
  consultarCnpj(cnpj) {
    const digitos = cnpj.replace(/\D/g, "");
    return request(`/leads/consultar-cnpj/${digitos}`);
  },
  deleteLead(id) {
    return request(`/leads/${id}`, { method: "DELETE" });
  },
  salvarRegistro(id, { status, nota }) {
    return request(`/leads/${id}/registros`, { method: "POST", body: { status, nota } });
  },
  getNovosLeads() {
    return request("/leads/novos");
  },
  ocultarLead(cnpj) {
    return request("/leads/novos/ocultar", { method: "POST", body: { cnpj } });
  },
  listarUsuariosAdmin() {
    return request("/admin/usuarios");
  },
  criarUsuarioAdmin(dados) {
    return request("/admin/usuarios", { method: "POST", body: dados });
  },
  resetarSenhaAdmin(id) {
    return request(`/admin/usuarios/${id}/resetar-senha`, { method: "POST" });
  },
  excluirUsuarioAdmin(id) {
    return request(`/admin/usuarios/${id}`, { method: "DELETE" });
  },
  listarAuditoriaAdmin() {
    return request("/admin/auditoria");
  },
};
