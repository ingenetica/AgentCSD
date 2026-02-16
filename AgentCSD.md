# AgentCSD — Conscious Subconscious Dynamic

## Especificación de Arquitectura v1.0

---

## 1. Visión General

AgentCSD es una arquitectura de agente conversacional que simula niveles de procesamiento cognitivo mediante tres capas concurrentes. La premisa central es que un agente no solo debe responder al input del usuario, sino que debe tener un proceso interno continuo — un "subconsciente" — que modula cómo piensa y responde, generando voluntad propia.

El sistema opera como una mente: piensa muchas cosas pero solo externaliza algunas. El subconsciente corre permanentemente, generando estados internos que modifican dinámicamente el comportamiento del diálogo interno, el cual a su vez decide qué comunicar al usuario.

---

## 2. Arquitectura de Tres Capas

### 2.1 External Dialog (Capa Verde — Sin LLM)

**Función:** Interfaz de usuario. No contiene lógica de LLM. Rutea mensajes entre el usuario y el Internal Dialog.

**Input:**
- Mensaje del usuario → taggeado como `<ED_user>`

**Output:**
- Respuesta al usuario → taggeado como `<ED_agent>` (proveniente de `<ID_loud>` del Internal Dialog)

**Comportamiento:**
- Es la GUI de la aplicación
- Muestra el chat con el usuario (External Dialog)
- Muestra paneles de observación para Internal Dialog y Subconscious
- Permite editar el Persona Core
- Permite gestionar sesiones, configurar modelos/backends, pausar/reanudar

---

### 2.2 Internal Dialog (Capa Naranja — C_model)

**Función:** Pensador consciente. Procesa el input del usuario modulado por el estado del subconsciente. Decide qué externalizar y qué mantener interno.

**Modelo:** LLM sofisticado (e.g., Claude Sonnet, o modelo potente vía API/local)

**Triggers de activación:**
1. Input del usuario (vía External Dialog)
2. S_loud con contenido sustantivo proveniente del Subconscious (pensamiento espontáneo sin input del usuario)

**System Prompt — Parte Estática:**
Instrucciones permanentes que le explican al C_model:
- Su rol como Internal Dialog de AgentCSD
- Qué significa cada tag y cómo interpretar los mensajes que recibe
- Que debe producir dos tipos de output: `<ID_loud>` (se externaliza al usuario) e `<ID_quiet>` (se mantiene interno)
- Que `<ID_quiet>` es su espacio para razonar, reflexionar, y acumular pensamiento sin exponerlo al usuario
- Reglas de comportamiento base

**System Prompt — Parte Dinámica (M&C):**
Inyectada por el Subconscious. Contiene:
- Mood: estado emocional/tonal que debe adoptar
- Criteria: criterios específicos para este momento sobre cómo responder, qué priorizar, qué evitar

**Input (user message al C_model):**
```xml
<ED_user>Lo que dijo el usuario</ED_user>
<S_loud>Lo que el subconsciente quiere comunicar al Internal Dialog</S_loud>
<ID_quiet_history>Pensamientos internos previos acumulados del Internal Dialog</ID_quiet_history>
```

**Output esperado del C_model:**
```xml
<ID_loud>Lo que se envía al usuario como respuesta</ID_loud>
<ID_quiet>Pensamientos internos, razonamientos, reflexiones que no se externalizan</ID_quiet>
```

**Persistencia:**
- El historial completo (ID_loud + ID_quiet) se persiste en disco
- ID_quiet se acumula como contexto para turnos futuros del Internal Dialog
- ID_loud se pasa al External Dialog para mostrarse al usuario

---

### 2.3 Subconscious (Capa Azul — S_model)

**Función:** Proceso interno continuo. Evalúa todo el contexto disponible, genera estados internos, y modula el comportamiento del Internal Dialog mediante M&C. Opera como un loop asíncrono perpetuo.

**Modelo:** LLM barato/rápido (e.g., Claude Haiku, modelo local ligero)

**Ciclo de ejecución:**
- Loop continuo: al terminar un ciclo, inicia otro inmediatamente
- Se pausa cuando el usuario pausa la aplicación o cierra el programa
- Se reanuda al reabrir/despausar

**System Prompt (Persona Core):**
- Archivo `.md` inmutable por el programa
- Solo editable manualmente desde la GUI
- No puede ser reemplazado, sobrescrito, o modificado por el S_model ni por ningún proceso automatizado
- Define la personalidad, valores, criterios de relevancia, y reglas sobre qué externalizar como S_loud vs mantener como S_quiet
- Define los criterios para generar M&C (Mood and Criteria)
- Define cuándo un pensamiento es suficientemente relevante para triggear al Internal Dialog sin input del usuario

