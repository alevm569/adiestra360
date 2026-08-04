# Fase 5 — Despliegue (Railway + PWA) y Validación

Guía operativa para desplegar Adiestra360 en Railway, exponerlo como PWA
instalable y correr la validación con usuarios reales + datos simulados.

> Todo el código queda listo para `git pull` en la máquina Windows. Los
> comandos de abajo se corren **allá** (donde sí hay entorno del backend y
> `npm install`), no en la máquina de desarrollo.

---

## 1. Despliegue en Railway

Dos servicios en el mismo proyecto: **backend** (Django) y **frontend** (PWA),
más un plugin **MySQL**.

### 1.1 Base de datos

Añade el plugin **MySQL** al proyecto. Railway crea las variables
`MYSQLDATABASE`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLHOST`, `MYSQLPORT`.

### 1.2 Servicio backend

- **Root Directory:** `adiestra360_backend`
- Railway detecta `requirements.txt` + `Procfile` (Nixpacks, Python 3.12 por
  `.python-version`). El `Procfile` corre migraciones, `collectstatic` y
  `gunicorn`.
- **Variables** (panel → Variables). Referencia el MySQL con `${{ MySQL.* }}`:

  ```
  SECRET_KEY            = <clave larga y aleatoria>
  DEBUG                 = False
  ALLOWED_HOSTS         = <backend>.up.railway.app
  CSRF_TRUSTED_ORIGINS  = https://<backend>.up.railway.app
  CORS_ALLOWED_ORIGINS  = https://<frontend>.up.railway.app
  SECURE_SSL_REDIRECT   = True
  VALIDATION_ADMIN_EMAILS = valery.villarruel569@gmail.com
  DB_NAME     = ${{ MySQL.MYSQLDATABASE }}
  DB_USER     = ${{ MySQL.MYSQLUSER }}
  DB_PASSWORD = ${{ MySQL.MYSQLPASSWORD }}
  DB_HOST     = ${{ MySQL.MYSQLHOST }}
  DB_PORT     = ${{ MySQL.MYSQLPORT }}
  ```

  `RAILWAY_PUBLIC_DOMAIN` se añade solo a `ALLOWED_HOSTS`/`CSRF` (ver
  `settings.py`), pero conviene fijar los dominios explícitos igualmente.

- El **catálogo y las técnicas se cargan solos** en cada arranque: el `Procfile`
  corre `loaddata adiestra360_backend/fixtures/initial_data.json` (niveles,
  ejercicios, refuerzos, logros) y `seed_techniques` (técnicas "cómo enseñar").
  Ambos son idempotentes, así que se pueden repetir sin duplicar.

### 1.3 Frontend (PWA) en Netlify — gratis

El frontend es estático, así que va en **Netlify** (plan gratis permanente, sin
tarjeta), no en Railway.

- Netlify → **Add new site → Import from GitHub** → el repo.
- **Base directory:** `adiestra360_frontend` · **Build:** `npm run build` ·
  **Publish:** `dist` (todo esto ya viene en `netlify.toml`).
- La URL del backend va en `adiestra360_frontend/.env.production` (la lee Vite en
  el build):

  ```
  VITE_API_URL=https://<backend>.up.railway.app/api
  ```

- `netlify.toml` maneja el fallback SPA a `index.html` (para que refrescar una
  ruta como `/perfil` no dé 404).
- **Importante:** en el backend de Railway, `CORS_ALLOWED_ORIGINS` debe incluir
  el dominio de Netlify (p. ej. `https://adiestra360.netlify.app`).

### 1.4 Comprobaciones post-deploy

- `https://<backend>/admin/` carga con estilos (WhiteNoise OK).
- La PWA abre, hace login y llega al backend (sin errores CORS en consola).
- En Chrome DevTools → Application → Manifest e **Instalar app** disponible;
  Service Worker activo y "offline" sirve el shell.

---

## 2. PWA (ya implementada)

- `vite-plugin-pwa` genera `sw.js` + `manifest.webmanifest` en el build web.
  El SW se registra **solo en web** (`main.tsx`); dentro de Capacitor nativo no.
- Manifest, iconos (`public/pwa-*.png`, favicons, apple-touch-icon) y metas en
  `index.html` listos. Cacheo offline del shell, fotos de técnicas y fuentes.
- **Instalación sin tienda:** el usuario abre la URL del frontend en el móvil y
  usa "Añadir a pantalla de inicio" (Android/Chrome muestra el prompt de
  instalación; iOS/Safari vía Compartir → Añadir a inicio).

---

## 3. Validación

### 3.1 Cuestionario SUS (dentro de la app)

- Cualquier usuario lo abre en **Perfil → Cuestionario de usabilidad**
  (`/validacion/encuesta`). Son los 10 ítems estándar del System Usability
  Scale (escala 1–5) en español, con comentario abierto opcional.
