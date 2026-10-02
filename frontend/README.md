# Agente de Inventario - Frontend

Interfaz de chat para el agente de inventario (React 19 + Vite + TypeScript + Tailwind v4).

## Dos formas de ejecutarlo

### Docker (recomendado, igual que produccion)

El frontend forma parte del `docker-compose.yml` de `inventory_backend`:

```bash
cd ../inventory_backend
docker compose up -d --build frontend
```

Queda en `http://localhost:5173`. La imagen es multi-etapa: Node compila y nginx
sirve `dist/`. El `Dockerfile` hace `npm ci` y `npm run build`, asi que el
typecheck corre tambien dentro del build.

Desde el navegador solo se ve un origen: nginx hace proxy de `/agent/` hacia el
servicio `agent` de la red de Docker. Por eso el codigo del cliente es
identico en desarrollo y en el contenedor.

### Desarrollo local

```bash
npm install
npm run dev
```

La app queda en `http://localhost:5173` y el proxy de Vite reenvia `/agent`
hacia `http://localhost:8090`.

## Requisitos

- Node.js 20 o superior para el modo de desarrollo.
- Docker Compose para el modo en contenedor.

## Comandos

| Comando           | Que hace                                          |
| ----------------- | ------------------------------------------------- |
| `npm run dev`     | Servidor de desarrollo con proxy hacia el agente  |
| `npm run build`   | `tsc --noEmit` y luego build de produccion        |
| `npm run preview` | Sirve `dist/` localmente                          |

## Como se conecta con el agente

En ambos modos se usa la ruta relativa `/agent`. En desarrollo la reescribe el
proxy de `vite.config.ts` hacia `http://localhost:8090`; en el contenedor la
reescribe nginx hacia `http://agent:8080`. El navegador nunca cruza de origen.

Si sirves el build desde otro dominio, define la URL completa del agente:

```bash
VITE_AGENT_BASE_URL=https://agente.ejemplo.com npm run build
```

En ese caso el agente debe permitir el origen. Sus valores por defecto son
`http://localhost:5173` y `http://127.0.0.1:5173`, y se ajustan con la variable
`AGENT_CORS_ORIGINS`.

## Endpoints usados

| Endpoint         | Metodo | Cuerpo                                  |
| ---------------- | ------ | --------------------------------------- |
| `/chat`          | POST   | `{"message": "...", "session_id": "..."}` |
| `/chat/reset`    | POST   | `{"session_id": "..."}`                |
| `/health`        | GET    | -                                       |

## Comportamiento

- El historial vive en el agente, indexado por `session_id`. El boton de nueva
  conversacion genera un identificador nuevo y llama a `/chat/reset` para
  liberar el contexto anterior.
- Cada envio cancela la peticion en vuelo mediante `AbortController`, de modo que
  nunca se cruzan dos respuestas. El boton de stop aborta la consulta.
- El agente responde con HTTP 200 incluso cuando no logra llamar al modelo, asi
  que `isAgentFailure` detecta esos casos por el texto y los pinta como error.
- Las respuestas se renderizan como Markdown con tablas GFM, que es el formato
  real que devuelve el agente.
- El tema claro/oscuro se guarda en `localStorage` y se aplica antes del primer
  pintado para evitar el parpadeo.

## Estructura

```
src/
  api/agentClient.ts        Cliente HTTP del agente
  components/
    chat/                   Composer, ChatView, MessageList, MessageBubble...
    icons/                  Iconos SVG en linea
    layout/                 AppShell, BrandBar
    markdown/               MarkdownRenderer, MarkdownTable
  data/mockData.ts          Textos de interfaz y preguntas sugeridas
  hooks/                    useChat, useTheme, useAgentHealth
  types/chat.ts             Tipos del dominio del chat
```

## Nota sobre los datos

Las cifras provienen del dataset AdventureWorks con fecha de analisis
2025-06-29. El propio agente advierte cuando esa informacion esta desactualizada.