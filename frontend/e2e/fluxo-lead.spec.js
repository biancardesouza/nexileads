import { test, expect } from "@playwright/test";

// Precisam ficar em sincronia com backend/tests_e2e/bubble_mock.py (JS não
// pode importar direto de lá) — se mudar um lado, mude o outro.
const E2E_EMAIL = "e2e@nexileads.test";
const E2E_SENHA = "senha-e2e-123";
const E2E_CNPJ = "12345678000199";
const E2E_RAZAO_SOCIAL = "Empresa E2E Testes Ltda";

async function login(page, { email = E2E_EMAIL, senha = E2E_SENHA } = {}) {
  await page.goto("/");
  await page.getByPlaceholder("seu@email.com").fill(email);
  await page.getByPlaceholder("••••••••").fill(senha);
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("login com senha errada mostra erro e permanece na tela de login", async ({ page }) => {
  await login(page, { senha: "senha-errada" });

  await expect(page.getByText("E-mail ou senha inválidos")).toBeVisible();
  await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible();
});

test("login, adicionar lead por CNPJ, registrar ligação e logout", async ({ page }) => {
  await login(page);

  await expect(page.getByRole("heading", { name: "Painel de leads" })).toBeVisible();

  // Adicionar lead por CNPJ
  await page.getByPlaceholder("00.000.000/0001-91").fill(E2E_CNPJ);
  await page.getByRole("button", { name: "Buscar" }).click();

  await expect(page.getByText(E2E_RAZAO_SOCIAL)).toBeVisible();
  await page.getByRole("button", { name: "+ Adicionar aos meus leads" }).click();

  // Filtra por `td.cnpj` pra pegar só o <tr> da linha na tabela (SavedLeadRow)
  // — sem isso, assim que o detalhe (LeadDetail) abre num <tr> separado logo
  // abaixo, ele também contém a razão social e passaria a bater no mesmo
  // locator por texto, ambíguo.
  const linhaLead = page.locator("tr").filter({ has: page.locator("td.cnpj") }).filter({ hasText: E2E_RAZAO_SOCIAL });
  await expect(linhaLead).toBeVisible();
  await expect(linhaLead.getByText("Sem contato ainda")).toBeVisible();

  // Registrar ligação e mudar o status
  await linhaLead.getByRole("button", { name: "Ver mais" }).click();
  // Há também um <select> de filtro com uma <option>"Atendeu" em outro lugar
  // da página, e "Não atendeu" contém "atendeu" (hasText ignora
  // maiúsc./minúsc.) — escopar pro `.vbar` do LeadDetail com exact:true evita
  // a ambiguidade.
  await page.locator(".vbar").getByText("Atendeu", { exact: true }).click();
  await page.getByPlaceholder("Como foi a ligação? Anote aqui...").fill("Cliente demonstrou interesse.");
  await page.getByRole("button", { name: "Salvar registro" }).click();

  // A mesma nota aparece duas vezes (resumo na linha da tabela + histórico
  // completo no detalhe) — `.tx-obs` escopa pro item do histórico.
  await expect(page.locator(".tx-obs", { hasText: "Cliente demonstrou interesse." })).toBeVisible();
  await expect(linhaLead.getByText("Atendeu", { exact: true })).toBeVisible();

  // Logout
  await page.getByText("Sair", { exact: true }).click();
  await expect(page.getByPlaceholder("seu@email.com")).toBeVisible();
});