- Una respuesta por usuario (upsert). El puntaje SUS (0–100) se calcula solo.
- Endpoints: `GET/POST /api/validation/survey/`.

### 3.2 Datos simulados (complemento)

Genera usuarios/perros/sesiones/encuestas sintéticos, reproducibles y marcados
como simulados (email `@sim.adiestra360.local`):

```
python manage.py seed_validation                 # 15 usuarios, semilla 42
python manage.py seed_validation --users 20 --days 45
python manage.py seed_validation --clear         # borra los previos y regenera
```

Requiere el catálogo ya cargado (niveles/ejercicios/refuerzos). Con `--clear`
elimina en cascada todos los datos simulados anteriores.

### 3.3 Panel de métricas (solo admin)

- **Perfil → Panel de validación** (`/validacion/metricas`), visible solo para
  los emails de `VALIDATION_ADMIN_EMAILS`.
- Segmenta **Reales / Simulados / Todos**: tasa de éxito, sesiones, días
  activos, rachas, XP, ejercicios dominados, cumplimiento de criterios, resumen
  SUS (media, adjetivo, distribución, % sobre la media de industria 68) y tasa
  de éxito por ejercicio.
- La tarjeta **Usuarios con más de un perro** muestra el conteo de dueños con 2
  o más perros (`multi_dog_users`, `max_dogs_per_user`) y, al desplegarla,
  cómo leer cada media cuando la muestra los tiene.
- Endpoint: `GET /api/validation/metrics/`.

### 3.4 Exportación para el informe

```
python manage.py export_metrics --format csv  --output participantes.csv
python manage.py export_metrics --format json --output metricas.json
```

- **CSV:** una fila por participante (segmento, perro, sesiones, tasa de éxito,
  días activos, racha, XP, puntaje SUS, adjetivo, comentario).
- **JSON:** el payload agregado completo (igual que el panel).

### 3.5 Pruebas automáticas

```
python manage.py test validation
```

## 4. Recuperación de contraseña

Flujo público en `/recuperar` (enlace "¿Olvidaste tu contraseña?" en el login):
el usuario escribe su correo, recibe un **código de 6 dígitos** y lo usa junto
con la contraseña nueva. Se eligió código y no enlace porque la app corre como
PWA y como APK de Capacitor: un enlace del correo sacaría al usuario de la app
instalada.

- Endpoints: `POST /api/auth/password-reset/` y
  `POST /api/auth/password-reset/confirm/`.
- El código se guarda **hasheado**, es de un solo uso, caduca a los 15 minutos,
  muere tras 5 intentos fallidos y se invalida al pedir uno nuevo. Pedir código
  para un correo inexistente responde igual que para uno real (no se puede
  averiguar quién está registrado). Solo se envía un correo por minuto y correo.

### Configurar el envío (Gmail)

1. En la cuenta de Google que va a enviar: activar la **verificación en dos
   pasos** y crear una **contraseña de aplicación**
   (`myaccount.google.com/apppasswords`). Es una clave de 16 caracteres, **no**
   la contraseña normal de la cuenta.
2. Añadir estas variables en Render (Environment):

   ```
   EMAIL_HOST_USER      = tucorreo@gmail.com
   EMAIL_HOST_PASSWORD  = <contraseña de aplicación>
   DEFAULT_FROM_EMAIL   = Adiestra360 <tucorreo@gmail.com>
   ```

   `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587` y `EMAIL_USE_TLS=True` ya son
   los valores por defecto. Opcionales:
   `PASSWORD_RESET_CODE_TTL_MINUTES`, `PASSWORD_RESET_MAX_ATTEMPTS`,
   `PASSWORD_RESET_RESEND_SECONDS`.

3. En local, si `EMAIL_HOST_USER` está vacío el correo se **imprime en la
   consola** de `runserver`: el código se lee ahí y no hace falta SMTP.

Pruebas: `python manage.py test users`.

Cubre el scoring SUS, el upsert de la encuesta y el gateado por email del panel.

---

## 4. Resumen de lo nuevo en esta fase

**Backend — app `validation`:**
`models.py` (SUS `SurveyResponses`), `constants.py` (preguntas + scoring),
`serializers.py`, `permissions.py` (allowlist por email), `views.py`,
`metrics.py` (agregación real/simulado/combinado), `urls.py`, `admin.py`,
`tests.py`, migración `0001_initial`, y comandos `seed_validation` /
`export_metrics`. Wiring en `settings.py`, `urls.py` raíz y `UserSerializer`
(`is_metrics_admin`).

**Frontend — feature `validation`:**
`SurveyPage` (cuestionario SUS), `MetricsPage` (panel), `api.ts`, tipos, rutas y
accesos desde el perfil.
