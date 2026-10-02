/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base del agente. Por defecto usa el proxy de Vite ("/agent"). */
  readonly VITE_AGENT_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}