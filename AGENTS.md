# AGENTS.md — Reglas de proceso (agnósticas a la tecnología)

> **Documento canónico de proceso para TODOS los proyectos bajo `dev/`.** Lo leen Claude Code, Codex
> y cualquier agente/contribuidor. Estas reglas **override** el comportamiento por defecto de cualquier
> agente. Son **agnósticas al stack**: aplican igual a un motor C++/Vulkan, una web React/Next, un
> backend Go, un firmware embebido o un notebook de datos. Cada proyecto puede tener su propio
> `AGENTS.md` que **concreta** estas reglas a su tecnología y dominio; ante conflicto, el del proyecto
> manda sobre éste **solo** en lo específico (nunca para relajar una disciplina de verificación).
>
> Donde abajo se dice "test", "build", "linter", "framework de test", "runtime", "módulo", etc., se
> entiende **el equivalente del stack del proyecto** (p. ej. test = Catch2/Jest/pytest/go test; build =
> CMake/Vite/cargo/gradle; linter = clang-tidy/eslint/ruff). La **disciplina** es la misma; la
> **herramienta** la define el proyecto.

## 0. Idioma — al usuario, en su idioma (español)

Toda respuesta, resumen, mensaje de progreso, título/cuerpo de PR, mensaje de commit y nota va **en
español**. Quedan en inglés (datos crudos / ya versionados): identificadores y símbolos, comentarios y
logs dentro del código, archivos ya en inglés, nombres de ramas (kebab-case), comandos/paths/hex/
ranges/exit-codes.

## 0.0 Co-diseño + co-confirmación con un segundo modelo — uno codea, los dos piensan/confirman

> **Ni un agente solo: dos.** Un segundo modelo (p. ej. Codex/otro asistente con visión) caza/confirma
> cosas que el primero no ve; el primero implementa/mide lo que el segundo no puede.

- **Un solo agente escribe el código.** El otro es copiloto de pensamiento y de ojos (no toca el árbol).
- **Diseño / root-cause no trivial EN PAREJA**: antes de implementar una solución no trivial (root-cause
  de bug, decisión de arquitectura, approach de feature, elección entre fixes), consultar al segundo
  modelo y reconciliar las dos lecturas. No avanzar con un diseño que razonó uno solo.
- **Confirmación de salida EN PAREJA**: toda evaluación de un artefacto perceptible (¿se ve bien una
  captura? ¿es correcto un output? ¿pasa el criterio?) pasa **también** por el segundo modelo —no
  confiar solo en la lectura del primero. Prompt neutral, sin sesgar.
- **Qué NO requiere segundo modelo**: cambios triviales (typo, rename, bump con criterio claro) y el
  acto de tipear. El **diseño** del cambio y la **confirmación** del resultado, sí.
- **Si el segundo modelo no responde (rate limit, error, timeout, caída), NO bloquees**: hacé vos la
  revisión de diseño + la confirmación con tu propio criterio y **continuá** (incluido el merge). Es un
  refuerzo, no un gate duro. Dejá declarado en el CHANGELOG que la co-confirmación quedó pendiente y por
  qué, y reintentá más tarde si el motivo es temporal.

## 0.bis Norte del proyecto — todo tiene un motivo, todo se filtra por el norte

> **⚖ Desempate supremo:** ante CUALQUIER duda, gana la opción **más correcta, más rigurosa y de mayor
> calidad** (verificada contra la realidad/los datos/las referencias, no contra la intuición), por
> encima de conveniencia, simplicidad de implementación o gusto. Si dudás entre dos caminos, elegí el
> que mejor sirva al **norte documentado del proyecto**. Este criterio override cualquier otra
> preferencia cuando entran en conflicto.

Cada proyecto define su **norte** en un documento (típicamente `GOAL.md`): la pregunta-filtro y el loop
mínimo. Se lee antes de cada iteración. Toda feature responde primero **"¿por qué existe esto en el
sistema?"** antes que "¿es conveniente?": si una mecánica/feature no se funda en una causa real del
dominio, **no entra**. Nada scripteado "para el usuario" cuando el sistema puede producirlo causalmente.

Donde un proyecto tenga además un **doc de arquitectura/diseño** (p. ej. `docs/design/…`: bounded
contexts, fronteras, dirección de dependencias, invariantes), se lee **junto al norte** antes de cada
iteración y **todo cambio se filtra también por él**: cumple el norte **Y** respeta la arquitectura
vigente. Un cambio que necesite desviarse de la arquitectura **modifica primero el doc** (con la
evidencia), no la viola en silencio (cf. §2.B SADD, §6).

## 0.ter Sin ceremonia pesada para features chicas/medianas

No invocar flujos formales pesados (brainstorm→spec→plan→N-subagentes) para features chicas o medianas:
la ceremonia no se justifica. **Workflow correcto:** conversación directa de diseño → branch + impl +
tests + commit + PR + merge. Spec/plan formal **solo** si el cambio tiene complejidad arquitectónica
genuina y el usuario lo pide. Las utilidades livianas del entorno (no las ceremonias) sí están permitidas.

## 0.quater Elección de stack — guiarse por `STACKS.md`

