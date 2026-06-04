# Hermes ⇄ AnythingLLM — portfolio

> **Le da a un agente de IA memoria buscable sobre todo su historial y documentos.** Conecta el
> agente **Hermes** con **AnythingLLM** para que pueda buscar —por significado, no por palabra
> clave— en sus conversaciones pasadas y en los documentos que subió.

| | |
|---|---|
| **Qué es** | Un puente entre un agente de IA y una base de conocimiento vectorial, vía MCP, para recuperación semántica sobre toda su historia. |
| **Disciplina** | IA · tooling para agentes · integraciones |
| **Rol** | Diseño e implementación del MCP server, la sincronización de sesiones y la regla de comportamiento. |
| **Stack** | Python · MCP · AnythingLLM · SQLite · embeddings/vector search |

## Cómo funciona

- **MCP server** (`anythingllm-server`): expone herramientas que el agente puede invocar para
  consultar la base de AnythingLLM — listar/buscar documentos, buscar en el historial de chat,
  info de workspace y logs de eventos.
- **Sincronización de sesiones**: cada sesión del agente se sube como documento de texto a
  AnythingLLM, donde se **vectoriza** y queda buscable por significado.
- **Regla de comportamiento**: instruye al agente a **buscar en su memoria antes de responder**
  sobre información personal, preferencias o conversaciones pasadas — así no inventa, recuerda.

## Lo interesante de ingeniería

- **Recuperación semántica sobre la historia propia del agente**: en vez de un contexto que se
  pierde al cerrar la sesión, el agente consulta una memoria persistente y la cita.
- **Integración limpia vía MCP**: el agente gana una capacidad nueva (buscar su pasado) sin
  acoplarse a la base — el server traduce entre ambos mundos.

---

> **Sobre las imágenes:** es una **integración / MCP server** sin UI propia; su "interfaz" son
> las herramientas que el agente invoca. No lleva capturas de UI.

*Arquitectura de memoria y uso: ver el [`README.md`](../../README.md) raíz.*
