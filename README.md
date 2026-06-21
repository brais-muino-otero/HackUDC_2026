# 🌤️ Santi & Go — Tiempo & Deporte en Galicia

Plataforma regional que conecta la API de **OpenWeatherMap** con **Grafana**
para responder de un vistazo: *¿es buen momento para hacer deporte al aire libre
en cualquier concello de Galicia?* — con **avisos automáticos por Telegram**.

- **Backend:** Python + Flask (modular)
- **Datos:** OpenWeatherMap API (tiempo real)
- **Visualización:** Grafana + plugin **Infinity** (gauges, stats y un **Geomap**)
- **Alertas:** Grafana Alerting → **Telegram** (alerta por concello no apto)

URL plataforma Santi & Go: http://localhost:3000/d/br9bzzl/santi-and-go-c2b7-tiempo-and-deporte-en-galicia
---

## 1. Arquitectura

```
santi-go/
├── main.py              # Punto de entrada Flask (endpoints)
├── config.py            # Token, umbrales y catálogo de concellos (lat/lon)
├── weather_client.py    # Cliente OpenWeather + cache
├── evaluator.py         # Lógica "apto / no apto" (pura, testeable)
├── dashboard.json       # Dashboard listo para importar en Grafana
├── provisioning/
│   └── alerting/
│       ├── contact-point-telegram.yaml
│       └── alert-rule-no-apto.yaml
├── requirements.txt
├── .env.example         # Plantilla del token (copiar a .env)
├── .gitignore
└── test_local.py        # Pruebas sin gastar llamadas a la API
```

**Decisión clave de diseño:** un único endpoint que centraliza la lógica de negocio.

| Petición | Devuelve | Lo consume |
|---|---|---|
| `GET /api/galicia/deporte` | **Todos** los concellos (array) | El **Geomap** y la **alerta** |
| `GET /api/galicia/deporte?municipio=Vigo` | **Un** concello específico | Los **gauges/stats** filtrados |

El backend consulta a la API de OpenWeatherMap, procesa los datos y aplica la lógica de "apto/no apto" según los umbrales configurados. Cada registro del JSON devuelto es:

```json
{
  "ciudad": "Santiago de Compostela",
  "provincia": "A Coruña",
  "latitud": 42.8805,
  "longitud": -8.5457,
  "temperatura": 19.4,
  "precipitacion": 0.0,
  "viento": 10.8,
  "apto": 1,
  "recomendacion": "¡Ideal para deporte!",
  "actualizado": "2026-06-17T02:00:00"
}

```

## 2. Despliegue del backend (paso a paso)

> Comandos para **Windows / PowerShell** (tu entorno). Entre paréntesis, el equivalente Linux/Mac.

```powershell
# 1) Entrar en la carpeta del proyecto
cd santi-go

# 2) Crear y activar un entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# (Linux/Mac:  python3 -m venv .venv  &&  source .venv/bin/activate)

# 3) Instalar dependencias
pip install -r requirements.txt

# 4) Configurar el token de OpenWeather API
copy .env.example .env
# (Linux/Mac:  cp .env.example .env)
# Edita .env y pega tu token en OPENWEATHER_API_KEY

# 5) Lanzar el servidor
python main.py
```

Comprobación rápida (otra terminal o el navegador):

```powershell
curl http://localhost:5000/health
curl "http://localhost:5000/api/galicia/deporte?municipio=Vigo"
curl http://localhost:5000/api/galicia/deporte
```

---

## 3. Importar el dashboard en Grafana

1. **Instala el plugin Infinity** (si no lo tienes):
   *Connections → Add new connection → busca **Infinity** (`yesoreyeram-infinity-datasource`) → Install.*
2. **Crea el datasource Infinity:**
   *Connections → Data sources → Add → Infinity.* Déjalo por defecto y **Save & test**.
3. **Importa el dashboard:**
   *Dashboards → New → Import → Upload JSON file →* selecciona `dashboard.json`.
4. En la pantalla de import te pedirá el datasource: **elige tu Infinity**.
5. Arriba verás dos controles: **Concello** (`$municipio`) y **URL del backend** (`$base_url`).