La **elección de lenguaje y tecnologías** no se improvisa: se decide según **`STACKS.md`** (documento
hermano de éste, fuente canónica de stack para todos los proyectos bajo `dev/`). Antes de arrancar un
proyecto, un módulo nuevo o sumar una tecnología: (1) clasificá el **tipo de software** (sitio estático,
web dinámica, web app con backend, videojuego/motor, IA/ML, robótica/edge, CLI, microservicio, etc.);
(2) eso fija el **lenguaje + stack por defecto** de la tabla maestra de `STACKS.md` (con las **versiones
de referencia** que ya corren en el repo); (3) recién entonces elegís librería puntual, subiendo antes
la escalera de `§3.ter` (reusar lo que ya está antes que sumar). **Desviarse del default exige razón
registrada en el PR** (por qué el default no sirve, qué se elige, qué costo permanente se asume). Mientras
`AGENTS.md` define **el proceso** (agnóstico a la tecnología), `STACKS.md` define **la tecnología**.

## 1. Trunk-based — nunca push directo a la rama principal

`main` (o la rama principal) es el trunk. Todo cambio (hasta una línea) va por **branch corta off
`main` + PR + merge** — nunca commit/push directo a `main`, nunca editar `main` local. Arrancá siempre
desde trunk actualizado (`git checkout main && git pull`) antes de crear la branch. "Corta" = minutos a
pocas horas; si una branch se acerca a un día sin mergear, está muy grande (partila) o estancada
(mergeá un parcial). Una PR = una unidad lógica (no mezclar feature + refactor, bugfix + reformateo, ni
migración + cambio visual: cada uno su PR). **Nada de ramas largas paralelas** (`develop`,
`release/*`, `staging`, `qa`, `hotfix/*`): solo trunk + ramas cortas (un hotfix es una rama `fix-…`
corta más, §6).

Nombres de rama describen **scope, no actor**: `feat-…`, `fix-…`, `chore-…`, `docs-…`. Evitar nombres
con el actor o con fecha.

El agente aprueba y mergea (squash + delete branch) una vez que pasan los gates de §3. El usuario NO
gatea cada merge — la forma de la PR + verificación + diff limpio son el gate. El usuario gatea solo si
lo pide o si el cambio es high-risk (arquitectónico, schema/API-breaking, refactor grande). **El merge lo
hace siempre el agente, nunca lo deja para el usuario:** una PR abierta con CI en verde esperando solo
que un humano apriete "merge" es trabajo sin terminar, no un entregable. **Esto incluye las PRs de
release: versionar y publicar es 100% automático** (el pipeline corta tag + GitHub Release por
Conventional Commits, sin gate humano ni tag a mano; detalle §1.bis/§6). Aplica a **todos los repos**
(`dev/` y portfolio): cada uno corre el mismo motor de CI/CD portable.

**Flujo production-ready (esencial):** `main` = "próxima versión publicable", no "lo último que codeé" →
siempre compila/construye, pasa tests y arranca limpio. **PR chico** (revisable en 10–20 min,
idealmente < ~300–500 líneas; si no, partilo). **Squash merge** (un commit limpio por PR, fácil de
revertir). **Feature flags** para lo incompleto (entra a `main` apagado por default; cada flag con dueño
+ fecha/condición de borrado — §3.ter). **Branch by abstraction** para refactors grandes (no ramas
largas: abstracción → impl vieja detrás → impl nueva en paralelo → switch por flag → borrar la vieja).
**Backward-compatibility de datos/estado/saves** (expand/contract; nunca romper un dato persistido
existente — §6). **Rollback**: flag off > build anterior > revert. **Tags + releases** (detalle en
§1.bis y §6): toda versión distribuida lleva un **annotated tag** SemVer `v` que **corta el pipeline, no
la máquina del dev**; los `v*` son **inmutables** (release mala → nueva PATCH, no se mueve el tag).
**Progressive delivery** donde haya servicio/usuarios
(internos → 1 % → 5 % → 25 % → 50 % → 100 % con métricas de error/latencia/KPIs en cada paso). Seguir las
**métricas de flujo (DORA + salud):** lead time for changes, deployment frequency, change failure rate,
MTTR, tiempo de PR abierto, tiempo de CI, flags vencidas, rollbacks.

## 1.bis Entrega: build-once, previews y CI con mínimo privilegio

- **Build-once / artefacto inmutable por SHA.** Cada commit produce un artefacto inmutable
  identificado por su SHA; el **mismo artefacto ya testeado** se promueve por los entornos — no se
  re-buildea por entorno ni a mano.
- **Preview / entorno efímero por PR** cuando el stack lo permita: la PR se revisa contra algo
  **corriendo**, no solo contra el diff.
- **CI con permiso mínimo por job** (solo los scopes que necesita: leer código, escribir la PR,
  publicar el paquete, OIDC) y **producción protegida** (entorno con required reviewers / OIDC /
  secrets por entorno). Los **tags/releases productivos los crea el pipeline**, no la máquina del dev
  (§1).
- **CI/CD homogéneo, definido una sola vez (DRY).** La lógica de CI/CD vive **una sola vez** en el motor
  portable `nicolasbatistoni/ci-toolkit` (scripts bash; su README es la fuente). Cada repo declara solo
  sus parámetros en `cicd.yml` (raíz) y lleva un **adaptador fino** por herramienta de CI
  (`.woodpecker.yml` primario) que solo invoca `cicd <stage>`. Un único comando hace todo el CI/CD —
  `cicd all` (CI + CD, componibles con `--no-ci`/`--no-cd`)— y corre igual local, en Woodpecker o en
  cualquier CI. El versionado es automático por Conventional Commits sobre **git tags** (sin
  release-please ni gate humano). Para cambiar de herramienta de CI se reescribe **solo** el adaptador;
  los scripts (`lib/`, `steps/`) no se tocan.
