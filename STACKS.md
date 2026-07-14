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
| **Videojuego / motor 3D propio** (control total, perf máxima) | **C++** | **C++20** + **Vulkan 1.3** (motor propio) | `spacesim-c` |
| **Videojuego con motor (prototipo rápido / multiplataforma)** | GDScript / C++ | **Godot 4.x** *(prototipo 2D/3D)* · **Unreal Engine 5.x** *(AAA/Nanite-Lumen)* | `spacesim-godot` (4.6), `gangsters`/`spacesim-pixelart-godot`, `procedural-space-sim` (UE 5.7) |
| **Juego mobile hyper-casual (Android, monetizado con ads)** | GDScript | **Godot 4.7** (GL Compatibility) + export Android/gradle + **AdMob** (plugin) + **GameAnalytics** + firma keystore + publish Play API | `godot-games/games/*` mobile (ver §4.mobile) |
| **Juego desktop premium (Steam, Linux+Windows)** | GDScript | **Godot 4.7** (GL Compatibility 2D / Forward+ 3D) + export headless Linux/Windows + **SteamPipe** (steamcmd) + GodotSteam solo on-demand | `godot-games/games/*` Steam (ver §4.desktop-steam) |
| **Prototipo web 3D / vertical slice sin build** | **JavaScript** | **Three.js** (vanilla HTML/CSS/JS, sin build step) | `spacesim-js` |
| **Port experimental / lenguaje de sistemas emergente** (MVP CLI, determinismo, sin GC) | **Odin** | **Odin** (compilador + `odin test`); secundario, no default | `spacesim-odin` |
| **Editor / cockpit local sobre un pipeline IA/ML** (UI de autoría/curación/orquestación; viewport 3D) | **Python + TypeScript** | **FastAPI** (in-process sobre el pipeline) + **React/Vite/Tailwind** (+ react-three-fiber); opcional pywebview desktop | `ai-asset-pipeline/editor` |
| **Audio / SFX procedural** (síntesis físicamente-fundada, DSP — sin pesos, license-clean) | **Python** | **Python 3.12+** + numpy (síntesis modal) + soundfile (WAV 24-bit/OGG) + pyloudnorm (LUFS ITU-R BS.1770) | `ai-asset-pipeline` (dominio audio) |
| **App mobile** (híbrida/nativa multiplataforma) | **TypeScript** | **Expo (React Native)** + Expo Router/React Navigation + TanStack Query + tokens propios/StyleSheet (sin NativeWind) + auth Bearer en SecureStore; e2e por `expo export --platform web` + Playwright. `tempi-ionic` (Ionic v1/Cordova) es **legacy** | `otara-labs/apps/queze-mobile`, `fran-colarusso/riviera/driver-app` |
| **App desktop** (ventana nativa sobre web) | **TS/JS** | **Sin default consolidado vigente** — al necesitarlo, elegir y registrar (Tauri / Electron actual); `tuitpic`, `chequer-electron` (Electron 1.3) son **legacy** | `tuitpic`, `chequer-electron` (legacy) |
| **IA / ML — pipeline, RAG, servicio de inferencia** (prioriza iteración) | **Python** | **Python 3.12+** + FastAPI + libs ML (torch, embeddings, vector DB) | `agents` (Brain), `claude-rag-memory` |
| **IA / robótica con presión de latencia** (tiempo real, hot path duro) | **C++** | **C++20** (Python solo el orquestador/glue) | — (criterio, ver §IA) |
| **Robótica / edge / visión en hardware chico** (RPi, microcontrolador) | **Python** o **C/C++** | Python (visión/control alto nivel) · C/C++ firmware | `rpi-self-awareness`, `arduplane-gy-87` |
| **CLI / herramienta / script / automatización** | **Python** | Python 3.12+ + Typer (CLI) · Node si el ecosistema es JS | `agents` (CLI Typer) |
| **Integración / MCP server / glue de IA** | **Python** | Python + `mcp` SDK | `hermes-anythingllm`, `claude-rag-memory` |
| **Servicios self-hosted / homelab** (infra, edge en RPi) | — | **k3s** (imágenes pinneadas `:X.Y.Z`) → **GitOps repo-de-entorno + Flux** (pin de versión por app en el repo de entorno; rollback = `git revert`) | `otara-infra` (cluster), `nicoq` (k3s RPi) |

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
  - **Componentes:** **shadcn/ui** (Radix + Tailwind, copiado al repo vía `components.json`) como sistema
    de componentes accesible por default; **TanStack Query** para estado de servidor. Package manager:
    **npm** por default, **Bun** aceptado cuando el repo ya lo usa (`bun.lockb`) — uno solo por repo.
  - **Tests:** Vitest + Testing Library + Playwright + `@axe-core/playwright` + `jest-axe` + LHCI.
