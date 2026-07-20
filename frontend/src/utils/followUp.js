// Lead "sem contato" por tempo demais provavelmente foi esquecido — esse é
// o prazo a partir do qual avisamos que precisa de um follow-up.
export const DIAS_PARA_FOLLOW_UP = 5;

export function diasSemContato(lead) {
  if (!lead.criado_em) return 0;
  const ms = Date.now() - new Date(lead.criado_em).getTime();
  return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)));
}

export function precisaFollowUp(lead) {
  return lead.status === "sem_contato" && diasSemContato(lead) >= DIAS_PARA_FOLLOW_UP;
}