- **Promoción declarativa por commit (GitOps de manual), no rebuild.** El CD promueve por **bump de
  definiciones en git**, no por rebuild: `main` en verde publica la imagen **inmutable** `…X.Y.Z`; el
  stage **`promote`** reescribe el pin `image:` de `infra/**` a `:X.Y.Z` y commitea el bump; ese commit
  **dispara el reconcile en el host** vía **agente pull** (el host tira; CI no empuja ni tiene
  credenciales del cluster) — **sin poller de registry**. Definiciones **por-repo** en `infra/`. Detalle,
  anti-loop y setup del host: `STACKS.md §6`.
- **Objetivo de tiempos de CI:** feedback de PR ~5–10 min, pipeline de `main` ~10–20 min; si se pasa,
  paralelizar o partir.

## 1.ter Monorepo — cuándo, y cómo no romper el trunk

Un repo puede contener **varios paquetes/apps/productos** (`apps/*`, `services/*`, `packages/*`). Se elige
**monorepo** cuando comparten tooling, disciplina y ciclo de vida y conviene atomicidad de cambios
cross-package; se eligen **repos separados** cuando los ciclos de release, los dueños o los dominios son
independientes. La elección de **estructura física** (qué tecnología/layout) la fija `STACKS.md`; estas
son las reglas de **proceso**, que no cambian:

- **Todo lo de trunk-based sigue igual** (§1): branch corta + PR + squash merge; **una PR = una unidad
  lógica** (no mezclar dos paquetes en un mismo cambio salvo que sea un solo cambio atómico que los cruza).
- **CI con path-filter por paquete:** cada push corre **solo** lo afectado (build/test/deploy del paquete
  tocado y sus dependientes), no todo el monorepo — mismo motor portable, declarado una vez (DRY, §1.bis).
- **Versionado e historia por paquete:** cada paquete publicable lleva **su propia SemVer** con **tag
  prefijado** (`web-vX.Y.Z`, `api-vX.Y.Z`) y **su propio `CHANGELOG.md`**; el bump se deriva de los
  Conventional Commits **scoped** a ese paquete (`feat(web): …`). Cadencia de release **independiente**
  por paquete; el pipeline corta el tag/release del paquete que cambió, no de todos. **Mecanismo:** cada
  paquete declara `tag_pattern: '<pkg>-v*'` en su `cicd.yml` + su path-filter en el adaptador CI
  (`when: path:`); el motor **no** filtra commits por path — el aislamiento depende de ambos.
- **Frontera de dependencias explícita:** las deps entre paquetes van en una sola dirección válida (cf.
  §2.B SADD); un paquete no importa internals de otro por fuera de su API pública.
- **Lo compartido, una sola vez (DRY):** config, hooks, motor de CI/CD y disciplinas viven a nivel raíz y
  se heredan; no se duplican por paquete.

## 2. Las disciplinas de verificación — verification first

> **⚠ Regla absoluta — TDD + e2e en TODO, sin excepción.** Toda unidad de código lleva **unit test
> (TDD) + e2e (spec de comportamiento y/o verificación de salida perceptible)**, y **perf** si toca el
> hot path. No son alternativas; son filtros independientes. Unas verifican la **salida** (¿produce el
> resultado correcto?) y otras el **diseño** (¿está hecho de la forma correcta?).

### 2.A De salida — artefacto verificable escrito ANTES del código

| Aspecto del cambio | Disciplina | Mecanismo |
|---|---|---|
| **Lógica pura** (cálculo, parsing, scheduling, generación determinística) | **Unit test (TDD)** | test del framework del proyecto |
| **Comportamiento / integración** (flujos, máquinas de estado, forma de una UI/respuesta) | **BDD/spec (e2e)** | spec dado/cuando/entonces |
| **Cualquier cosa perceptible** (render, UI, audio, output de archivo/API) | **Verificación de salida (e2e)** | captura/snapshot/golden + revisión del artefacto |

Las patas **no son alternativas** — son complementarias. Un cambio con un primitivo matemático Y un
efecto perceptible necesita unit test Y verificación de salida. **El e2e nunca se omite**: la captura/
snapshot se declara "no aplica" solo si el sistema no produce salida perceptible, pero entonces el spec
de comportamiento cubre el e2e.

Para cualquier code path o cambio de comportamiento:
1. **Escribir la verificación que falla primero** → confirmar fail → implementar → confirmar pass.
2. Commit; abrir la PR; el body documenta qué pata cubrió qué aspecto (y flagea lo que NO se pudo cubrir).

**Regla de la cobertura múltiple**: todo cambio perceptible se comprueba con **varias muestras en
estados/escalas OPUESTOS y extremos** (cerca/lejos, vacío/lleno, mín/máx, ángulos distintos), **no una
sola foto/caso**. Un artefacto puede esconderse en un estado y saltar en otro — **revisar TODAS las
muestras** (no una) antes de declarar "se ve/funciona bien". Una sola muestra prueba que algo se
renderiza/corre, no que está bien en todo su rango.