- **Microservicios/workers** (`otara-labs/apps/mail-api`, `fran-colarusso/riviera/worker`): Node
  minimal — Express solo si expone HTTP; libs puntuales (`axios`, `cron`, `pg`, `escpos`) según tarea.

> **Express + Mongoose + MongoDB + React** es el default de web app. PostgreSQL (`pg`) solo cuando el
> dominio es fuertemente relacional/transaccional (caso worker de impresión sobre Postgres existente).

> **Starters generados por IA (p. ej. Lovable):** son un punto de partida (`link-board`,
> `pentest-canvas-hub`, `otara-labs-offensive-security-expertise`), no un entregable. Antes de
> considerarlos hechos hay que **subirlos a las disciplinas** (tests TDD+e2e, a11y como gate, CI/CD
> portable) — el código generado no exime de `AGENTS.md §3`.

> **Backends heredados / de cliente / de práctica** (no greenfield default): **Java + Spring Boot +
> Maven** (`msf`) y **Ruby on Rails** (`fran-colarusso/riviera`) aparecen por herencia o contexto de
> cliente. No se eligen para algo nuevo salvo razón registrada en el PR; se mantienen con la misma
> disciplina de proceso que el resto.

## 4. Videojuego / motor 3D — C++20 + Vulkan (motor propio)

**Cuándo:** se busca **control total y performance máxima**, motor propio a escala real. Es el default
para los juegos serios del repo.

**Stack de referencia (`spacesim-c`):**
- **C++20** (CMake `>=3.24` + **CMake Presets**), **MSVC `/utf-8`** o Clang/GCC con charset UTF-8.
- **Vulkan 1.3** (SDK aparte, provee loader + glslang) sobre un **motor propio**.
- **Dependencias vía vcpkg manifest (`vcpkg.json`):** `glfw3` (ventana/input), `glm` (matemática),
  `vk-bootstrap` (init de Vulkan), `vulkan-memory-allocator` (VMA), `imgui` (debug UI, binding glfw+
  vulkan), `stb` (carga/volcado de imágenes/capturas).
- **Tests:** **Catch2** (unit + integración) vía CTest. **Shaders:** GLSL → SPIR-V como gate de build.

**Alternativas con motor (prototipo / equipo chico / multiplataforma):**
- **Godot `4.x`** (GDScript) — iteración rápida, export a Steam. 3D (`spacesim-godot`, Godot 4.6),
  2D/pixelart en modo GL Compatibility (`spacesim-pixelart-godot`) y juego con assets Blender
  (`gangsters`, Godot 4.7).
- **Unreal Engine `5.x`** (C++ + Blueprints, Nanite/Lumen) — AAA / geometría masiva
  (`procedural-space-sim`, UE 5.7).
- **Three.js** (vanilla JS, sin build) — prototipo web / vertical slice jugable en navegador
  (`spacesim-js`).
- **Odin** (compilado, sin GC) — port experimental / MVP de consola determinístico (`spacesim-odin`):
  el valor está en el modelo procedural verificable, no en el renderer. Secundario, no default.

> Regla: **motor propio C++/Vulkan** cuando el proyecto **es** el motor y la perf es el norte; **motor
> existente** (Godot/UE5) cuando lo que importa es el juego y la velocidad de iteración; **Three.js/Odin**
> para prototipos/ports experimentales del mismo modelo en otro stack.

### §4.mobile — Juego mobile hyper-casual (Android, monetizado con ads)

**Cuándo:** juego casual/hyper-casual de sesión corta (<2 min) para **Google Play**, monetizado con
**ads** (foco: generar ingreso vía volumen + retención). No es un stack nuevo: es el default de juego
(**Godot 4.x**, fila §0) aplicado a mobile, con el toolchain de deploy/monetización que abajo se fija.
Las deps externas se **justifican en el PR que las integra** (`AGENTS.md §3.ter`).

**Stack de deploy/monetización de referencia (programa `godot-games/games/*` mobile):**
- **Motor:** **Godot 4.7** con renderer **GL Compatibility** (`rendering_method.mobile="gl_compatibility"`),
  input táctil, portrait/landscape según juego. Plantilla de proyecto: `games/spacesim-pixelart`.
