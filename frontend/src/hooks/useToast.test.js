import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useToast } from "./useToast";

const DURATION_MS = 2200;

describe("useToast", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("inicia com toastMessage nulo", () => {
    const { result } = renderHook(() => useToast());
    expect(result.current.toastMessage).toBeNull();
  });

  it("showToast define a mensagem imediatamente", () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast("texto");
    });

    expect(result.current.toastMessage).toBe("texto");
  });

  it("mantém a mensagem antes de DURATION_MS ter passado", () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast("texto");
    });

    act(() => {
      vi.advanceTimersByTime(DURATION_MS - 1);
    });

    expect(result.current.toastMessage).toBe("texto");
  });

  it("limpa a mensagem depois de DURATION_MS", () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast("texto");
    });

    act(() => {
      vi.advanceTimersByTime(DURATION_MS);
    });

    expect(result.current.toastMessage).toBeNull();
  });

  it("reinicia o timer ao chamar showToast novamente antes da mensagem sumir", () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showToast("primeira");
    });

    act(() => {
      vi.advanceTimersByTime(DURATION_MS - 500);
    });
    expect(result.current.toastMessage).toBe("primeira");

    act(() => {
      result.current.showToast("segunda");
    });

    // Passou o tempo total desde a primeira chamada (que já ultrapassaria os
    // 2200ms dela), mas o timer foi reiniciado pela segunda chamada, então a
    // mensagem ainda deve estar visível.
    act(() => {
      vi.advanceTimersByTime(DURATION_MS - 500);
    });
    expect(result.current.toastMessage).toBe("segunda");

    // Agora sim passou 2200ms desde a SEGUNDA chamada.
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current.toastMessage).toBeNull();
  });
});