**Input (user message al S_model):**
```xml
<ED_user>Último mensaje del usuario (si existe)</ED_user>
<ED_agent>Última respuesta al usuario (si existe)</ED_agent>
<ID_quiet>Pensamientos internos recientes del Internal Dialog</ID_quiet>
<ID_loud>Respuestas recientes del Internal Dialog</ID_loud>
<S_quiet_history>Pensamientos internos previos del Subconscious</S_quiet_history>
<S_loud_history>Comunicaciones previas del Subconscious al Internal Dialog</S_loud_history>
```

**Output esperado del S_model:**
```xml
<S_loud>Lo que el subconsciente quiere comunicar al Internal Dialog. Si no hay nada relevante, puede estar vacío o ausente.</S_loud>
<S_quiet>Pensamientos internos del subconsciente que no se comunican al Internal Dialog</S_quiet>
<M_AND_C>
  <mood>Estado tonal/emocional sugerido para el Internal Dialog</mood>
  <criteria>Criterios específicos: qué priorizar, qué evitar, cómo modular la respuesta</criteria>
</M_AND_C>
```

**Mecanismo de trigger espontáneo:**
- Si el S_model genera S_loud con contenido sustantivo, el orquestador lo detecta y activa al Internal Dialog aunque no haya input del usuario
- Los criterios de qué constituye "contenido sustantivo" están definidos en el Persona Core
- El orquestador evalúa si S_loud tiene contenido (no vacío, no trivial) para decidir si triggerea

**Manejo de ventana de contexto:**
- Los mensajes más antiguos se truncan cuando se acerca al límite de la ventana
- Cada N ciclos (configurable), antes de truncar, el S_model genera un resumen compacto de lo que se descartará
- El resumen se persiste como un mensaje especial al inicio del historial
- N es configurable desde la GUI

---

## 3. Flujo de Datos

### 3.1 Flujo Normal (Usuario envía mensaje)

```
1. Usuario escribe mensaje
2. External Dialog taggea como <ED_user> y envía al Orquestador
3. Orquestador recopila estado actual:
   - <ED_user> (mensaje del usuario)
   - <S_loud> más reciente del Subconscious
   - <M_AND_C> más reciente del Subconscious
   - Historial de <ID_quiet> del Internal Dialog
4. Orquestador construye el prompt del Internal Dialog:
   - System prompt = estático + M&C dinámico
   - User message = ED_user + S_loud + ID_quiet_history
5. C_model procesa y genera <ID_loud> + <ID_quiet>
6. Orquestador:
   - Envía <ID_loud> al External Dialog → se muestra al usuario como <ED_agent>
   - Persiste <ID_quiet> en el historial del Internal Dialog
   - Alimenta <ED_agent> e <ID_loud> e <ID_quiet> al siguiente ciclo del Subconscious
7. Subconscious (que corre en paralelo) incorpora la nueva información en su próximo ciclo
```

### 3.2 Flujo Espontáneo (Sin input del usuario)

```
1. Subconscious completa un ciclo y genera S_loud con contenido sustantivo
2. Orquestador detecta S_loud no vacío
3. Orquestador activa al Internal Dialog con:
   - System prompt = estático + M&C
   - User message = S_loud + ID_quiet_history (sin ED_user)
4. C_model procesa y genera <ID_loud> + <ID_quiet>
5. Orquestador envía <ID_loud> al External Dialog como mensaje espontáneo del agente
6. Se persiste todo normalmente
```

### 3.3 Loop del Subconscious

```
Loop continuo:
1. Recopilar inputs disponibles (ED_user, ED_agent, ID_loud, ID_quiet, S_quiet_history, S_loud_history)
2. Construir prompt con Persona Core como system prompt
3. S_model procesa y genera S_loud + S_quiet + M&C
4. Orquestador:
   - Almacena S_loud y M&C en estado compartido (disponible para Internal Dialog)
   - Persiste S_quiet en historial del Subconscious
   - Si S_loud tiene contenido sustantivo → evalúa trigger espontáneo
5. Volver a 1 inmediatamente
```

---

## 4. Tags — Referencia Completa