- **Export Android:** `godot --headless --import` (cachea `class_name`) → `--export-release "Android" out.aab`,
  con **Android build template custom (gradle)**, **JDK 17**, **Android SDK/cmdline-tools** + **export
  templates 4.7** + `bundletool`. AAB (Play requiere bundle), ETC2/ASTC on.
- **Ads:** **AdMob** vía plugin **`poingstudios/godot-admob-plugin`** (Godot 4.2+, GDScript, Android;
  banner/interstitial/rewarded; editor mock ads). Se accede detrás del puerto `IAdService`
  (`packages/mobile-services`) — el dominio del juego no importa el SDK.
- **Analytics:** **GameAnalytics** (SDK Godot oficial `GA-SDK-GODOT`, GDExtension) para retención/DAU/
  ARPDAU, detrás del puerto `IAnalytics` (swappable a Firebase sin tocar dominio). Ingreso/eCPM también
  desde la consola de AdMob.
- **Firma + publish:** keystore de release (via env/secrets, **nunca** committeado en `export_presets.cfg`)
  + **Play Developer API** (`fastlane supply`) para subir a track internal → producción desde CI.
- **Arquitectura:** hexagonal `src/{domain,application,adapters}` + puertos mobile compartidos en
  `packages/mobile-services` (`IAdService`/`IAnalytics`/`IConsent`/`ITouchInput`, con adapters Godot y
  **fakes** para test headless y dev de escritorio) + Atomic Design de UI sobre `packages/ui-kit`.
- **CI/CD:** todo dockerizado — imagen `ci/Dockerfile.godot-android` (base cicd-toolkit + Godot + Android
  toolchain), stages `build`/`publish` en `cicd`, versionado SemVer automático por Conventional Commits
  con tag scoped `<juego>-vX.Y.Z`.

> **iOS:** fuera de alcance mientras el dev sea Linux (requiere Mac/Xcode). El puerto `IAdService`/plugin
> AdMob soportan iOS, así que portar es sumar el target, no rediseñar.

### §4.desktop-steam — Juego desktop premium (Steam, Linux + Windows)

**Cuándo:** juego premium (pago único, USD 3–10) para **Steam**, PC (foco: generar ingreso por venta;
Steam **prohíbe** modelos basados en ads). No es un stack nuevo: es el default de juego (**Godot 4.x**,
fila §0) aplicado a desktop, con el toolchain de export/publicación que abajo se fija. Programa:
`godot-games/docs/design/steam/`.

**Stack de deploy/publicación de referencia (programa `godot-games/games/*` Steam):**
- **Motor:** **Godot 4.7** binario **simple** (precisión doble solo si el dominio la exige, cf.
  spacesim-3d). Renderer: **GL Compatibility** para 2D/pixel (máxima compatibilidad GPUs
  viejas/Proton/Steam Deck); **Forward+** solo para 3D con efectos.
- **Export desktop:** headless desde CI — `godot --headless --import` → `--export-release "Linux"` +
  `--export-release "Windows"` con export templates 4.7. **PCK separado** (no embed: deltas mínimos de
  SteamPipe). Preset Windows con `application/modify_resources=false` (evita rcedit/wine en el export
  cross desde Linux; icono custom del `.exe` = deuda declarada hasta que duela).
- **Publicación:** **SteamPipe** (`steamcmd` en la imagen CI) con VDFs parametrizados por env
  (`STEAM_APP_ID`, depot por OS) — subida automática al branch **`beta`** de Steam en cada release tag;
  promoción a `default` **manual** en Steamworks (gate forzado por Valve, 2FA web). Canal paralelo:
  zips por OS + `SHA256SUMS` en el GitHub Release (build-once; alimentan playtests y la venta directa).
- **SDK de Steam:** **ninguno en el MVP** (YAGNI — un premium sin achievements no lo necesita; Steam
  Cloud vía Auto-Cloud, config web, cero código). Cuando una feature lo exija: **GodotSteam**
  (GDExtension) detrás de puertos en `packages/steam-services` (patrón `mobile-services`: puertos +
  fakes; adapter real en `packages/godot-adapters`; factory con degradación segura sin Steam corriendo).
- **Arquitectura:** hexagonal `src/{domain,application,adapters}` + `packages/*` (det-rng, ui-kit,
  settings + `SettingsApplier` para window/volumen, input de teclado/gamepad) + Atomic Design.
- **CI/CD:** imagen `ci/Dockerfile.godot-desktop` (base cicd-toolkit + Godot + export templates +
  steamcmd), `release.artifact: binary` multi-preset con checksums, SemVer automático con tag scoped
  `<juego>-vX.Y.Z`.

