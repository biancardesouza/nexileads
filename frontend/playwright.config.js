import { defineConfig } from "@playwright/test";

// Caminho do python do venv do backend — layout do venv difere entre
// Windows (Scripts/python.exe) e Linux/Mac (bin/python), este último é o
// que roda num futuro CI.
const pythonVenv = process.platform === "win32" ? ".\\venv\\Scripts\\python.exe" : "./venv/bin/python";

// Sobe o backend real (com Bubble/BrasilAPI mockados via respx — ver
// backend/tests_e2e/) e o frontend real (Vite dev server), e roda os
// testes em e2e/ contra os dois. Portas diferentes das usadas em dev
// (8000/5173) pra não colidir com um servidor de desenvolvimento já aberto.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  reporter: "html",
  use: {
    baseURL: "http://localhost:4173",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: `${pythonVenv} -m tests_e2e.server`,
      cwd: "../backend",
      port: 8001,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "npm run dev -- --port 4173 --strictPort",
      env: { VITE_API_URL: "http://localhost:8001" },
      port: 4173,
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
