export interface SuggestionPrompt {
  readonly id: string;
  readonly label: string;
  readonly prompt: string;
}

export const APP_META = {
  name: 'Agente de Inventario',
  tagline: 'Existencias, riesgos, pron\u00f3sticos y alertas consultadas en vivo.',
  source: 'Backend Django + 19 herramientas de inventario',
} as const;

export const SUGGESTION_PROMPTS: readonly SuggestionPrompt[] = [
  { id: 'panorama', label: 'Panorama general', prompt: 'Dame un panorama general del inventario' },
  { id: 'desabasto', label: 'Riesgo de agotamiento', prompt: '\u00bfQu\u00e9 productos tienen riesgo de agotarse?' },
  { id: 'reposicion', label: 'Qu\u00e9 reponer primero', prompt: '\u00bfQu\u00e9 productos deber\u00eda reponer primero?' },
  {
    id: 'sobreinventario',
    label: 'Exceso de inventario',
    prompt: '\u00bfQu\u00e9 productos tienen exceso de inventario?',
  },
  { id: 'rotacion', label: 'Rotaci\u00f3n', prompt: 'Analiza la rotaci\u00f3n del inventario' },
  { id: 'caducidades', label: 'Caducidades', prompt: '\u00bfQu\u00e9 lotes est\u00e1n pr\u00f3ximos a caducar?' },
  {
    id: 'existencias',
    label: 'Existencias',
    prompt: '\u00bfCu\u00e1ntas existencias hay del producto 680 y en qu\u00e9 ubicaciones?',
  },
  { id: 'alertas', label: 'Alertas pendientes', prompt: 'Mu\u00e9strame las alertas pendientes' },
];

export const UI_TEXT = {
  composerPlaceholder: 'Escribe tu pregunta. Enter envia, Shift+Enter agrega una l\u00ednea.',
  composerLabel: 'Pregunta para el agente',
  send: 'Enviar',
  stop: 'Detener',
  copy: 'Copiar',
  copied: 'Copiado',
  newConversation: 'Nueva conversaci\u00f3n',
  thinking: 'Consultando el inventario',
  thinkingHint: 'El agente consulta varias herramientas, por eso puede tardar de 10 a 60 segundos.',
  emptyTitle: '\u00bfQu\u00e9 necesitas saber del inventario?',
  emptyHint: 'Elige una pregunta sugerida o escribe la tuya. Las respuestas se muestran con tablas y formato.',
  you: 'T\u00fa',
  agent: 'Agente',
  themeToggle: 'Cambiar tema',
  sessionLabel: 'Sesi\u00f3n',
  conversationStart: 'Conversaci\u00f3n nueva',
  disclaimer:
    'Las cifras provienen del dataset AdventureWorks con fecha de an\u00e1lisis 2025-06-29. Verifica la vigencia antes de tomar decisiones.',
  listRegion: 'Lista de mensajes de la conversaci\u00f3n',
  agentOffline:
    'No se pudo contactar al agente en :8090. Levanta el servicio con docker compose up -d agent desde inventory_backend.',
} as const;

/**
 * El agente responde con HTTP 200 incluso cuando no logra llamar al modelo.
 * Estos prefijos permiten distinguir esa situacion y pintar la burbuja como error.
 */
export const AGENT_FAILURE_PREFIXES: readonly string[] = [
  'No se puede comunicar con el agente',
  'La operacion necesito demasiadas rondas',
];