> **macOS:** fuera de alcance (exige firma/notarización con Mac). Linux+Windows cubren Steam y Steam
> Deck (Proton); sumar macOS es agregar un preset + firma, no rediseñar.

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
- **Servicios internos / homelab (k3s)** → imágenes **GHCR** versionadas (`:X.Y.Z` + `:sha-…` para
  trazabilidad; **`:latest` no es disparador de deploy**) desplegadas por **GitOps repo-de-entorno**: los
  manifests/chart viven en el **repo del producto**; un **repo de entorno** (p.ej. `otara-infra` para el
  cluster de producción) declara el **pin de versión por app**, que es la **fuente de verdad del estado
  desplegado** (`AGENTS.md §6`).
- **El pipeline de CI NO se escribe: lo GENERA el motor** (`cicd render-pipeline`) desde el `cicd.yml`.
  Woodpecker no tiene include remoto, así que cada repo necesita su `.woodpecker.yml` físico — la respuesta
  no es herencia, es **generación**. Los dos datos genuinos de cada repo (`paths` = allowlist de disparo,
  `images.ci` = imagen del step) van al `cicd.yml`; el resto lo pone el motor. El gate
  `cicd render-pipeline --check` corre en el step `security` y **rompe el CI** si alguien edita el
  `.woodpecker.yml` a mano.
- **El motor `cicd-toolkit` es multi-build y multi-deploy** (no CI-only ni k8s-only). **Build:** artefacto
  `release.artifact: none|binary|godot_desktop|android` (binario genérico · export Godot desktop · AAB a
  Play), despachado por el puerto `artifact` (sumar iOS/Steam/Flatpak = un adaptador nuevo, no otra rama de
  un `case`) **+** **imagen OCI** vía la sección `deploy` (engine `docker` **o** `podman` rootless). Ojo:
  **la imagen OCI NO es un valor de `release.artifact`** — es otro ciclo de vida (build-once + scan + push)
  y vive en `deploy`. **Deploy
  (`reconcile.kind`):** **k8s/k3s** (`kubectl apply`) · **docker compose** (`compose up -d`) · **un
  contenedor** `docker run` (`kind: docker`). El **target elige el mecanismo**: k8s → **GitOps
  repo-de-entorno + Flux** (abajo, preferido); docker/compose (host sin k8s, p. ej. RPi) → `cicd reconcile`
  **pull en el host**.
- **Modelo de CD — repo-de-entorno + Flux** (para el target **k8s**; reemplaza el agente pull en el host
  para k8s, el polling de registry y keel):
  - **Ownership.** El **repo de producto** es dueño de su **set de manifests/chart** (Deployment/
    StatefulSet, Service, HTTPRoute, PVC, ConfigMap, Secret refs, ServiceAccount/RBAC, NetworkPolicy
    *allow-rules de la app*, PodDisruptionBudget, HPA, migrations/Jobs, config por entorno). El **repo de
    entorno** es dueño solo de la **plataforma compartida** (ingress/Gateway, cert-manager, DNS, Flux,
    namespaces + baseline **default-deny NetworkPolicy**/quota/limits, SOPS, IaC compartida) **+ el pin de
    versión** por app en `clusters/<env>/apps/<app>.yaml` (Flux `GitRepository` → repo de la app +
    `Kustomization`/`HelmRelease` pineado a tag, reconciliado tras la plataforma).
  - **IaC compartido vs app-exclusivo (regla lifecycle).** La frontera del IaC (Terraform/Pulumi/etc.) la
    fija el **ciclo de vida**, no la conveniencia: *ciclo de vida = del cluster/plataforma → **repo de
    entorno*** (VPS, cluster, **zona DNS completa**, IAM/firewall globales, storage compartido, state
    remoto); *ciclo de vida = de la app → **repo de la app*** (bucket exclusivo, cola, DB administrada
    exclusiva, secret en Vault, cloud SA, **registro DNS excepcional** de esa app), como módulo propio o
    consumido por ella. Una app **nunca** toca zona DNS completa / firewall / IAM global / cluster: si lo
    necesita, lo pide a la plataforma. El IaC exclusivo se despliega **tras** el compartido (el cluster
    existe antes que el bucket de una app). (En `otara-infra` hoy `terraform/**` está 100% compartido; la
    regla define **dónde vivirá** el IaC exclusivo cuando aparezca, no obliga a mover nada existente.)
  1. `main` en verde del repo de app publica el artefacto inmutable y, si corta versión, la **release +
     imagen `:X.Y.Z`** (`AGENTS.md §1, §1.bis`).
  2. El stage **`promote`** del pipeline (motor `cicd-toolkit`) abre un **PR al repo de entorno**
     bumpeando el **pin de versión** de esa app — **no re-buildea: pinea el artefacto ya testeado**
     (build-once). **Release ≠ deploy**: el bump es auditable y revisable.
  3. **Flux** (GitOps in-cluster) detecta el commit del bump y **reconcilia** el cluster contra lo
     declarado. **El cluster tira**; **CI nunca empuja al cluster** ni tiene credenciales (mínimo
     privilegio, `AGENTS.md §1.bis`).
  - **Sin anti-loop especial:** el bump cae en el **repo de entorno** (sin pipeline de build de la app),
    así que no re-dispara CI ni re-buildea — la separación de repos elimina el loop por construcción.
  - **Rollback = `git revert` del PR de bump** en el repo de entorno: Flux reconcilia a la versión
    previa; **no se mueve ni reescribe un tag** (`AGENTS.md §6`).
  - **Excepción documentada:** un **servicio de plataforma upstream sin repo-producto propio** (p.ej.
    **Woodpecker**) queda **vendored** en el repo de entorno (`apps/<svc>/`); no aplica el repo-de-app.
  - **Setup (una vez):** `flux bootstrap` + secret de decrypt (SOPS/age) in-cluster + **auth GHCR
    in-cluster** (`imagePullSecret` / `registries.yaml` de k3s); detalle por cluster en el repo de entorno.
  - **Retirados (para k8s):** el **agente pull en el host** para k8s (`cicd reconcile` k8s +
    agente Woodpecker-en-host), **keel** (poller de GHCR) y el CronJob casero `auto-deploy` — para k8s,
    Flux es el motor de reconcile único. (`cicd reconcile` **sigue vigente** para targets **docker/
    compose** sin k8s, p. ej. un contenedor o un compose en un host chico.)