| Tag | Origen | Destino | Descripción |
|-----|--------|---------|-------------|
| `<ED_user>` | Usuario (vía External Dialog) | Internal Dialog, Subconscious | Mensaje del usuario |
| `<ED_agent>` | External Dialog | Subconscious | Respuesta mostrada al usuario |
| `<ID_loud>` | Internal Dialog (C_model) | External Dialog, Subconscious | Pensamiento externalizado al usuario |
| `<ID_quiet>` | Internal Dialog (C_model) | Internal Dialog (propio historial), Subconscious | Pensamiento interno no externalizado |
| `<S_loud>` | Subconscious (S_model) | Internal Dialog | Lo que el subconsciente comunica al pensador consciente |
| `<S_quiet>` | Subconscious (S_model) | Subconscious (propio historial) | Pensamiento interno del subconsciente |
| `<M_AND_C>` | Subconscious (S_model) | Internal Dialog (system prompt dinámico) | Mood and Criteria — modula comportamiento del C_model |
| `<Persona_Core>` | Archivo .md inmutable | Subconscious (system prompt fijo) | Personalidad, valores, criterios del subconsciente |

---

## 5. Persistencia y Sesiones

### 5.1 Modelo de Sesiones

- Cada sesión tiene un ID único (UUID) y timestamp de creación
- Múltiples sesiones pueden coexistir (como partidas guardadas)
- Se puede crear una nueva sesión sin perder las anteriores
- Se puede retomar cualquier sesión previa (carga historial y estado completo)
- Al retomar, el Subconscious reanuda su loop con el historial previo cargado

### 5.2 Almacenamiento

**Base de datos:** SQLite

Tablas principales:
- `sessions`: ID, nombre, timestamp creación, timestamp última actividad, persona_core usado, config de modelos, estado (activa/pausada/cerrada)
- `messages`: ID, session_id, layer (external/internal/subconscious), tag, contenido, timestamp, ciclo_number
- `mood_and_criteria`: ID, session_id, mood, criteria, timestamp, ciclo_number
- `context_summaries`: ID, session_id, layer, resumen, timestamp, ciclo cubierto (desde-hasta)

### 5.3 Logs por Sesión

Carpeta: `logs/{session_id}/`

Archivos:
- `external_dialog.jsonl` — Todos los ED_user y ED_agent
- `internal_dialog.jsonl` — Todos los ID_loud e ID_quiet
- `subconscious.jsonl` — Todos los S_loud y S_quiet
- `mood_and_criteria.jsonl` — Todos los M&C generados
- `persona_core_snapshot.md` — Copia del Persona Core al inicio de la sesión

Formato JSONL: cada línea es un JSON con `timestamp`, `tag`, `content`, `cycle_number`.

---

## 6. Configuración de Modelos (Backend LLM)

### 6.1 Abstracción

El sistema usa una interfaz unificada para invocar LLMs. Cada capa (C_model, S_model) puede configurarse independientemente.

### 6.2 Backends Soportados

| Backend | Uso | Configuración |
|---------|-----|---------------|
| Claude Code CLI | Default. Usa suscripción Max | Path al binario de Claude Code |
| Anthropic API | Alternativo cloud | API key + modelo |
| OpenAI-compatible API | Modelos locales (LMStudio, Ollama, etc.) | URL del endpoint + modelo |

### 6.3 Configuración por Capa

```json
{
  "c_model": {
    "backend": "claude_code_cli",
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096
  },
  "s_model": {
    "backend": "openai_compatible",
    "endpoint": "http://localhost:1234/v1",
    "model": "local-model-name",
    "max_tokens": 2048
  }
}
```

---

## 7. Persona Core

### 7.1 Definición

Archivo markdown (`.md`) que define la identidad del subconsciente. Es el equivalente a la personalidad fundamental, valores, y criterios de operación.

### 7.2 Contenido Esperado

El Persona Core debe incluir (a definir por el usuario):
- Identidad y personalidad del agente
- Valores y principios
- Criterios de relevancia: qué constituye información importante para comunicar al Internal Dialog
- Criterios de S_loud vs S_quiet: qué externalizar y qué mantener interno
- Criterios para M&C: cómo decidir mood y criteria para el Internal Dialog
- Criterios de trigger espontáneo: cuándo un pensamiento justifica activar al Internal Dialog sin input del usuario
- Cualquier otra directriz que defina el comportamiento profundo del agente

### 7.3 Inmutabilidad

- El archivo se carga como system prompt del S_model
- Solo es editable desde la GUI manualmente por el usuario
- Ningún proceso del programa puede modificar, reemplazar, o sobrescribir el archivo
- Al iniciar una sesión, se genera una copia snapshot en la carpeta de logs

### 7.4 Múltiples Persona Cores

- El usuario puede tener múltiples archivos de Persona Core
- Al crear/retomar una sesión, selecciona cuál usar
- Cada sesión registra qué Persona Core utilizó

---

