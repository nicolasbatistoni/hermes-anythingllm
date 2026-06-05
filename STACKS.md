# STACKS.md — Elección de tecnologías por tipo de software (Otara / dev)

> **Documento canónico de stack para TODOS los proyectos bajo `dev/`.** Lo leen Claude Code, Codex
> y cualquier agente/contribuidor junto con `AGENTS.md`. Mientras `AGENTS.md` define **el proceso**
> (agnóstico a la tecnología), este archivo define **la tecnología**: qué lenguaje y qué stack se
> elige según el **tipo de software**, y con qué **versiones de referencia** (las que ya corren en
> los proyectos del repo, fuente de verdad real, no aspiracional).
>
> **Cómo se usa:** al arrancar un proyecto o feature nueva, primero se clasifica el **tipo de
> software** (abajo), eso fija el **lenguaje + stack por defecto**, y recién entonces se elige
> librería puntual. Desviarse del default exige una razón registrada en el PR (§ "Cómo desviarse").

---

## 0. Tabla maestra — tipo de software → lenguaje → stack

| Tipo de software | Lenguaje | Stack por defecto | Proyecto de referencia |
|---|---|---|---|
| **Sitio web estático** (landing, portfolio, institucional, marketing) | **TypeScript** | **Astro** + React (islands) + Tailwind | `otara-labs/apps/web` |
| **Sitio web dinámico** (SSR/SSG con datos, auth, panel, e-commerce) | **TypeScript** | **Next.js** (App Router) + React + Tailwind | `casa-raiz` |
| **Web app / SaaS con backend propio** (API + SPA, multi-tenant, realtime) | **JavaScript/TypeScript (Node)** | **Node** + Express + Mongoose + MongoDB + React (Vite) | `nicoq/doble-yema` |
| **Microservicio / worker / API chica** (envío de mail, impresión, jobs) | **Node** | **Node** + Express (HTTP) o proceso + libs puntuales | `otara-labs/apps/mail-api`, `fran-colarusso/riviera-worker` |
| **Videojuego / motor 3D propio** (control total, perf máxima) | **C++** | **C++20** + **Vulkan 1.3** (motor propio) | `spacesim-c` (ccosmos) |
| **Videojuego con motor (prototipo rápido / multiplataforma)** | GDScript / C++ | **Godot 4.x** *(prototipo)* · **Unreal Engine 5.x** *(AAA/Nanite-Lumen)* | `spacesim-godot`, `spacesim-ue5` |
| **Prototipo web 3D / vertical slice sin build** | **JavaScript** | **Three.js** (vanilla HTML/CSS/JS, sin build step) | `spacesim-js` |
| **IA / ML — pipeline, RAG, servicio de inferencia** (prioriza iteración) | **Python** | **Python 3.12+** + FastAPI + libs ML (torch, embeddings, vector DB) | `agents` (Brain), `claude-rag-memory` |
| **IA / robótica con presión de latencia** (tiempo real, hot path duro) | **C++** | **C++20** (Python solo el orquestador/glue) | — (criterio, ver §IA) |
| **Robótica / edge / visión en hardware chico** (RPi, microcontrolador) | **Python** o **C/C++** | Python (visión/control alto nivel) · C/C++ firmware | `rpi-self-awareness`, `arduplane-gy-87` |
| **CLI / herramienta / script / automatización** | **Python** | Python 3.12+ + Typer (CLI) · Node si el ecosistema es JS | `agents` (CLI Typer) |
| **Integración / MCP server / glue de IA** | **Python** | Python + `mcp` SDK | `hermes-anythingllm`, `claude-rag-memory` |
| **Servicios self-hosted / homelab** (media, descargas, infra) | — | **Docker Compose** (imágenes pinneadas) → GHCR + keel en RPi | `plex-rpi` |

**Regla de decisión rápida:**
1. ¿Lo ve un usuario en el navegador y **no** tiene backend propio? → **Astro** (estático).
2. ¿Web con datos/auth/SSR pero sin necesidad de un backend Node separado? → **Next.js**.
3. ¿Necesita backend propio con API + base de datos + cliente? → **Node/Express/Mongo/React**.
4. ¿Es un juego/motor donde la performance y el control mandan? → **C++/Vulkan** (motor propio); si es
   prototipo o equipo chico, **Godot/UE5**.
5. ¿Es IA/datos/robótica? → **Python** por defecto; **C++** solo si el hot path no tolera Python.
6. ¿Es una herramienta de línea de comandos o automatización? → **Python** (Typer).

---

## 1. Sitio web estático — Astro + React + Tailwind