- **Kubernetes** (`k8s/`) solo cuando un servicio lo justifica (caso `casa-raiz` self-host). En homelab,
  **k3s** (incl. RPi ARM) con **build multi-arch** (`linux/arm/v7` + `linux/amd64`); el reconcile lo hace
  **Flux** y las notificaciones van a **Telegram** (`nicoq`, `otara-labs`).
- **Compose** queda solo como **borde de transición** durante una migración a k8s (no como destino con
  agente pull); el estado objetivo self-hosted es **k3s + Flux**.
- **AWS CodeDeploy** (`appspec.yml` + scripts `hooks` de deploy) donde el destino es EC2/on-prem en vez
  de Vercel/k8s (cluster `codedeploy-test*`, experimental).
- **Artefacto inmutable por SHA** (build-once), promovido por entornos sin rebuild; la promoción entre
  entornos es un **bump del pin de versión en git**, no un build nuevo (`AGENTS.md §1.bis`).

## 7. Dominios particulares y stacks legacy

**Offensive-security / pentest (dominio, no stack nuevo):** los productos de pentesting (`offsec`,
`pentest-canvas-hub`, `otara-labs-offensive-security-expertise`) mapean al **web app default**
(Node/Express/Mongo + React/Vite, o el motor en **Python + FastAPI + Typer**) más **libs puntuales de
dominio** (`shodan`, `weasyprint` para reportes PDF, `jinja2`). No es un stack aparte: es el default +
libs según tarea, con el mismo proceso y privacidad de material público (`AGENTS.md §6`).

**Stacks legacy (congelados — no elegir para algo nuevo).** Existen en repos `archivado`/`legacy`
(`AGENTS.md §6`); se documentan para reconocerlos, **no** para reusarlos:

| Stack legacy | Repo(s) | Reemplazo moderno (para algo nuevo) |
|---|---|---|
| AngularJS + Grunt + Bower + Karma/Jasmine | `chequer-front`, `tempi` (front) | React/Vite (§3) |
| LoopBack 2.x + socket.io | `chequer-back` | Node + Express + Mongoose (§3) |
| Jade/Pug + Express server-rendered | `codedeploy-test-backend` | Next.js (§2) o API + SPA (§3) |
| Create React App / react-scripts | `codedeploy-test-frontend` | Vite (§3) |
| Ionic v1 + Cordova + Gulp | `tempi-ionic` | mobile a decidir (§0, fila mobile) |
| Electron 1.3 + electron-packager | `tuitpic`, `chequer-electron` | desktop a decidir (§0, fila desktop) |

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