**Alcanzabilidad (UI/feature):** una verificación aislada prueba que algo RENDERIZA/CORRE, **no que es
ALCANZABLE** por el usuario. Nada se mergea sin su entrada real (binding/menú/ruta/interacción) — o se
marca WIP/deferred con el gap declarado.

**Perf**: medir el caso más estresado del cambio (promedio **y p99**). **Obligatorio si toca el hot
path**. Reportar p99 además del promedio (promedio bueno con p99 malo = stutters = falla). Medir en el
**peor perfil** realista (carga/movimiento/concurrencia), no solo el caso quieto. Cada componente con
requisitos de perf lleva un **budget documentado**; una **regresión >5 % bloquea el merge** salvo
justificación explícita en el PR. Vigilar la **amplificación de acceso a datos (N+1)**: preferir una
consulta con join/batch a N consultas en loop por render/request.

**La fuente de verdad primaria son los DATOS, no la impresión.** La captura/lectura subjetiva es
evidencia **necesaria pero no suficiente**. La verdad primaria son logs, valores, asserts, métricas y
las **validaciones del runtime** (validation layers, type checkers, sanitizers). Si una impresión
contradice los datos, **priorizar los datos**. Toda confirmación de salida pasa **también** por el
segundo modelo (§0.0).

**Infra de verificación durable, no temporal.** Si falta un modo para verificar lo que necesitás,
**parametrizá** el mecanismo existente con un caso nuevo (DRY) — NO agregues un diagnóstico efímero para
revertir después. Solo se acepta efímero si es imposible parametrizarlo (y se borra al cumplir).

### 2.B De diseño — bloque corto en el PR body (o "no-op — …"; el silencio = "ni lo pensé")

**SADD — Software Architecture Driven Design.** Gatilla si el cambio toca límites entre módulos, agrega
una dependencia entre módulos, expone API público, introduce un sistema nuevo, o cambia el grafo de
includes/imports público. Contestar: (1) **Módulo dueño** (¿quién es dueño? si va en el equivocado,
justificá); (2) **Delta de deps** (dirección válida); (3) **Patrón existente** (sibling que ya lo hace,
o este PR lo establece); (4) **Fronteras** (las capas de bajo nivel no filtran al dominio). Si no
aplica: `Architecture (SADD): no-op — …`.

**PDD — Performance Driven Design.** Gatilla si toca el hot path, agrega allocations por iteración, I/O
síncrono, threads o cómputo pesado. Contestar: (1) **¿Hot path? ¿cuánto cuesta?**; (2) **Budget**;
(3) **Allocations** (¿algo por iteración? → cache/setup); (4) **Async-able** (¿worker/async?);
(5) **Escenario de regresión** (¿hay un test que detecte una regresión 10×?). Si no aplica:
`Performance (PDD): no-op — …`.

**UXDD — UX Driven Design.** Gatilla si el usuario VE o INTERACTÚA (UI, bindings, mensajes, feedback,
accesibilidad). Contestar: (1) **Principios** (claridad/feedback inmediato/transparencia/coherencia
entre contextos/input parity/respeto del tiempo del usuario); (2) **Anti-patterns** evitados
(hold-to-confirm repetido, menús >3 niveles, info crítica solo por color, animaciones no-skippables,
tutoriales modales, stats ocultos); (3) **Capa de marca** (separar la voz del **producto/empresa hacia
el usuario** de la voz del **sistema/in-app/in-personaje** del mundo interno; no mezclarlas); (4)
**Accesibilidad** (escala, contraste suficiente, info no-solo-por-color, navegación por teclado,
low-motion); (5) **Estructura de UI — Atomic Design (obligatorio en TODO frontend, cualquier framework
de componentes):** la UI se compone en **átomos → moléculas → organismos → templates → páginas**;
componentes chicos, reutilizables y composables, sin duplicar (DRY) ni saltear niveles. Todo cambio
visible se revisa además contra el cuerpo de heurísticas/leyes de UX/UI del proyecto (si lo tiene). Si no
aplica: `UX (UXDD): no-op — …`.

## 3. Gates de verificación por PR + definición de ENTREGADO

**ENTREGADO** — nada está entregado si no tiene: (1) tests TDD en verde, (2) tests e2e en verde,
(3) test de **performance** en verde si toca hot path, (4) push + merge a `main` por la branch corta
(PR), y (5) **build/arranque** revisado (construye y arranca limpio tras mergear). Si falta cualquiera,
**NO** está entregado.

**Pipeline a punto fijo.** Si **cualquier** etapa de verificación (test, diseño, perf, revisión) obliga
a un cambio, se re-corre el pipeline **completo desde el principio** —no solo la etapa que falló: un fix
puede romper otra cosa—; se itera hasta que **una pasada entera no genere ningún cambio** y todos los
gates pasen. Recién ahí la iteración está terminada.

Antes de mergear una PR que toca código, el body confirma:
- **Build** limpio: exit 0, sin warnings nuevos tratados como error.
- **TDD + e2e** (obligatorios): suite 100 % verde; e2e por spec y/o verificación de salida.
- **Perf** (si hot path): promedio + p99 citados del log/test.
- **Gate del runtime/compilación especial** (si toca shaders, migraciones, schemas, pipelines, infra de
  bajo nivel): el artefacto **compila/valida** sin error **con las validaciones del runtime activadas** —
  corriendo el modo que realmente los ejercita (un harness puede no cubrir todo).