---

## 4. Geomap: qué campos usar

El panel Geomap ya viene configurado, pero estos son los campos que lo hacen funcionar:

- **Layer type:** `Markers`
- **Location mode:** `Coords`
  - **Latitude field →** `latitud`
  - **Longitude field →** `longitud`
- **Marker color → field `apto`** (umbrales: `0` rojo = no apto, `1` verde = apto)
- **Marker text → field `ciudad`** (etiqueta de cada punto)
- **Tooltip:** `Details`

> Importante: en el target de Infinity, `latitud` y `longitud` deben declararse como
> tipo **number** (ya lo están). Si llegan como *string*, el Geomap no los reconoce
> como coordenadas y no pinta nada.

---

## 5. 🔔 Alertas en Telegram (Nivel Avanzado)

Objetivo: que el ciudadano reciba un aviso en Telegram **sin mirar gráficas** cuando
un concello no sea apto para deporte. Montamos una **alerta multidimensional**: una
sola regla que genera **una instancia por cada concello no apto**, con su nombre y motivo.

### 5.1 Crear el bot y obtener el token + chat ID

1. En Telegram, abre **@BotFather** → `/newbot` → ponle nombre y un usuario que acabe en `bot`.
   Copia el **HTTP API token** (formato `123456789:AAporejemplo...`).
2. Crea un **grupo** en Telegram y **añade tu bot** a ese grupo. Envía un mensaje cualquiera al grupo.
3. Obtén el **Chat ID**: en el navegador abre
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   y busca en el JSON el campo `chat.id` (en grupos suele ser **negativo**, p. ej. `-1001234567890`;
   copia también el signo menos).

### 5.2 Crear el contact point (UI — funciona en Cloud y OSS)

*Alerting → Contact points → + Add contact point*
- **Name:** `telegram-santi-go`
- **Integration:** `Telegram`
- **BOT API Token:** tu token
- **Chat ID:** el ID del grupo (con el `-` si es negativo)
- *(Opcional)* **Message** — mensaje bonito en Telegram:
  ```
  {{ range .Alerts }}{{ if eq .Status "firing" }}🔴 ALERTA{{ else }}🟢 RESUELTO{{ end }} · Santi & Go
  {{ .Annotations.summary }}
  {{ end }}
  ```
- Pulsa **Test** (debe llegarte un mensaje de prueba al grupo) y **Save contact point**.

### 5.3 Crear la regla de alerta (UI)

*Alerting → Alert rules → + New alert rule*

1. **Nombre:** `Concello no apto para deporte`.
2. **Define query and alert condition** → activa **Advanced options** y selecciona tu **datasource Infinity**.
3. **Query A** (el truco multidimensional está aquí):
   - **Type:** `JSON` · **Source:** `URL` · **Parser:** `Backend` · **Format:** `Table`
   - **URL:** `http://localhost:5000/api/galicia/deporte`
     *(en Grafana Cloud pon aquí tu URL de **ngrok**, no `localhost` — ver nota 5.5)*
   - **Columns** (¡clave! solo UNA numérica):
     | Selector | Type |
     |---|---|
     | `ciudad` | **String** → será etiqueta |
     | `recomendacion` | **String** → será etiqueta |
     | `apto` | **Number** → valor a evaluar |
4. **Expresiones** — borra el `Reduce` que Grafana añade por defecto (con datos en tabla
   no hace falta y colapsaría las filas) y añade una expresión **Threshold**:
   - **Input:** `A` · **Condition:** `IS BELOW` · valor **`1`**
   - Marca esta expresión (`C`) como **alert condition**.

   > Por qué funciona: Grafana convierte cada fila de la tabla en una instancia de alerta.
   > Como `apto` es la única columna numérica, es el valor evaluado; `ciudad` y
   > `recomendacion` (texto) pasan a ser etiquetas. El umbral `apto < 1` deja en
   > **Alerting** solo las filas con `apto = 0` (no aptas) y en **Normal** las aptas.