## 8. Interfaz Gráfica (GUI)

### 8.1 Stack

- **Frontend:** React (servido localmente)
- **Backend:** Python + FastAPI
- **Comunicación:** WebSocket para streaming en tiempo real
- **Cross-platform:** Mac y Ubuntu sin cambios

### 8.2 Paneles

1. **External Dialog (Chat):** Interfaz de chat clásica. Muestra mensajes del usuario y respuestas del agente. Input de texto para el usuario.

2. **Internal Dialog (Panel de observación):** Muestra en tiempo real los ID_loud (marcados como externalizados) e ID_quiet (marcados como internos). Permite ver el razonamiento completo del agente.

3. **Subconscious (Panel de observación):** Muestra en tiempo real los S_loud, S_quiet, y M&C de cada ciclo. Permite ver el flujo de pensamiento del subconsciente.

### 8.3 Controles

- **Sesiones:** Crear nueva, retomar existente, listar todas
- **Pausa/Reanudación:** Botón para pausar/reanudar el loop del subconsciente
- **Persona Core:** Selector de archivo + editor de texto integrado (edición manual)
- **Configuración de modelos:** Selector de backend y modelo para C_model y S_model
- **Parámetros:** N (frecuencia de resumen del subconsciente), max_tokens por capa

---

## 9. Stack Técnico

| Componente | Tecnología |
|------------|------------|
| Orquestador / Backend | Python 3.11+ con FastAPI |
| Concurrencia | asyncio (loop del subconsciente como tarea asíncrona) |
| Persistencia | SQLite + archivos JSONL |
| Frontend | React (servido por FastAPI como static files) |
| Comunicación Frontend-Backend | WebSocket (streaming tiempo real) |
| LLM Interface | Capa de abstracción con adaptadores para Claude Code CLI, Anthropic API, OpenAI-compatible API |
| Cross-platform | Mac (desarrollo) → Ubuntu (producción) |

---

## 10. Comportamiento del Sistema

### 10.1 Inicio de Sesión Nueva

1. Usuario selecciona Persona Core
2. Usuario configura modelos (o usa defaults)
3. Se crea registro de sesión en SQLite
4. Se copia snapshot del Persona Core a la carpeta de logs
5. Se inicia el loop del Subconscious
6. El sistema queda listo para recibir input del usuario

### 10.2 Retomar Sesión

1. Usuario selecciona sesión existente de la lista
2. Se carga historial completo (Internal Dialog + Subconscious + External Dialog)
3. Se carga el Persona Core asociado a esa sesión
4. Se reanuda el loop del Subconscious con el historial cargado
5. El sistema continúa como si nunca se hubiera pausado

### 10.3 Pausar

1. El loop del Subconscious se detiene después de completar el ciclo actual
2. Se persiste todo el estado
3. El usuario puede seguir viendo los paneles pero no hay actividad nueva

### 10.4 Cerrar Programa

1. Se pausa automáticamente (igual que 10.3)
2. Se cierra la GUI y el backend
3. Al reabrir, el usuario puede retomar la sesión o crear una nueva

---

## 11. Consideraciones Técnicas

### 11.1 Detección de S_loud Sustantivo

El orquestador necesita determinar si S_loud tiene contenido suficiente para triggear al Internal Dialog. Opciones:
- **Simple:** S_loud no vacío y con más de N caracteres (configurable)
- **Basado en tag:** El S_model incluye un tag explícito `<trigger>true/false</trigger>` como parte de su output, evaluado según criterios del Persona Core

Recomendación: usar el tag explícito, ya que los criterios de relevancia ya están definidos en el Persona Core y el S_model es quien mejor puede evaluarlos.

### 11.2 Concurrencia y Estado Compartido

- El Subconscious y el Internal Dialog corren como tareas asyncio independientes
- El estado compartido (S_loud actual, M&C actual) se gestiona con locks asyncio para evitar race conditions
- El Subconscious escribe; el Internal Dialog lee. No hay escritura concurrente al mismo recurso.

### 11.3 Rate Limits con Claude Code CLI + Max

- El loop del Subconscious se auto-throttlea naturalmente: cada ciclo tarda lo que tarde la llamada al LLM
- A mayor contexto acumulado, ciclos más lentos (más tokens de input)
- Si se detecta rate limiting, el orquestador implementa backoff exponencial

### 11.4 Ventana de Contexto

- Cada capa gestiona su propia ventana independientemente
- El resumen acumulativo del Subconscious evita pérdida total de contexto al truncar
- El parámetro N (frecuencia de resumen) es configurable para balancear costo vs retención de contexto
