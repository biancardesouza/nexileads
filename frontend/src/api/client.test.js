import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, BASE_URL, fotoSrc } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fotoSrc", () => {
  it("retorna null quando fotoUrl é null", () => {
    expect(fotoSrc(null)).toBeNull();
  });

  it("retorna null quando fotoUrl é undefined", () => {
    expect(fotoSrc(undefined)).toBeNull();
  });

  it("retorna a própria URL quando já é uma URL completa https", () => {
    const url = "https://cdn.bubble.io/x.jpg";
    expect(fotoSrc(url)).toBe(url);
  });

  it("retorna a própria URL quando é protocol-relative (//)", () => {
    const url = "//cdn.bubble.io/x.jpg";
    expect(fotoSrc(url)).toBe(url);
  });

  it("prefixa com BASE_URL quando é um caminho relativo", () => {
    expect(fotoSrc("/uploads/x.jpg")).toBe(`${BASE_URL}/uploads/x.jpg`);
  });
});

describe("api (via request)", () => {
  it("login faz POST com credentials include (sessão é cookie httpOnly, não token no corpo)", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ nome: "Ana Silva" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const resultado = await api.login("a@b.com", "senha123");

    expect(resultado).toEqual({ nome: "Ana Silva" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/auth/login`);
    expect(options.method).toBe("POST");
    expect(options.credentials).toBe("include");
    expect(options.body).toBe(JSON.stringify({ email: "a@b.com", password: "senha123" }));
    expect(options.headers.Authorization).toBeUndefined();
    expect(options.headers["Content-Type"]).toBe("application/json");
  });

  it("logout faz POST para /auth/logout com credentials include", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => null });
    vi.stubGlobal("fetch", fetchMock);

    await api.logout();

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/auth/logout`);
    expect(options.method).toBe("POST");
    expect(options.credentials).toBe("include");
  });

  it("getLeads faz GET com credentials include (cookie de sessão vai automaticamente)", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ id: 1 }],
    });
    vi.stubGlobal("fetch", fetchMock);

    const resultado = await api.getLeads();

    expect(resultado).toEqual([{ id: 1 }]);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/leads`);
    expect(options.method).toBe("GET");
    expect(options.credentials).toBe("include");
    expect(options.headers.Authorization).toBeUndefined();
  });

  it("consultarCnpj remove caracteres não numéricos antes de montar a URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ razao_social: "Empresa X" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const resultado = await api.consultarCnpj("12.345.678/0001-99");

    expect(resultado).toEqual({ razao_social: "Empresa X" });
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/leads/consultar-cnpj/12345678000199`);
  });

  it("addLead faz POST para /leads com o corpo do lead", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 1 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const lead = { nome: "Empresa Y" };
    const resultado = await api.addLead(lead);

    expect(resultado).toEqual({ id: 1 });
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/leads`);
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify(lead));
  });

  it("salvarRegistro faz POST para /leads/:id/registros com status e nota", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await api.salvarRegistro(7, { status: "atendeu", nota: "ligar depois" });

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/leads/7/registros`);
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify({ status: "atendeu", nota: "ligar depois" }));
  });

  it("getNovosLeads faz GET para /leads/novos", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });
    vi.stubGlobal("fetch", fetchMock);

    await api.getNovosLeads();

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/leads/novos`);
    expect(options.method).toBe("GET");
  });

  it("ocultarLead faz POST para /leads/novos/ocultar com o cnpj", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await api.ocultarLead("12345678000199");

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/leads/novos/ocultar`);
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify({ cnpj: "12345678000199" }));
  });

  it("retorna null sem parsear JSON quando status é 204", async () => {
    const jsonSpy = vi.fn(async () => ({ nao: "deveria ser chamado" }));
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: jsonSpy,
    });
    vi.stubGlobal("fetch", fetchMock);

    const resultado = await api.deleteLead(42);

    expect(resultado).toBeNull();
    expect(jsonSpy).not.toHaveBeenCalled();
  });

  it("lança ApiError com a mensagem do corpo JSON (detail) e status correspondente", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: async () => ({ detail: "mensagem" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.getMe()).rejects.toMatchObject({
      message: "mensagem",
      status: 401,
    });
    await expect(api.getMe()).rejects.toBeInstanceOf(ApiError);
  });

  it("lança ApiError usando statusText quando o corpo não é JSON válido", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => {
        throw new Error("corpo inválido");
      },
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.getMe()).rejects.toMatchObject({
      message: "Internal Server Error",
      status: 500,
    });
  });
});