- **Smoke** (si aplica): el ejecutable/servicio arranca y llega a un estado usable sin error fatal.
- **Verificación de salida** (si perceptible): cita el artefacto (captura/snapshot/log), qué confirma y
  el seed/fixture. Bug-fixes: before + after, **con su test de regresión** (falla contra el código
  viejo, pasa con el fix; un fix sin test de regresión no está terminado).
- **Observabilidad** (si toca lógica crítica): el cambio deja logs/métricas/trazas suficientes para
  operarlo y diagnosticarlo en producción (no se mergea lógica crítica a ciegas).
- **Bloques de diseño** SADD/PDD/UXDD (§2.B).
- **Principios** (chequeo en CADA cambio/iteración, sin excepción): el cambio respeta **Clean Code**
  (nombres claros, funciones chicas, sin código muerto), **SOLID**, **KISS** (la solución más simple que
  funciona), **DRY** (una sola fuente de verdad; reusar/parametrizar antes que duplicar, §3.ter),
  **YAGNI** (no construir lo que no se necesita aún), **Arquitectura Hexagonal** (ports & adapters: el
  dominio en el centro, sin depender de infraestructura/UI/IO; las dependencias apuntan hacia adentro y
  lo externo entra por puertos/adaptadores — cf. §2.B SADD) y las **mejores prácticas de la industria**
  vigentes del stack. Tensión DRY vs KISS/YAGNI: ante la duda preferí lo simple y concreto; abstraé
  recién cuando la duplicación duele de verdad. La Arquitectura Hexagonal es el patrón por defecto; un
  proyecto chico/sin IO real puede simplificarla, declarándolo. Si un cambio viola un principio a
  propósito (deuda deliberada), declararlo en el CHANGELOG.

**Limpieza tras cada entrega**: borrar los efímeros que ya no se usan (capturas revisadas, scripts de un
solo uso, artefactos de build descartados, ramas mergeadas). No borrar nada versionado/útil ni los tests.

**Verification gaps**: declararlos explícitos cuando son inevitables y encolar el follow-up. PRs docs-only
skipean build/test/captura (decilo), pero llevan los bloques de diseño cuando aplican.

**Verificación en capas — ninguna herramienta sola alcanza.** Combiná **análisis estático/linter**
(evita errores tontos mientras codeás) + **scanners/validadores automáticos del runtime** (encuentran
problemas comunes) + **tests automatizados unit/integración/e2e** (evitan regresiones) + **revisión**
(humana/segundo-modelo: confirma si realmente sirve). Cada capa atrapa lo que la otra no. Aplicá la que
corresponda al stack en cada momento del desarrollo (mientras codeás → linter; local → validadores/
scanners; CI → tests e2e + regresión; pre-merge → revisión). La accesibilidad, la seguridad y la
performance se verifican igual: lint + scanner + test automatizado + revisión, no una sola. La
verificación de **accesibilidad es 100 % automatizada** (sin QA manual, sin testeo a teclado ni lectores
de pantalla operados a mano) y es **gate de CI**: una regresión de a11y en las rutas principales bloquea
el merge igual que un test. (Las herramientas automáticas no cubren todo WCAG; se asume ese límite a
cambio de cero fricción manual.) Donde la plataforma provea **auditorías de calidad** (accesibilidad,
SEO, best-practices, performance), se mantienen en su **puntaje máximo** como invariante y gate de CI.
**No se borra ni se saltea un test** para pasar el gate (`skip`/`xfail` solo temporal, documentado y
con follow-up encolado).

## 3.bis Disciplina documental — qué va en cada archivo

Roles **estrictamente separados**; mantenerlos es parte de cada PR. **Convención: los docs de proceso de
la raíz van con basename en MAYÚSCULAS** (`GOAL.md`, `README.md`, `IDEAS.md`, `BACKLOG.md`,
`CHANGELOG.md`, `AGENTS.md`; ⚠ en FS case-insensitive verificar con `git ls-files`).
- **`GOAL.md`** — el norte: pregunta-filtro + loop mínimo. Se lee antes de cada iteración; casi nunca cambia.
- **`README.md`** — visión + estático (arquitectura macro, setup, controles/uso). NUNCA roadmap,
  "current state", features recientes, ideas. Si muta cada PR, no va al README.
- **`IDEAS.md`** — propuestas no comprometidas, con dificultad (S/M/L/XL) + valor. **Una idea NO se
  implementa desde IDEAS:** antes de realizarse **pasa a `BACKLOG.md`** (priorizada, con scope+done) y se
  **QUITA de `IDEAS.md`** (mover, no copiar). Implementar algo que sigue solo en IDEAS está prohibido.
- **`BACKLOG.md`** — tareas comprometidas priorizadas por ROI, con scope + done. **Al ENTREGAR, la tarea
  se QUITA de `BACKLOG.md` y su registro pasa a `CHANGELOG.md`** (mover, no copiar): no se deja la tarea
  marcada `✅` en BACKLOG. BACKLOG contiene solo lo pendiente/en curso.
