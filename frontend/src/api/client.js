export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "nexileads_token";

// foto_url pode ser um caminho local (upload direto no Faro, ex: "/uploads/x.jpg",
// precisa do BASE_URL na frente) ou uma URL já completa vinda do Bubble
// (ex: "//cdn.bubble.io/...jpg" ou "https://..."), que não pode ser prefixada.
export function fotoSrc(fotoUrl) {
  if (!fotoUrl) return null;
  if (/^(https?:)?\/\//.test(fotoUrl)) return fotoUrl;
  return `${BASE_URL}${fotoUrl}`;
}

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

export const api = {
  login(email, password) {
    return request("/auth/login", { method: "POST", body: { email, password }, auth: false });
  },
  getMe() {
    return request("/auth/me");
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
};