5. **Evaluation behavior:** crea un *Evaluation group* (p. ej. `Santi & Go`) con intervalo
   `1m` y **Pending period** `0s` (aviso inmediato). *(Validado en pruebas reales: con
   intervalos más agresivos, como `10s`, el motor de alerting puede generar notificaciones
   incompletas al procesar muchas alertas a la vez; `1m` es estable.)*
6. **Configure labels and notifications:**
   - **Summary** (annotation):
     `⚠️ No apto para deporte en {{ $labels.ciudad }} — {{ $labels.recomendacion }}`
   - En **Notifications**, **Select contact point → `telegram-santi-go`**.
7. **Save rule and exit.** Para probar en seco, baja temporalmente algún umbral en
   `config.py` (p. ej. `UMBRAL_VIENTO_KMH = 1`) para forzar un "no apto" y ver llegar el mensaje.

### 5.4 (Bonus) Provisioning para Grafana local/OSS

Si corres Grafana self-hosted (Docker/local), tienes los ficheros listos en
`provisioning/alerting/`. Cópialos a `/etc/grafana/provisioning/alerting/`,
exporta el token y reinicia Grafana:

```bash
export TELEGRAM_BOT_TOKEN="123456789:AA..."
export TELEGRAM_CHAT_ID="-1001234567890"
# y sustituye <UID_INFINITY> en alert-rule-no-apto.yaml por el UID de tu datasource Infinity
```

En **Grafana Cloud** el provisioning por fichero no está disponible: usa la UI (5.2 y 5.3).
Si quieres versionar la config, créala por UI y luego usa **Export → Provisioning (YAML)**.

### 5.5 Nota importante para la alerta

La query de la alerta **no usa** la variable `$base_url` del dashboard (las reglas son
independientes del dashboard). Por eso la URL va escrita directamente en la Query A:
- **Grafana local:** `http://localhost:5000/...`
- **Grafana Cloud:** tu URL pública de **ngrok** (`https://...ngrok-free.dev/...`).

---

## 6. Notas técnicas (léelas, evitan dolores de cabeza)

### ⚠️ `localhost` vs Grafana Cloud — el punto más importante
El datasource Infinity usa el **parser backend** (`jq-backend`): **el servidor de Grafana**
hace la petición HTTP, no tu navegador.

- **Grafana local (OSS/Docker en tu PC):** `http://localhost:5000` funciona perfecto.
- **Grafana Cloud:** los servidores de Grafana **NO ven tu `localhost`** (por eso usabas ngrok).
  1. `ngrok http 5000`
  2. Copia la URL `https://....ngrok-free.dev`
  3. Pégala en la variable **`$base_url`** del dashboard **y** en la URL de la **Query A de la alerta**.

### CORS
Con el parser backend no hay problema de CORS (servidor→servidor). Aun así, el backend
incluye `flask-cors` activado como red de seguridad por si usas Infinity en modo *frontend*.

### Token de OpenWeather API
- Se pide registrándote en OpenWeather API.
- Va **solo** en `.env` (`OPENWEATHER_API_KEY`). Nunca en el código ni en git.
- Si ves `features` vacío o error 4xx, suele ser token inválido o coordenadas fuera de malla.

### Coordenadas
OpenWeather API espera `lat`/`lon` como parámetros separados. El cliente ya lo gestiona.

### Caché y rate-limit
`weather_client.py` cachea cada concello **10 min** (`CACHE_TTL_SECONDS`) y refresca todos en
paralelo (`MAX_WORKERS=6`). Como el dato cambia poco en ese margen de tiempo, no pierdes
frescura y evitas saturar la API. Ajusta ambos valores en `config.py`.

### Verificación del parseo
La respuesta JSON de OpenWeather API se parsea de forma defensiva (lee `main.temp`,
`rain.1h` y `wind.speed`; normaliza m/s → km/h). Si OpenWeather cambiara algún nombre de
campo, el único sitio a tocar es `weather_client.py`.

### Añadir concellos
Edita `CONCELLOS` en `config.py` y ejecuta `python generate_dashboard.py` para
regenerar el `dashboard.json` con la nueva lista en la variable `$municipio`.