**Cuándo:** landing, portfolio, sitio institucional/marketing, contenido mayormente estático con
algo de interactividad puntual (islands). SEO y accesibilidad al 100 como invariante.

**Stack de referencia (`otara-labs/apps/web`):**
- **Astro `^6.4`** (output con `@astrojs/node ^10` para SSR / `@astrojs/vercel ^10` para deploy).
- **React** como islands solo donde hace falta interactividad (no por default).
- **Tailwind CSS `^4.3`** vía `@tailwindcss/vite` (Tailwind v4, sin `tailwind.config` clásico).
- **TypeScript `^5`**; typecheck con **`astro check`** (`@astrojs/check ^0.9`).
- **Sitemap:** `@astrojs/sitemap ^3.7`. **Email:** `resend ^6`.
- **Tests:** **Vitest `^4`** (unit) + **`vitest-axe`** (a11y de componentes) + **Playwright `^1.60`**
  con **`@axe-core/playwright ^4.11`** (e2e: `a11y.spec.ts`, `seo.spec.ts`, `contrast.spec.ts`).
- **Lint a11y:** ESLint `^9` + `eslint-plugin-astro` + `eslint-plugin-jsx-a11y`.
- **Deploy:** Vercel (auto desde `main` + preview por PR).

## 2. Sitio web dinámico — Next.js + React + Tailwind

**Cuándo:** la web necesita SSR/SSG con datos reales, autenticación, panel de administración,
e-commerce, rutas dinámicas. App Router.

**Stack de referencia (`casa-raiz`):**
- **Next.js `16.x`** (App Router) + **React `19.x`** + **react-dom `19.x`**.
- **Tailwind CSS `^4`** (vía `@tailwindcss/postcss`).
- **Base de datos:** **MongoDB** con **Mongoose `^9`**. **Auth:** **NextAuth/Auth.js `^5`**.
- **Validación:** **Zod `^4`**. **Pagos:** Mercado Pago (`mercadopago ^3`). **Hash:** `bcryptjs`.
- **TypeScript `^5`**; lint con `eslint ^9` + `eslint-config-next`.
- **Tests:** **Vitest `^4`** (unit, con `mongodb-memory-server` para integración de DB) +
  **Playwright `^1.60`** + `@axe-core/playwright` (a11y e2e).
- **Scripts/seed:** `tsx`. **Deploy:** Vercel; contenedor Docker + manifests `k8s/` para self-host.

## 3. Web app / SaaS — Node + Express + Mongoose + MongoDB + React

**Cuándo:** producto con **backend propio** (API REST/realtime) + cliente SPA + base de datos.
Separar `apps/api` (backend) y `apps/web` (frontend) en un monorepo.

**Stack de referencia (`nicoq/doble-yema`):**
- **Backend (`apps/api`):** **Node** + **Express `^4.19`** + **Mongoose `^8`** sobre **MongoDB**.
  - Auth: `jsonwebtoken` + `cookie-parser`. Logs: `pino`. Mail: `resend`. Uploads: `multer`.
  - Integraciones según dominio (ej. `@whiskeysockets/baileys` para WhatsApp, `exceljs`, `qrcode`).
  - **Tests:** **Vitest `^2`** + **Supertest** (rutas/handlers) + `mongodb-memory-server`.
- **Frontend (`apps/web`):** **React `^18`** + **react-router-dom `^6`** + **Vite `^5`** +
  **Tailwind `^3`**.
  - **Tests:** Vitest + Testing Library + Playwright + `@axe-core/playwright` + `jest-axe` + LHCI.
- **Microservicios/workers** (`otara-labs/apps/mail-api`, `fran-colarusso/riviera-worker`): Node
  minimal — Express solo si expone HTTP; libs puntuales (`axios`, `cron`, `pg`, `escpos`) según tarea.

> **Express + Mongoose + MongoDB + React** es el default de web app. PostgreSQL (`pg`) solo cuando el
> dominio es fuertemente relacional/transaccional (caso worker de impresión sobre Postgres existente).

## 4. Videojuego / motor 3D — C++20 + Vulkan (motor propio)

**Cuándo:** se busca **control total y performance máxima**, motor propio a escala real. Es el default
para los juegos serios del repo.

**Stack de referencia (`spacesim-c` / ccosmos):**
- **C++20** (CMake `>=3.24` + **CMake Presets**), **MSVC `/utf-8`** o Clang/GCC con charset UTF-8.
- **Vulkan 1.3** (SDK aparte, provee loader + glslang) sobre un **motor propio**.
- **Dependencias vía vcpkg manifest (`vcpkg.json`):** `glfw3` (ventana/input), `glm` (matemática),
  `vk-bootstrap` (init de Vulkan), `vulkan-memory-allocator` (VMA), `imgui` (debug UI, binding glfw+
  vulkan), `stb` (carga/volcado de imágenes/capturas).