- **`CHANGELOG.md`** — append-only: cada PR mergeado = entry (título + fecha + cambios + verificación).
- **Docs narrativos/de showcase** (si el proyecto los tiene, p. ej. lore o portfolio) — avanzan **en
  paralelo** al código: una feature nueva sin su entrada correspondiente está incompleta; reflejan el
  mejor estado actual, no un snapshot viejo.

**Flujo de movimiento (regla dura): IDEAS → BACKLOG → CHANGELOG, siempre MOVIENDO (quitar del origen,
agregar al destino), nunca copiando ni dejando duplicado.**

**Flujo cada PR:** actualizar CHANGELOG (siempre que entregue algo, **quitando** la tarea de BACKLOG) +
mover ideas maduradas de IDEAS a BACKLOG en el mismo merge. README solo si cambió algo estático. Un PR
que entrega y NO toca CHANGELOG bloquea la coherencia. Re-evaluar showcase/README cada iteración que
avance lo que se ve o se promete (actualizarlos en el mismo merge; ninguno queda mostrando un estado peor
o desactualizado).

**No se crean archivos de documentación nuevos** (`*.md`, READMEs y similares) salvo pedido explícito del
usuario, como parte del flujo spec/plan de un cambio con complejidad arquitectónica genuina (§0.ter), o
como actualización de los docs vivos de arriba (GOAL/README/IDEAS/BACKLOG/CHANGELOG/showcase). La doc por
default vive en los archivos que ya existen, no en archivos nuevos sueltos.

## 3.ter Disciplina de flags/parámetros de ejecución — SOLID/DRY/KISS/YAGNI

Antes de agregar CUALQUIER parámetro/flag/env-var/script de ejecución, aplicá la escalera (parate en el
primero que sirva): (1) **Reusá** un flag/modo existente; (2) **Parametrizá una familia existente** en
vez de un flag nuevo (DRY): un caso nuevo de un mecanismo existente, no un mecanismo nuevo; (3)
**Diagnóstico puntual** (pokear estado runtime UNA vez): NO committees env-var + script, usá un branch
temporal que **borrás** (YAGNI); (4) **Flag/env-var PERMANENTE** solo si es necesidad **recurrente y
parametrizada**, documentado en la tabla **en el mismo PR** (DRY: una env-var se lee en **un** accessor);
(5) **Borrá** los one-off cuando cumplieron. **No dupliques mecanismos:** un modo por flag CLI y además
por env-var son dos sistemas para lo mismo — converger, no sumar. **Tipos de flag** (cada uno con dueño
+ fecha/condición de borrado): `release` (ocultar lo incompleto), `experiment` (A/B), `ops`
(kill-switch) y `permission` (por usuario/rol/tenant). **Toggle = switch, no comentar código:** para prender/apagar algo que **ya funciona**, usá
un switch (flag/env/config) con **default seguro** (ausente ⇒ comportamiento más restrictivo/estable) y nombre que diga qué activa
(`ALLOW_PUBLIC_REGISTRATION`, no `FLAG_7`) — **nunca** comentar/borrar/restaurar código. (Feature nueva → desarrollala; bug →
arreglalo; código muerto definitivo → borralo: ninguno de esos es un switch.)

**Lo mismo aplica a las dependencias externas.** Antes de sumar una, subí la misma escalera: ¿lo resuelve
algo que ya está en el árbol o en la stdlib del stack? ¿vale el costo permanente (peso del artefacto,
mantenimiento, superficie de seguridad/ataque, una transitiva más que auditar)? **No se agrega una
dependencia sin justificación registrada en el PR**; ante la duda, parametrizar/reusar lo existente o
escribir lo mínimo propio antes que sumar una dependencia (KISS/YAGNI). Cada dependencia nueva es un
compromiso, no un atajo. Para deps que viajan en el artefacto distribuido (código de cliente/bundle), medí el **delta de tamaño
antes/después** y justificá si crece de forma no trivial.

## 3.quater Tamaño de este archivo — límite soft 36 KB / hard 40 KB (sin perder info jamás)

`AGENTS.md` se inyecta entero cada sesión, así que su tamaño es un recurso. **Dos límites: soft 36 KB
(objetivo a no cruzar) y hard 40 KB (tope final infranqueable).** Pasar el soft es una señal para
condensar/mover detalle a `docs/`; pasar el hard está **prohibido**. Pero ningún límite **justifica
perder información**: el tamaño se controla **moviendo** detalle a `docs/`, no borrando reglas. Apuntá a
~34–37 KB para headroom. Si encoge de golpe sin una migración documentada, es señal de que se perdió
contenido — restaurá lo que falte. Toda PR que toque `AGENTS.md` re-chequea el tamaño (el gate de CI lo
verifica contra el hard de 40 KB).

## 3.quinquies Portfolio de venta — material comercial en `nicolasbatistoni/portfolio`

Todo proyecto **publicable/vendible** mantiene su material de portfolio **pensado para la venta** en el
repo central **`nicolasbatistoni/portfolio`**, bajo una carpeta con el **nombre del repo del proyecto**:
`nicolasbatistoni/portfolio/<nombre-repo-del-proyecto>/`. Es el material que se le muestra a un cliente
potencial (no doc técnica): qué problema resuelve, para quién y con qué resultado.

**Sin detalle de implementación (regla dura):** el portfolio **nunca nombra tecnologías, frameworks,
librerías, lenguajes, arquitectura, infraestructura ni decisiones técnicas**. Se habla en lenguaje de
**cliente** (problema → solución → resultado), no del "cómo está hecho". Cualquier entrada que mencione
el "cómo" técnico no cumple y se corrige.

