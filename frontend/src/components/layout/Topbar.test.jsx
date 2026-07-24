import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Topbar from "./Topbar";

describe("Topbar", () => {
  it("com perfil.foto_url preenchido, renderiza uma img com o caminho no src", () => {
    const perfil = { nome: "Ana Silva", foto_url: "/uploads/foto.jpg" };
    const { container } = render(<Topbar perfil={perfil} onLogout={() => {}} onAbrirPerfil={() => {}} />);
    const imgs = container.querySelectorAll("img");
    expect(imgs.length).toBeGreaterThan(0);
    expect(imgs[0].src).toContain("/uploads/foto.jpg");
  });

  it("sem foto_url, renderiza as iniciais do nome", () => {
    const perfil = { nome: "Ana Silva" };
    render(<Topbar perfil={perfil} onLogout={() => {}} onAbrirPerfil={() => {}} />);
    expect(screen.getAllByText("AS").length).toBeGreaterThan(0);
  });

  it("botão de perfil (desktop) chama onAbrirPerfil ao clicar", () => {
    const onAbrirPerfil = vi.fn();
    const perfil = { nome: "Ana Silva" };
    const { container } = render(
      <Topbar perfil={perfil} onLogout={() => {}} onAbrirPerfil={onAbrirPerfil} />
    );
    const trigger = container.querySelector(".perfil-trigger");
    fireEvent.click(trigger);
    expect(onAbrirPerfil).toHaveBeenCalledTimes(1);
  });

  it("clicar em 'Sair' (desktop) chama onLogout", () => {
    const onLogout = vi.fn();
    const perfil = { nome: "Ana Silva" };
    render(<Topbar perfil={perfil} onLogout={onLogout} onAbrirPerfil={() => {}} />);
    const sairEls = screen.getAllByText("Sair");
    fireEvent.click(sairEls[0]);
    expect(onLogout).toHaveBeenCalledTimes(1);
  });

  it("hambúrguer abre o menu mobile ao clicar", () => {
    const perfil = { nome: "Ana Silva" };
    render(<Topbar perfil={perfil} onLogout={() => {}} onAbrirPerfil={() => {}} />);

    expect(screen.queryByText("Ver perfil")).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Abrir menu"));

    expect(screen.getByText("Ver perfil")).toBeInTheDocument();
    expect(screen.getAllByText("Sair").length).toBeGreaterThan(1);
  });

  it("clicar fora do menu mobile fecha o menu", () => {
    const perfil = { nome: "Ana Silva" };
    render(<Topbar perfil={perfil} onLogout={() => {}} onAbrirPerfil={() => {}} />);

    fireEvent.click(screen.getByLabelText("Abrir menu"));
    expect(screen.getByText("Ver perfil")).toBeInTheDocument();

    fireEvent.mouseDown(document.body);

    expect(screen.queryByText("Ver perfil")).not.toBeInTheDocument();
  });

  it("clicar em 'Sair' dentro do menu mobile fecha o menu e chama onLogout", () => {
    const onLogout = vi.fn();
    const perfil = { nome: "Ana Silva" };
    render(<Topbar perfil={perfil} onLogout={onLogout} onAbrirPerfil={() => {}} />);

    fireEvent.click(screen.getByLabelText("Abrir menu"));
    const menuMobileSair = screen.getAllByText("Sair").find((el) => el.tagName === "BUTTON");
    fireEvent.click(menuMobileSair);

    expect(onLogout).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Ver perfil")).not.toBeInTheDocument();
  });

  it("clicar em 'Ver perfil' dentro do menu mobile fecha o menu e chama onAbrirPerfil", () => {
    const onAbrirPerfil = vi.fn();
    const perfil = { nome: "Ana Silva" };
    render(<Topbar perfil={perfil} onLogout={() => {}} onAbrirPerfil={onAbrirPerfil} />);

    fireEvent.click(screen.getByLabelText("Abrir menu"));
    fireEvent.click(screen.getByText("Ver perfil"));

    expect(onAbrirPerfil).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Ver perfil")).not.toBeInTheDocument();
  });
});