- **Tests:** **Catch2** (unit + integración) vía CTest. **Shaders:** GLSL → SPIR-V como gate de build.

**Alternativas con motor (prototipo / equipo chico / multiplataforma):**
- **Godot `4.x`** (GDScript) — iteración rápida, export a Steam (`spacesim-godot`, Godot 4.6).
- **Unreal Engine `5.x`** (C++ + Blueprints, Nanite/Lumen) — AAA / geometría masiva (`spacesim-ue5`,
  UE 5.7).
- **Three.js** (vanilla JS, sin build) — prototipo web / vertical slice jugable en navegador
  (`spacesim-js`).

> Regla: **motor propio C++/Vulkan** cuando el proyecto **es** el motor y la perf es el norte; **motor
> existente** (Godot/UE5) cuando lo que importa es el juego y la velocidad de iteración.

## 5. IA / ML / robótica — Python (default) o C++ (si la velocidad manda)

**Decisión Python vs C++:**
- **Python 3.12+** por **default** para IA/ML/datos: prioriza velocidad de iteración, ecosistema
  (torch, transformers, vector DBs) y glue. Es lo correcto salvo que el hot path no lo tolere.
- **C++20** cuando hay **presión dura de latencia / tiempo real** (control de robot en el loop,
  inferencia en hot path, sin headroom para el overhead de Python). Patrón típico: **núcleo C++ +
  orquestación Python**.

**Stack de referencia IA/ML (`agents` — Brain · `claude-rag-memory`):**
- **Python `>=3.12`**, packaging con **hatchling** (+ PyInstaller para binario distribuible).
- **API/servicio:** **FastAPI `^0.115`** + **uvicorn**; UI desktop opcional con `pywebview`.
- **ML:** **torch `^2.4`**, embeddings (**BGE-M3** vía `FlagEmbedding`, `sentence-transformers`),
  **vector DB** (**Qdrant** embebido / **ChromaDB**), LLM (`openai`/`anthropic`, Ollama/LM Studio).
- **CLI:** **Typer**. **Config/logs:** `pyyaml`, `structlog`. **MCP:** SDK `mcp[cli]`.
- **Tests:** **pytest** (+ `pytest-asyncio`, `pytest-bdd`, `pytest-benchmark`, `pytest-cov`).
  **Lint/format:** **ruff**.

**Stack de referencia robótica / edge (`rpi-self-awareness` — ARIA · `arduplane-gy-87`):**
- **Python** para visión y control de alto nivel en hardware chico (RPi): `opencv-python-headless`,
  `tflite-runtime` (inferencia liviana), `psutil`, `anthropic` (razonamiento opcional vía API).
- **C/C++** para firmware / flight controller (ej. **ArduPlane** en RPi como FC con GY-87): config de
  hardware (`hwdef`), sin Python en el loop de control.

## 6. Infra, deploy y empaquetado (transversal)

- **Web** → **Vercel** (auto-deploy desde `main` + preview por PR).
- **Servicios internos / homelab (RPi)** → imágenes **GHCR** versionadas (`:vX.Y.Z` / `:sha-…`) +
  **keel** para auto-update; orquestación con **Docker Compose** (imágenes pinneadas, no `latest`).
- **Kubernetes** (`k8s/`) solo cuando un servicio lo justifica (caso `casa-raiz` self-host).
- **Artefacto inmutable por SHA** (build-once), promovido por entornos sin rebuild (ver `AGENTS.md §1.bis`).

---

## Cómo desviarse del default

El default de la tabla §0 se respeta salvo razón explícita **registrada en el PR**. Antes de elegir un
stack distinto o sumar una tecnología nueva, subir la escalera de `AGENTS.md §3.ter` (reusar lo que ya
está en el repo antes que sumar). Una desviación válida documenta: (1) por qué el default no sirve para
este caso, (2) qué se elige en su lugar, (3) el costo permanente que asume (mantenimiento, peso,
superficie de seguridad). Cada tecnología nueva es un compromiso, no un atajo.

## Mantenimiento de este archivo

- Las **versiones** de este doc son las que **realmente corren** en los proyectos de referencia: cuando
  un proyecto sube una versión mayor, actualizar acá (este archivo sigue a la realidad del repo, no al
  revés).
- Al incorporar un **tipo de software nuevo** que no esté en la tabla §0, agregar su fila con
  lenguaje + stack + proyecto de referencia en el mismo PR que lo introduce.
- Mantener alineado con `AGENTS.md` (proceso) — este doc **no** repite reglas de proceso; solo elección
  de tecnología.