**Estructura única (igual para todos los proyectos):**
```
nicolasbatistoni/portfolio/<nombre-repo-del-proyecto>/
  README.md      # caso de estudio de venta: Problema → Solución → Resultado/impacto →
                 #   Capturas → CTA (demo / contacto). SIN stack ni detalle técnico.
  img/           # capturas REALES del producto corriendo (1 hero + galería), no mockups
  meta.yml       # título, tagline (1 línea), categoría, links (demo/video), estado, fecha
```

**El sitio `otara-labs` refleja exactamente este repo:** la sección portfolio de la web muestra
**exactamente** el contenido del repo `nicolasbatistoni/portfolio` (mismo texto y mismas capturas, por
proyecto). El repo es la **fuente de verdad** del material de venta; la web no agrega copy ni detalle de
implementación que no esté ahí. Si cambia uno, se actualiza el otro en el mismo cambio.

**Actualización en CADA cambio/iteración (regla dura):** el material de portfolio se actualiza **en el
mismo merge** que avanza lo que se ve o se promete. Una feature de cara al usuario **sin** su entrada/
capturas de portfolio actualizadas está **incompleta** (no cumple la Definición de ENTREGADO, §3). El
portfolio refleja **el mejor estado actual**, nunca un snapshot viejo o peor que el producto real.

**Privacidad (ver §6):** en el material público **nunca se nombran personas** (clientes, dueños,
contactos); sí se pueden nombrar **negocios/marcas**. Las imágenes son **capturas reales** del sistema
corriendo, no mockups ni diagramas.

## 4. Knowledge base + memoria — TODO in-repo, nunca fuera

KB, research, docs **y la memoria cross-session de los agentes** viven versionados bajo `docs/`. NO usar
el directorio de memoria per-máquina del harness como home de knowledge; si el harness de auto-memoria
escribe ahí, **migrar al repo**.
- **`docs/kb/`** — knowledge autoritativa, citation-anchored. Índice en `docs/kb/README.md`.
- **`docs/research/`** — research fuente del usuario (tracked).
- **`docs/notes/`** — gotchas / correcciones / preferencias / estado. Índice en `docs/notes/MEMORY.md`.

Research nueva: leer → diff vs condensación existente → sumar fuente a `docs/research/` → actualizar
`docs/kb/` + índice → branch+PR.

## 4.bis Proyectos referentes — consultar la implementación hermana

Si existe un proyecto **hermano/referente** que ya resolvió una mecánica/modelo (aunque sea en otro
stack), ante **cualquier duda de cómo implementar** (root-cause, approach, fórmula, orden causal, qué
cuenta como "correcto") **consultalo primero**: su CHANGELOG lista lo entregado con el modelo citado, su
BACKLOG/IDEAS el pool pendiente, y su código la referencia real. No es copy-paste entre stacks distintos,
pero **el modelo, las fórmulas y el orden causal se portan**. Las tareas importadas viven marcadas en el
BACKLOG con su procedencia.

## 5. Cuando dudes

Verificá contra el código, no contra intuición o memoria. Las entries de memoria son snapshots; las citas
`file:line` envejecen. El repo es la fuente de verdad. Para modelos/fórmulas, el referente es el proyecto
hermano (§4.bis).

## 6. Project policies (compromisos permanentes)

Sobreviven iteraciones de feature. Una PR que quiera violar una policy modifica el doc primero (con la
evidencia que cambió), no in-silently:
- **Backward-compatibility de datos persistidos** (expand/contract; nunca romper un dato/save/schema
  existente sin migración).
