import { useCallback, useRef, useState } from "react";

const DURATION_MS = 2200;

export function useToast() {
  const [message, setMessage] = useState(null);
  const timerRef = useRef(null);

  const showToast = useCallback((text) => {
    setMessage(text);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setMessage(null), DURATION_MS);
  }, []);

  return { toastMessage: message, showToast };
}
