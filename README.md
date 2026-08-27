# 🌤️ Santi & Go — Tiempo & Deporte en Galicia

Plataforma regional que conecta la API de **OpenWeatherMap** con **Grafana**
para responder de un vistazo: *¿es buen momento para hacer deporte al aire libre
en cualquier concello de Galicia?* — con **avisos automáticos por Telegram**.

- **Backend:** Python + Flask (modular), desplegado en **Render**
- **Datos:** OpenWeatherMap API (tiempo real)
- **Visualización:** Grafana Cloud + plugin **Infinity** (gauges, stats, tabla, medias y un **Geomap**)
- **Alertas:** Grafana Alerting → **Telegram** (alerta por concello no apto)
- **Keep-alive:** UptimeRobot (evita que el plan gratuito de Render hiberne el backend)

Enlaces del proyecto:

**📸 Vista pública del dashboard (snapshot, sin login):**
https://proudballoon610.grafana.net/dashboard/snapshot/SIqkgs6yfZ45g1eU8uCkRPb0yux9qU9i
*(instantánea fija para ver el aspecto del dashboard sin cuenta; los datos son del momento
en que se capturó, no se actualizan)*

**🌐 Dashboard en vivo (Grafana Cloud, con login):**
https://proudballoon610.grafana.net/d/santi-go-galicia
*(datos en tiempo real; puede requerir sesión de Grafana según la configuración de acceso)*

**Backend (Render):** https://santi-go.onrender.com

**📈 Estado del backend en vivo (UptimeRobot):** https://stats.uptimerobot.com/rhc92PF4VK

> Nota: el dashboard está alojado en el plan gratuito de Grafana Cloud y el backend en el
> plan gratuito de Render. Render "duerme" el servicio tras un rato de inactividad, así que
> la primera carga tras un tiempo parado puede tardar ~30–50 s en responder (luego va fluido).

---

## 1. Arquitectura

```
santi-go/
├── main.py                        # Punto de entrada Flask (endpoints)
├── config.py                      # Token, umbrales y catálogo de concellos (lat/lon)
├── weather_client.py              # Cliente OpenWeather + cache
├── evaluator.py                   # Lógica "apto / no apto" (pura, testeable)
├── generate_dashboard.py          # Genera dashboard.json a partir del catálogo de concellos
├── dashboard.json                 # Dashboard BASE (8 paneles) generado por el script
├── dashboard_export_completo.json # Dashboard COMPLETO (13 paneles) exportado de Grafana
├── provisioning/
│   └── alerting/
│       ├── contact-point-telegram.yaml
│       └── alert-rule-no-apto.yaml
├── requirements.txt
├── .env.example                   # Plantilla del token (copiar a .env)
├── .gitignore
└── test_local.py                  # Pruebas sin gastar llamadas a la API
```

### 📊 Los dos archivos de dashboard

El repo incluye **dos** definiciones de dashboard, y conviene saber cuál usar:

| Archivo | Paneles | Cómo se mantiene | Cuándo usarlo |
|---|---|---|---|
| `dashboard.json` | **8** (base): cabecera, Concello, ¿Apto?, Recomendación, 3 gauges y Geomap | Se **genera** con `generate_dashboard.py` a partir del catálogo de `config.py` | Punto de partida / regenerar tras cambiar concellos |
| `dashboard_export_completo.json` | **13** (completo): los 8 anteriores **+ tabla por concello + 3 medias de Galicia + piechart de aptos** | Exportado directamente **desde Grafana** (los paneles extra se añadieron por UI) | **Importar la versión completa** tal cual en Grafana Cloud / OSS |

> **Para ver el dashboard tal como está en producción, importa `dashboard_export_completo.json`.**
> El `dashboard.json` es la base reproducible desde código; los paneles de tabla y medias
> todavía no están portados a `generate_dashboard.py` (mejora pendiente), por eso existe el
> export completo como fuente de la versión final.

**Decisión clave de diseño:** un único endpoint que centraliza la lógica de negocio.

| Petición | Devuelve | Lo consume |
|---|---|---|
| `GET /api/galicia/deporte` | **Todos** los concellos (array) | El **Geomap**, la **tabla**, las **medias**, el **piechart** y la **alerta** |
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

---

## 2. Despliegue del backend

### 2.1 En local (desarrollo)

> Comandos para **Windows / PowerShell**. Entre paréntesis, el equivalente Linux/Mac.

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

### 2.2 En producción (Render)

El backend está desplegado en **Render** como servicio web, lo que lo hace público y
accesible 24/7 sin necesidad de tener el PC encendido. A grandes rasgos:

1. Conecta el repositorio de GitHub a Render (New → Web Service).
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** el que arranque tu app (p. ej. `gunicorn main:app` o `python main.py`).
4. Añade la variable de entorno **`OPENWEATHER_API_KEY`** en el panel de Render
   (Environment). **Nunca** subas el token al repo.