- **Versionado SemVer 2.0.0** (https://semver.org) — `MAJOR.MINOR.PATCH`: **MAJOR** = cambio incompatible
  de API/datos públicos; **MINOR** = funcionalidad nueva backward-compatible; **PATCH** = bugfix
  backward-compatible. En **`0.y.z`** (desarrollo inicial) cualquier cosa puede cambiar; se sube MINOR por
  release. `1.0.0` recién al estabilizar la API/contenido público. Los **git tags** llevan prefijo `v`
  (`v0.3.0`); la semver es sin la `v`. **Pre-release**: sufijo `-alpha.1` / `-rc.1` (menor precedencia);
  **build metadata**: sufijo `+sha.abc123` (ignorado para precedencia). El **bump** lo determina el
  contenido, mapeado desde Conventional Commits: `fix`→PATCH, `feat`→MINOR, `feat!:` / `BREAKING CHANGE:`
  →MAJOR; `chore/docs/style/test/ci/build/refactor` no cortan versión (salvo breaking). Una versión
  publicada es **inmutable** (cambio → versión nueva; release fallida → nueva PATCH, nunca se reescribe
  ni se mueve un tag). Toda release consumible por humanos lleva su **artefacto + checksum** y notas con
  Summary / Added-Fixed-Changed / Breaking changes / migraciones de datos / rollback. **Hotfix** = branch
  `fix-…` → PR → merge → tag PATCH → release (sin ramas `hotfix/*`). **API pública** (lo que cuenta para el bump) = el contrato
  observable hacia afuera: endpoints/respuestas, URLs y formas de datos públicas, variables de entorno documentadas y schema
  persistido en lo que afecta compatibilidad; **refactors internos y cambios de UI sin cambio de contrato NO son cambios de API
  pública**. **Deprecaciones:** documentarlas y mantenerlas vivas **al menos una MINOR** antes de removerlas en una MAJOR.
- **Tag vs release:** toda release se ancla en un tag, pero **no todo tag necesita release**. Un
  **servicio/app de despliegue continuo** lleva tag siempre y release solo cuando hay algo que
  comunicar; una **librería/CLI/SDK/artefacto público consumible** lleva tag + release + changelog
  **siempre**.
- **Definición de deploy = fuente de verdad en git (GitOps).** El estado desplegado se declara en
  `infra/**` del repo (manifests k8s / Compose); **el pin `:X.Y.Z` lo escribe el pipeline (`promote`),
  nunca la mano** (editar un `image:` en producción = drift, prohibido). Disparador = **commit de
  definiciones**, no "apareció una imagen en el registry" (**sin pollers ni `:latest` como trigger**).
  **Rollback = `git revert` del bump**: el agente pull reconcilia a la versión previa (cf. §1.bis,
  `STACKS.md §6`).
- **Privacidad en material público** (showcase/portfolio/marketing/demos): **nunca nombrar personas**
  (clientes, dueños, contactos); sí se pueden nombrar **negocios/marcas**. Las imágenes públicas del
  producto son **capturas reales** del sistema corriendo, no mockups ni diagramas.
- **Estado del proyecto: activo / mantenimiento / archivado / experimento.** Cada repo declara su estado
  en el `README.md`. **Activo** = aplica la Definición de ENTREGADO y todos los gates (§3) sin excepción.
  **Mantenimiento** = sin features nuevas; solo fixes (seguridad/críticos) con sus gates. **Archivado /
  legacy** = **congelado**: no se le agregan features, **exento de los gates activos** (TDD/e2e/perf,
  portfolio/showcase, build obligatorio) y de la disciplina documental viva; se toca solo por un fix de
  seguridad puntual, y se documenta. **Experimento / spike** = vive corto, no es default de nada y se
  promueve a activo (asumiendo todos los gates) o se archiva; no queda a medio camino indefinidamente.
  Un proyecto **archivado/legacy/experimento no es referencia de stack para algo nuevo** (la elección de
  tecnología nueva se rige por `STACKS.md`, §0.quater). **Reactivar** = cambiar el estado en el `README.md`
  y volver a cumplir ENTREGADO antes del próximo merge de feature.
- Cualquier otro compromiso de dominio del proyecto vive en el `AGENTS.md`/`GOAL.md` del proyecto.

## 7. Enforcement local, build del artefacto y datos de usuario

- **Hooks versionados (enforcement local).** Tras clonar, instalar los hooks del repo (apuntando
  `core.hooksPath` al directorio de hooks versionado) para que las reglas se enforcen en cada máquina aun
  sin branch protection server-side. Mínimos: `pre-commit` (bloquea commit directo a la rama principal,
  archivos enormes, secrets obvios), `pre-push` (bloquea push directo y force-push no-fast-forward),
  `commit-msg` (Conventional Commits con los types permitidos). **Prohibido:** saltear hooks
  (`--no-verify` o equivalente), `--force`/force-push sobre la rama principal, y `--no-edit` en un rebase.
- **Escaneo de seguridad — gate de CI (no del hook).** El scan completo (Trivy: vulns HIGH/CRITICAL en
  dependencias, secrets, misconfigs de IaC, licencias prohibidas) corre en el **stage `security` de CI**,
  bloqueante pre-merge. Localmente el `pre-commit` hace detección rápida de secrets obvios (complemento,
  no reemplaza el scan de CI). Hallazgo **corregible** → arreglar antes de mergear; **falso positivo /
  riesgo aceptado** → entrada en el ignore-file del scanner con **justificación + fecha de revisión
  obligatoria** (`exp:YYYY-MM-DD`). **Nunca silenciar un hallazgo sin justificación ni sin fecha de revisión.**
- **El build del artefacto lo ejecuta el agente — siempre, sin preguntar.** Si el proyecto se distribuye
  como artefacto (binario/paquete/imagen/bundle), ningún cambio que toque código distribuido está
  entregado hasta que el agente corrió el build (con el script del proyecto, que mata procesos que
  bloqueen la salida, limpia el directorio de salida y verifica que el artefacto resultante existe) y
  confirmó que existe. **Nunca delegar el build al usuario ni preguntar "¿buildeo?"**: la entrega siempre
  incluye el resultado buildeado. (El usuario puede pedir buildear a mano; pero por default es del agente.)
- **Limpieza: jamás borrar datos de usuario.** La limpieza post-entrega (§3) nunca toca datos persistidos
  (bases de datos, stores, WAL, uploads) ni archivos del working tree sin commitear (puede ser WIP). Ante
  la duda, preguntar.

---

## Cross-references

`STACKS.md` (elección de tecnología por tipo de software — hermano de éste), `GOAL.md` (el norte),
`README.md` (visión + estático), `IDEAS.md`, `BACKLOG.md`, `CHANGELOG.md`, `docs/kb/README.md`,
`docs/notes/MEMORY.md`, y el material de venta en `nicolasbatistoni/portfolio/<nombre-repo>/` (§3.quinquies).
