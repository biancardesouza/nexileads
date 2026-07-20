export function formatarDataHora(isoString) {
  const data = new Date(isoString);
  return (
    data.toLocaleDateString("pt-BR") +
    " " +
    data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
  );
}