5. Render te da una URL pública tipo `https://santi-go.onrender.com`, que es la que
   consumen tanto el dashboard (`$base_url`) como la alerta.

> Plan gratuito: el servicio se suspende tras un periodo de inactividad y la primera
> petición lo "despierta" (~30–50 s). Es normal, no es un fallo.
> La raíz `/` devuelve un JSON de bienvenida con la descripción del servicio y la lista
> de endpoints disponibles; los datos están en `/api/galicia/deporte` y el estado en `/health`.

> 💡 **Evitar la hibernación (keep-alive):** para que el backend no se suspenda y responda
> siempre rápido, un monitor de [UptimeRobot](https://uptimerobot.com) hace una petición HTTP
> periódica (cada ~5 min) a `https://santi-go.onrender.com`. Así Render nunca llega al periodo
> de inactividad que dispara la suspensión, y el dashboard carga al instante desde el móvil.
> El estado del backend es público: **https://stats.uptimerobot.com/rhc92PF4VK**
> *(Nota: mantener despierto un servicio del plan gratuito consume más horas de cómputo; para
> un uso personal suele quedar dentro del margen mensual.)*

---

## 3. Importar el dashboard en Grafana

> Estos pasos valen tanto para **Grafana Cloud** como para **Grafana local (OSS)**.

1. **Instala el plugin Infinity** (si no lo tienes):
   *Connections → Add new connection → busca **Infinity** (`yesoreyeram-infinity-datasource`) → Install.*
2. **Crea el datasource Infinity:**
   *Connections → Data sources → Add → Infinity.* Déjalo por defecto y **Save & test**.
3. **Importa el dashboard:**
   *Dashboards → New → Import → Upload JSON file →* selecciona
   **`dashboard_export_completo.json`** (versión completa con tabla, medias y piechart).
   *(Si solo quieres la versión base reproducible desde código, usa `dashboard.json`.)*
4. En la pantalla de import te pedirá el datasource: **elige tu Infinity**.
   Si vas a reemplazar un dashboard existente, deja el **UID** en `santi-go-galicia` para
   que lo sobrescriba en vez de crear un duplicado.
5. Arriba verás dos controles: **Concello** (`$municipio`) y **URL del backend** (`$base_url`).
   - En **Grafana Cloud**, pon `$base_url` = `https://santi-go.onrender.com`.
   - En **Grafana local**, puedes usar `http://localhost:5000` si corres el backend en tu PC.

> **Importante — usa siempre `$base_url` en las queries de los paneles.** Todos los paneles
> deben construir su URL como `${base_url}/api/galicia/deporte`, nunca con `localhost` escrito
> a mano. Si un panel tiene la URL fija a `http://localhost:5000`, funcionará en tu PC pero
> saldrá **vacío** en Grafana Cloud (allí `localhost` no es tu backend). El
> `dashboard_export_completo.json` de este repo ya está corregido para usar `${base_url}` en
> todos los paneles.

---

## 4. Geomap: qué campos usar

El panel Geomap ya viene configurado, pero estos son los campos que lo hacen funcionar:

- **Base layer:** `Open Street Map`
  *(evita el basemap por defecto de CARTO: desde 2025 exige API key y muestra una marca de
  agua "API KEY REQUIRED" sobre el mapa. OpenStreetMap es gratuito y sin key.)*
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
- *(Opcional)* **Message** — mensaje bonito en Telegram, con una línea por alerta
  (usa las etiquetas directamente para que ciudad y motivo salgan siempre):
  ```
  {{ range .Alerts.Firing }}🔴 ALERTA · Santi & Go
  Estado del deporte en {{ .Labels.ciudad }}: {{ .Labels.recomendacion }}
  {{ end }}{{ range .Alerts.Resolved }}🟢 RESUELTO · Santi & Go
  Estado del deporte en {{ .Labels.ciudad }}: ¡Ideal para deporte!
  {{ end }}
  ```
- Pulsa **Test** (debe llegarte un mensaje de prueba al grupo) y **Save contact point**.

### 5.3 Crear la regla de alerta (UI)

*Alerting → Alert rules → + New alert rule*

1. **Nombre:** `Concello no apto para deporte`.
2. **Define query and alert condition** → activa **Advanced options** y selecciona tu **datasource Infinity**.
3. **Query A** (el truco multidimensional está aquí):
   - **Type:** `JSON` · **Source:** `URL` · **Parser:** `Backend` · **Format:** `Table`
   - **URL:** `https://santi-go.onrender.com/api/galicia/deporte`
     *(la alerta NO usa la variable `$base_url` del dashboard — ver nota 5.5 — así que la URL
     va escrita directa. En local sería `http://localhost:5000/api/galicia/deporte`.)*
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
6. **Agrupación por concello** (para recibir **un mensaje por concello**, no todos juntos):
   en la propia regla, dentro de *Silencio, agrupación y temporización*, activa
   **Anular agrupación** y añade las etiquetas `grafana_folder`, `alertname`, `ciudad`.
   Activa también **Anular tiempos** con: *Group wait* `0s`, *Group interval* `1m`,
   *Repeat interval* `1h`. *(Alternativa equivalente: añadir `ciudad` al "Group by" de la
   Notification policy por defecto en Alerting → Notification policies.)*
7. **Configure labels and notifications:**
   - **Summary** (annotation):
     `⚠️ No apto para deporte en {{ $labels.ciudad }} — {{ $labels.recomendacion }}`
   - En **Notifications**, **Select contact point → `telegram-santi-go`**.
8. **Save rule and exit.** Para probar en seco, baja temporalmente algún umbral en
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
- **Grafana Cloud:** tu URL pública de Render (`https://santi-go.onrender.com/...`).
- **Grafana local:** `http://localhost:5000/...`.

---

## 6. Notas técnicas (léelas, evitan dolores de cabeza)

### ⚠️ `localhost` vs Grafana Cloud — el punto más importante
El datasource Infinity usa el **parser backend**: **el servidor de Grafana** hace la
petición HTTP, no tu navegador. Por tanto el backend tiene que ser accesible desde internet.

- **Grafana local (OSS/Docker en tu PC):** `http://localhost:5000` funciona perfecto.
- **Grafana Cloud:** los servidores de Grafana **NO ven tu `localhost`**. La solución es tener
  el backend desplegado en un servicio público — en este proyecto, **Render**
  (`https://santi-go.onrender.com`). Pega esa URL en la variable **`$base_url`** del dashboard
  **y** en la URL de la **Query A de la alerta**.

  *(Durante el desarrollo también puede usarse un túnel como ngrok apuntando a tu localhost,
  pero Render es la opción estable y permanente, y no depende de tener el PC encendido.)*

> Aprendido a base de depuración: los paneles añadidos por UI (tabla, medias, piechart)
> tenían la URL escrita como `http://localhost:5000/...` en vez de `${base_url}/...`. En
> local funcionaban, pero al llevarlos a Grafana Cloud salían vacíos. La versión de
> `dashboard_export_completo.json` de este repo ya está corregida.

### CORS
Con el parser backend no hay problema de CORS (servidor→servidor). Aun así, el backend
incluye `flask-cors` activado como red de seguridad por si usas Infinity en modo *frontend*.

### Token de OpenWeather API
- Se pide registrándote en OpenWeather API.
- Va **solo** en `.env` (`OPENWEATHER_API_KEY`) en local, y como **variable de entorno en
  Render** en producción. Nunca en el código ni en git.
- Si ves error 401, suele ser token inválido o una clave recién creada aún sin activar
  (las claves nuevas de OpenWeather tardan desde minutos hasta ~2 h en activarse).

### Coordenadas
OpenWeather API espera `lat`/`lon` como parámetros separados. El cliente ya lo gestiona.

### Caché y rate-limit
`weather_client.py` cachea cada concello **10 min** (`CACHE_TTL_SECONDS`) y refresca todos en
paralelo (`MAX_WORKERS=6`). Como el dato cambia poco en ese margen de tiempo, no pierdes
frescura y evitas saturar la API. Ajusta ambos valores en `config.py`.

> **¿Por qué el backend local y el de Render muestran valores ligeramente distintos?**
> Son **backends independientes con cachés separadas**: cada uno consultó OpenWeather en un
> instante distinto, y el tiempo real cambia entre una consulta y otra. Por eso el dashboard
> que apunta a `localhost` y el que apunta a Render pueden marcar, por ejemplo, 15.8 °C vs
> 15.4 °C a la vez. **Es esperado, no un error.** Si necesitas datos idénticos en dos
> dashboards, haz que **ambos apunten al mismo backend** (misma `$base_url`).

### Verificación del parseo
La respuesta JSON de OpenWeather API se parsea de forma defensiva (lee `main.temp`,
`rain.1h` y `wind.speed`; normaliza m/s → km/h). Si OpenWeather cambiara algún nombre de
campo, el único sitio a tocar es `weather_client.py`.

### Añadir concellos
Edita `CONCELLOS` en `config.py` y ejecuta `python generate_dashboard.py` para
regenerar el `dashboard.json` con la nueva lista en la variable `$municipio`.

> Nota: `generate_dashboard.py` regenera únicamente los **8 paneles base**. Los paneles
> extra (tabla, medias, piechart) se añadieron por la UI de Grafana y viven en
> `dashboard_export_completo.json`. Si añades concellos y quieres la versión completa
> actualizada, tras regenerar habría que volver a incorporar esos paneles (mejora pendiente:
> portarlos al script para tener una única fuente de verdad).
