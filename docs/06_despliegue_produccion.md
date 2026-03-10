# 06 — Despliegue en Producción

> **Proyecto:** InfoSENA — Red social institucional SENA  
> **Stack:** Django 5.2.8 + MySQL + Redis + Channels + Daphne  
> **Requisito previo:** Manuales 01-05 completados, proyecto funcionando en local

---

## Tabla de Contenidos

1. [Resumen de estrategias de despliegue](#1-resumen-de-estrategias-de-despliegue)
2. [Pendientes críticos antes del despliegue](#2-pendientes-críticos-antes-del-despliegue)
3. [Preparar el proyecto para producción](#3-preparar-el-proyecto-para-producción)
4. [Opción A — Despliegue en Railway (Recomendado)](#4-opción-a--despliegue-en-railway-recomendado)
5. [Opción B — Despliegue en VPS (Alternativa)](#5-opción-b--despliegue-en-vps-alternativa)
6. [Variables de entorno de producción](#6-variables-de-entorno-de-producción)
7. [Configuración de CORS y seguridad](#7-configuración-de-cors-y-seguridad)
8. [Archivos estáticos y media en producción](#8-archivos-estáticos-y-media-en-producción)
9. [Validación final del despliegue](#9-validación-final-del-despliegue)
10. [Errores comunes en producción](#10-errores-comunes-en-producción)
11. [Mantenimiento post-despliegue](#11-mantenimiento-post-despliegue)
12. [Checklist final](#12-checklist-final)

---

## 1. Resumen de estrategias de despliegue

InfoSENA es una aplicación **Django monolítica con WebSockets**. No tiene frontend separado — Django sirve todo (HTML, CSS, JS, API). Esto simplifica el despliegue pero requiere soporte para WebSockets (ASGI).

| Opción | Plataforma | Pros | Contras | Costo |
|---|---|---|---|---|
| **A (Recomendada)** | **Railway** | Fácil, MySQL/Redis integrados, Procfile | Plan gratuito limitado | ~$5/mes |
| **B (Alternativa)** | **VPS (DigitalOcean/Contabo)** | Control total, sin límites | Requiere configuración manual | $5-12/mes |

### ¿Por qué Railway y no otra plataforma?

Se evaluaron 5 plataformas populares. Railway es la que mejor se adapta al stack de InfoSENA (Django + MySQL + Redis + WebSockets):

| Característica | Railway | Render | Heroku | Fly.io | Vercel |
|---|---|---|---|---|---|
| **Soporte Python/Django** | ✅ Nativo | ✅ Nativo | ✅ Nativo | ✅ Docker | ❌ No soporta |
| **MySQL integrado** | ✅ Addon 1-click | ❌ Solo PostgreSQL | ✅ Addon pago | ❌ Externo | ❌ No tiene |
| **Redis integrado** | ✅ Addon 1-click | ✅ Pago (~$10/mes) | ✅ Addon pago | ✅ Upstash | ❌ No tiene |
| **WebSockets (ASGI)** | ✅ Sin config extra | ✅ Funciona | ⚠️ Timeout 55s | ✅ Funciona | ❌ No soporta |
| **Lee Procfile** | ✅ Automático | ✅ Automático | ✅ Automático | ❌ Usa Dockerfile | ❌ No aplica |
| **Deploy desde GitHub** | ✅ Automático | ✅ Automático | ✅ Automático | ✅ Manual/CLI | ✅ Automático |
| **Variables de entorno** | ✅ Panel visual | ✅ Panel visual | ✅ Panel visual | ✅ CLI/Panel | ✅ Panel visual |
| **SSL/HTTPS gratis** | ✅ Automático | ✅ Automático | ✅ Automático | ✅ Automático | ✅ Automático |
| **Dominio personalizado** | ✅ Gratis | ✅ Gratis | ✅ Gratis | ✅ Gratis | ✅ Gratis |
| **Logs en tiempo real** | ✅ Panel web | ✅ Panel web | ✅ CLI/Panel | ✅ CLI | ❌ Limitado |
| **Costo mínimo** | ~$5/mes | ~$7-19/mes | ~$10/mes | ~$5/mes | No compatible |

#### ¿Por qué se descartan las demás?

| Plataforma | Razón de descarte |
|---|---|
| **Vercel** | ❌ No soporta Django ni backends Python con WebSockets. Es para frontend (React, Next.js, etc.) |
| **Heroku** | ⚠️ Funciona, pero los WebSockets tienen timeout de 55 segundos. El chat se desconectaría. Además es más caro (~$10/mes mínimo con addons). |
| **Render** | ⚠️ No tiene MySQL nativo — solo PostgreSQL. Migrar tu BD de MySQL a PostgreSQL requiere cambios en el código y en los datos. Redis es un servicio pago aparte (~$10/mes). Costo total más alto. |
| **Fly.io** | ⚠️ Requiere Docker (no soporta Procfile). Configuración más compleja. No tiene MySQL integrado — tendrías que usar un servicio externo como PlanetScale. |

#### Resumen: ¿Por qué Railway gana?

1. **MySQL con 1 click** — Tu proyecto usa MySQL con PyMySQL. Railway crea MySQL como addon sin cambiar nada de tu código.
2. **Redis con 1 click** — Necesario para el chat en tiempo real. En Railway es un addon instantáneo.
3. **WebSockets sin límites** — Heroku corta la conexión a los 55 segundos; Railway no tiene ese límite.
4. **Procfile compatible** — Railway lee tu Procfile directamente, sin necesidad de Dockerfile.
5. **Despliegue automático** — Cada `git push` a `main` redespliega automáticamente.
6. **Costo razonable** — ~$5/mes por los 3 servicios (app + MySQL + Redis) es el más económico.
7. **Simplicidad** — No necesitas saber Linux, Nginx, ni Docker. Todo se configura desde el panel web.

### ¿Cuándo elegir VPS en su lugar?

- Si necesitas **control total** del servidor (configurar Nginx, firewall, etc.)
- Si tienes **más de 100 usuarios concurrentes** en el chat (Railway puede quedar corto de RAM)
- Si quieres **aprender administración de servidores Linux**
- Si prefieres **no depender** de una plataforma PaaS
- Si necesitas **más de 1 GB de almacenamiento** para archivos media

---

## 2. Pendientes críticos antes del despliegue

Antes de desplegar, hay **problemas que deben resolverse**. Sin estos cambios, el proyecto **no funcionará correctamente** en producción.

### 2.1. Corregir asgi.py para WebSockets

**Problema:** El archivo `info/info/asgi.py` actual es básico y **no tiene configuración de Channels/WebSocket routing**. El chat no funcionará en producción.

**Archivo actual:**
```python
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'info.settings')
application = get_asgi_application()
```

**Archivo corregido (reemplazar todo el contenido de `info/info/asgi.py`):**

```python
"""
ASGI config for info project.
Configures HTTP + WebSocket routing for Django Channels.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'info.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from applications.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
```

**¿Qué hace este cambio?**
- `ProtocolTypeRouter` → Separa peticiones HTTP de WebSocket
- `AuthMiddlewareStack` → Permite que los WebSockets accedan al usuario autenticado
- `URLRouter(websocket_urlpatterns)` → Conecta las rutas de WebSocket definidas en `chat/routing.py`

### 2.2. Corregir Procfile para ASGI

**Problema:** El Procfile actual usa `gunicorn` (servidor WSGI) que **no soporta WebSockets**. El chat necesita `daphne` (servidor ASGI).

**Archivo actual:**
```
web: gunicorn info.wsgi
```

**Archivo corregido (reemplazar contenido de `info/Procfile`):**

```
web: daphne -b 0.0.0.0 -p $PORT info.asgi:application
```

**¿Qué hace este cambio?**
- `daphne` → Servidor ASGI que soporta HTTP + WebSocket
- `-b 0.0.0.0` → Escucha en todas las interfaces (necesario en producción)
- `-p $PORT` → Usa el puerto que la plataforma asigne (Railway, Heroku, etc.)
- `info.asgi:application` → Usa la configuración ASGI en lugar de WSGI

### 2.3. Agregar WhiteNoise para archivos estáticos

En producción, Django **no sirve archivos estáticos** (CSS, imágenes) por defecto. Necesitas **WhiteNoise** o un servidor como Nginx.

**Paso 1:** Agregar a `requirements.txt`:

```
whitenoise==6.8.2
```

**Paso 2:** Instalar:

```cmd
pip install whitenoise==6.8.2
```

**Paso 3:** Agregar al middleware en `settings.py` (después de SecurityMiddleware):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Agregar esta línea
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... resto del middleware
]
```

**Paso 4:** Agregar configuración en `settings.py`:

```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Paso 5:** Recolectar archivos estáticos:

```cmd
python manage.py collectstatic --noinput
```

---

## 3. Preparar el proyecto para producción

### 3.1. Configurar settings.py para producción

Agrega estas configuraciones al final de `info/info/settings.py` (se activan solo cuando `DEBUG=False`):

```python
# ---- CONFIGURACIÓN DE PRODUCCIÓN ----
if not DEBUG:
    # Seguridad
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
```

### 3.2. Generar una SECRET_KEY segura para producción

**Nunca uses la SECRET_KEY de desarrollo en producción.** Genera una nueva:

```cmd
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado y úsalo como `SECRET_KEY` en las variables de entorno de producción.

### 3.3. Actualizar requirements.txt

Asegúrate de que `requirements.txt` incluye todo lo necesario.

> ⚠️ **IMPORTANTE:** Tu `requirements.txt` actual **no incluye Pillow ni WhiteNoise**. Sin Pillow, las subidas de fotos de perfil y archivos fallarán en producción. Sin WhiteNoise, el CSS no cargará.

**Archivo `requirements.txt` completo para producción:**

```
asgiref==3.10.0
Django==5.2.8
gunicorn==23.0.0
packaging==25.0
PyMySQL==1.1.2
sqlparse==0.5.3
tzdata==2025.2
channels==4.0.0
channels-redis==4.1.0
redis==5.0.1
daphne==4.0.0
python-dateutil==2.8.2
openai>=1.0.0
python-dotenv
whitenoise==6.8.2
Pillow==11.1.0
```

**¿Qué se agregó y por qué?**

| Paquete | ¿Estaba? | ¿Por qué es necesario? |
|---|---|---|
| `whitenoise` | ❌ No | Servir archivos estáticos (CSS, imágenes) en producción |
| `Pillow` | ❌ No | Procesar `ImageField` en Django (fotos de perfil, fotos de grupo, archivos de publicaciones) |

**Instalar las dependencias nuevas localmente:**

```cmd
pip install whitenoise==6.8.2 Pillow==11.1.0
```

### 3.4. Crear runtime.txt (para Railway/Heroku)

Crea `info/runtime.txt`:

```
python-3.13.5
```

Esto le indica a la plataforma qué versión de Python usar.

### 3.5. Commit y push de todos los cambios

```cmd
cd info
git add .
git commit -m "chore: preparar proyecto para despliegue en producción"
git push origin main
```

---

## 4. Opción A — Despliegue en Railway (Recomendado)

### 4.1. Crear cuenta en Railway

1. Ve a [https://railway.app](https://railway.app)
2. Click en **"Login"** → **"Login with GitHub"**
3. Autoriza a Railway para acceder a tu cuenta de GitHub
4. Completa el registro

### 4.2. Crear un nuevo proyecto

1. En el dashboard de Railway, click en **"+ New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Busca tu repositorio **"infosena"** y selecciónalo
4. Railway detectará automáticamente que es un proyecto Python


### 4.3. Agregar MySQL (Railway)

Railway facilita la integración de MySQL generando automáticamente las variables de entorno necesarias. Sigue estos pasos:

#### Paso 1: Agregar el plugin de MySQL
1. Entra a tu proyecto en Railway (web).
2. Haz clic en “Add Plugin” o “Agregar plugin”.
3. Selecciona “MySQL”.
4. Espera a que Railway cree la base de datos.

#### Paso 2: Ubica las variables de entorno
Railway agregará variables como estas (los valores serán diferentes en tu proyecto):

```
MYSQLDATABASE=railway
MYSQLHOST=mysql.railway.internal
MYSQLPORT=3306
MYSQLUSER=root
MYSQLPASSWORD=contraseña_generada
```

#### Paso 3: Configura tu archivo `.env` (opcional para pruebas locales)
Agrega estas líneas a tu `.env` local:

```
DB_NAME=railway
DB_USER=root
DB_PASSWORD=contraseña_generada
DB_HOST=mysql.railway.internal
DB_PORT=3306
```

#### Paso 4: Configura `settings.py` en Django
Asegúrate de que tu archivo `settings.py` use las variables de entorno:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

#### Nota
- En Railway, no necesitas modificar nada: las variables ya están disponibles para tu app.
- Si usas otro nombre de variable, asegúrate de mapearlo correctamente en tu `.env` y en `settings.py`.
- Railway permite referenciar variables de otros servicios, por ejemplo: `${{MySQL.MYSQL_HOST}}`.

---
Esto garantiza que tu Django usará la base de datos MySQL de Railway tanto en producción como en pruebas locales (si copias las variables a tu `.env`).


### 4.4. Agregar Redis (Railway)

Redis es necesario para el chat y tareas en tiempo real. Railway permite agregarlo fácilmente:

#### Paso 1: Agregar el plugin de Redis
1. Entra a tu proyecto en Railway (web).
2. Haz clic en “Add Plugin” o “+ New” → “Database” → “Redis”.
3. Espera a que Railway cree la base de datos Redis.

#### Paso 2: Obtén la URL de conexión
1. Haz clic en el servicio Redis recién creado.
2. Ve a la pestaña “Variables”.
3. Copia el valor de la variable `REDIS_URL` (ejemplo: `redis://default:contraseña@redis.railway.internal:6379`).

#### Paso 3: Configura tu archivo `.env`
- **En producción (Railway):**
    - Pega la URL copiada en tu `.env` de Railway:
        ```
        REDIS_URL=redis://default:contraseña@redis.railway.internal:6379
        ```
        (Reemplaza por el valor real que te da Railway.)
- **En local:**
    - Si tienes Redis instalado en tu PC, usa:
        ```
        REDIS_URL=redis://127.0.0.1:6379
        ```
    - Si no usas Redis localmente, puedes dejarlo vacío o comentar la línea.

---
Esto asegura que tu Django usará Redis correctamente tanto en Railway como en desarrollo local.


### 4.5. Configurar variables de entorno

1. Haz clic en tu servicio web (el que tiene el código)
2. Ve a la pestaña **"Variables"**
3. Puedes agregar las variables una por una, o usar el **Raw Editor** para pegarlas todas de una vez (opcional y recomendado):

#### Opción rápida: Raw Editor

1. Haz clic en **Raw Editor** (arriba a la derecha en la pestaña Variables).
2. Borra lo que haya (si quieres empezar limpio) y pega este bloque (ajusta los valores según tu proyecto):

```env
SECRET_KEY=django-insecure-h2*$b!#5upbewe)h)c0s074)!675xs#zj4sj$sx3yd*bn55k!1
DEBUG=False

# ¡IMPORTANTE!
# Debes agregar exactamente el dominio generado por Railway a ALLOWED_HOSTS para evitar errores 400 (DisallowedHost).
# Ejemplo:
ALLOWED_HOSTS=web-production-6b79c.up.railway.app,infosena.site

# Si tu dominio cambia, actualiza este valor. Puedes ver el dominio en la parte superior de tu servicio web en Railway.

# Base de datos (Railway)
DB_NAME=railway
DB_USER=root
DB_PASSWORD=rtHncHhNyLzxAqSKEQdIPEEkxVVIuEky
DB_HOST=mysql.railway.internal
DB_PORT=3306

# Redis (Railway)
REDIS_URL=redis://default:iRvoiOLLexvDuoshytwNheoIlwbudVPf@redis.railway.internal:6379

# Email
EMAIL_HOST_USER=perezpolancocarlosmario@gmail.com
EMAIL_HOST_PASSWORD=zdotpwzoijuwwsts

# APIs
OPENAI_API_KEY=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
PERSPECTIVE_API_KEY=AIzaSyClFIfrYfiMOtH3nDTgBtYNSxS08en0fH4

PORT=8000
```

> **Nota:** Cambia los valores de las claves y contraseñas por los de tu proyecto. El valor de `ALLOWED_HOSTS` debe incluir el dominio de Railway y cualquier dominio personalizado que uses.

---
También puedes seguir agregando variables una por una si lo prefieres.

> **Tip:** Railway permite referenciar variables de otros servicios. Puedes usar `${{MySQL.MYSQL_HOST}}` como valor para `DB_HOST`.

### 4.6. Configurar el build y deploy

1. En tu servicio web → **"Settings"**
2. Verifica:

| Campo | Valor |
|---|---|
| **Root Directory** | `/info` (o la ruta donde está manage.py) |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| **Start Command** | (se lee del Procfile automáticamente) |

> Si Railway no detecta el Procfile, configura el Start Command manualmente:
> ```
> daphne -b 0.0.0.0 -p $PORT info.asgi:application
> ```

### 4.7. Desplegar

1. Railway despliega automáticamente cuando detecta cambios en tu rama `main`
2. Ve a **"Deployments"** para ver el progreso
3. Los logs te mostrarán si hay errores

### 4.8. Dominio personalizado (opcional)

1. En **"Settings"** → **"Networking"** → **"Public Networking"**
2. Click en **"Generate Domain"** para obtener un dominio `.up.railway.app`
3. O agrega tu dominio personalizado (ej: `infosena.site`):
   - Agrega un registro CNAME en tu proveedor de dominio apuntando a Railway
   - Railway configura SSL automáticamente

---

## 5. Opción B — Despliegue en VPS (Alternativa)

### 5.1. Contratar un VPS

Opciones recomendadas:

| Proveedor | Plan mínimo | Costo |
|---|---|---|
| **DigitalOcean** | Droplet básico (1 GB RAM, 1 vCPU) | $6/mes |
| **Contabo** | VPS S (4 GB RAM, 2 vCPU) | €5.5/mes |
| **Linode** | Nanode (1 GB RAM) | $5/mes |
| **Hetzner** | CX22 (2 GB RAM) | €3.5/mes |

Recomendado: **Ubuntu 22.04 LTS** como sistema operativo.

### 5.2. Configurar el servidor

**Conectarse por SSH:**

```bash
ssh root@IP_DEL_SERVIDOR
```

**Actualizar el sistema:**

```bash
sudo apt update && sudo apt upgrade -y
```

**Instalar dependencias del sistema:**

```bash
sudo apt install python3 python3-pip python3-venv nginx mysql-server redis-server git supervisor -y
```

### 5.3. Configurar MySQL en el VPS

```bash
sudo mysql_secure_installation
sudo mysql -u root -p
```

```sql
CREATE DATABASE infosena_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'infosena_user'@'localhost' IDENTIFIED BY 'UnaContraseñaSegura123!';
GRANT ALL PRIVILEGES ON infosena_db.* TO 'infosena_user'@'localhost';
FLUSH PRIVILEGES;
exit
```

### 5.4. Configurar Redis en el VPS

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping  # Debe responder PONG
```

### 5.5. Clonar el proyecto

```bash
cd /home
git clone https://github.com/TU_USUARIO/infosena.git
cd infosena
```

### 5.6. Configurar entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5.7. Crear archivo .env

```bash
nano .env
```

Llena con los valores de producción (ver sección 6).

### 5.8. Ejecutar migraciones y recolectar estáticos

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 5.9. Configurar Supervisor (gestión de procesos)

Supervisor mantiene Daphne corriendo y lo reinicia si se cae.

Crear archivo de configuración:

```bash
sudo nano /etc/supervisor/conf.d/infosena.conf
```

```ini
[program:infosena]
command=/home/infosena/venv/bin/daphne -b 0.0.0.0 -p 8000 info.asgi:application
directory=/home/infosena
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/infosena/app.log
environment=
    DJANGO_SETTINGS_MODULE="info.settings"
```

```bash
sudo mkdir -p /var/log/infosena
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start infosena
```

### 5.10. Configurar Nginx (proxy reverso)

Nginx recibe las peticiones de internet y las redirige a Daphne. También maneja SSL (HTTPS).

```bash
sudo nano /etc/nginx/sites-available/infosena
```

```nginx
upstream infosena_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name infosena.site www.infosena.site;  # Tu dominio

    client_max_body_size 20M;

    location /static/ {
        alias /home/infosena/staticfiles/;
    }

    location /media/ {
        alias /home/infosena/media/;
    }

    location / {
        proxy_pass http://infosena_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

> **Líneas clave para WebSockets:**  
> `proxy_set_header Upgrade $http_upgrade;` y `proxy_set_header Connection "upgrade";`  
> Sin estas líneas, el chat NO funcionará.

```bash
sudo ln -s /etc/nginx/sites-available/infosena /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl restart nginx
```

### 5.11. Configurar SSL con Let's Encrypt (HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d infosena.site -d www.infosena.site
```

Sigue las instrucciones interactivas. Certbot configurará HTTPS automáticamente y renovará el certificado cada 90 días.

---

## 6. Variables de entorno de producción

| Variable | Valor de desarrollo | Valor de producción |
|---|---|---|
| `SECRET_KEY` | insecure-key... | (generar nueva con 50+ caracteres) |
| `DEBUG` | `True` | **`False`** |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `tu-dominio.com,tu-app.railway.app` |
| `DB_NAME` | `infosena_db` | (nombre dado por Railway o que creaste en VPS) |
| `DB_USER` | `root` | (usuario de producción, NO root) |
| `DB_PASSWORD` | `root` | (contraseña segura de producción) |
| `DB_HOST` | `localhost` | (host proporcionado por Railway o localhost en VPS) |
| `DB_PORT` | `3306` | (puerto proporcionado) |
| `REDIS_HOST` | `127.0.0.1` | (host proporcionado por Railway o localhost) |
| `REDIS_PORT` | `6379` | (puerto proporcionado) |
| `EMAIL_HOST_USER` | correo de prueba | correo de producción |
| `EMAIL_HOST_PASSWORD` | app password | app password de producción |
| `PERSPECTIVE_API_KEY` | clave de prueba | misma clave (o crear una nueva) |

> ⚠️ **NUNCA uses `DEBUG=True` en producción.** Expone información sensible del sistema.

> ⚠️ **NUNCA uses `ALLOWED_HOSTS = ["*"]` en producción.** Permite cualquier dominio acceder a tu app.

---

## 7. Configuración de CORS y seguridad

### ¿Se necesita CORS en este proyecto?

**No.** CORS (Cross-Origin Resource Sharing) solo es necesario cuando el frontend y el backend están en **dominios diferentes**. En InfoSENA, Django sirve todo desde el mismo dominio, así que no hay peticiones cross-origin.

Si en el futuro se añade un frontend separado (React, Vue, etc.), necesitarás `django-cors-headers`.

### Configuración de seguridad para producción

Las siguientes configuraciones ya se agregaron en la sección 3.1, pero aquí está el resumen:

| Configuración | Valor | Propósito |
|---|---|---|
| `DEBUG` | `False` | No mostrar errores detallados al público |
| `SECURE_SSL_REDIRECT` | `True` | Redirigir HTTP → HTTPS |
| `SESSION_COOKIE_SECURE` | `True` | Cookies solo por HTTPS |
| `CSRF_COOKIE_SECURE` | `True` | Token CSRF solo por HTTPS |
| `SECURE_HSTS_SECONDS` | `31536000` | Forzar HTTPS por 1 año |
| `X_FRAME_OPTIONS` | `DENY` | Prevenir clickjacking |
| `SECURE_BROWSER_XSS_FILTER` | `True` | Protección XSS del navegador |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` | No adivinar tipo de contenido |

---

## 8. Archivos estáticos y media en producción

### Archivos estáticos (CSS, JS, imágenes del proyecto)

En producción, Django no sirve archivos estáticos. Las opciones son:

**Opción 1 — WhiteNoise (ya configurado en sección 2.3):**
- Django sirve los estáticos a través de WhiteNoise
- Es la opción más simple
- Suficiente para proyectos de tamaño mediano

**Recolectar estáticos (ejecutar antes de cada despliegue):**

```cmd
python manage.py collectstatic --noinput
```

Esto copia todos los archivos estáticos a la carpeta `staticfiles/`.

### Archivos media (fotos de perfil, archivos de chat, publicaciones)

Los archivos subidos por usuarios (media) son un tema aparte. En producción hay varias opciones:

**Opción 1 — Almacenamiento local (VPS):**
- Los archivos se guardan en el disco del servidor
- Simple pero limitado
- Si el servidor se cae, los archivos se pierden

**Opción 2 — Cloudinary (Recomendado para Railway):**
- Servicio de almacenamiento de imágenes/archivos en la nube
- Plan gratuito con 25 GB
- Se integra con Django via `django-cloudinary-storage`

> **Nota: Pendiente de implementar.** Actualmente el proyecto usa almacenamiento local. Para producción, se recomienda implementar almacenamiento en la nube antes del despliegue. Esto requiere:
> 1. Instalar `django-cloudinary-storage` o `django-storages` + boto3 (para S3)
> 2. Configurar los backends de almacenamiento en settings.py
> 3. Migrar los archivos existentes

**Opción 3 — AWS S3:**
- Más profesional y escalable
- Requiere cuenta de AWS
- Costo bajo para uso moderado

---

## 9. Validación final del despliegue

Después de desplegar, verifica que cada funcionalidad funcione:

### 9.1. Pruebas básicas

| # | Prueba | URL | Resultado esperado |
|---|---|---|---|
| 1 | Landing page | `https://tu-dominio.com/` | Se muestra la página de inicio |
| 2 | HTTPS | `http://tu-dominio.com/` | Redirige a HTTPS automáticamente |
| 3 | Admin | `https://tu-dominio.com/admin/` | Panel de administración de Django |
| 4 | Registro | `https://tu-dominio.com/registro/` | Formulario de registro visible |
| 5 | Login | `https://tu-dominio.com/sesion/login/` | Formulario de login visible |
| 6 | Archivos estáticos | (ver si CSS carga) | Página con estilos, no HTML plano |

### 9.2. Pruebas funcionales

| # | Prueba | Pasos | Resultado esperado |
|---|---|---|---|
| 1 | Registro completo | Registrar aprendiz → verificar código | Cuenta creada |
| 2 | Envío de email | Registrar usuario | Llega código al correo |
| 3 | Login | Ingresar con documento + contraseña | Acceso al feed |
| 4 | Chat WS | Abrir chat entre 2 usuarios | Mensajes en tiempo real |
| 5 | Moderación | Enviar mensaje ofensivo | Mensaje bloqueado |
| 6 | Publicaciones | Crear publicación (como Bienestar) | Post visible en feed |
| 7 | Amistades | Enviar solicitud de amistad | Notificación al receptor |
| 8 | Subida archivos | Subir foto de perfil | Imagen visible |

### 9.3. Verificar logs

**Railway:**
- Dashboard → Tu servicio → **"Deployments"** → Click en deployment → ver logs

**VPS:**
```bash
sudo tail -f /var/log/infosena/app.log
sudo tail -f /var/log/nginx/error.log
```

---

## 10. Errores comunes en producción

### Error: `DisallowedHost` / La página no carga

**Causa:** Tu dominio no está en `ALLOWED_HOSTS`.

**Solución:** Agrega tu dominio a la variable de entorno:
```
ALLOWED_HOSTS=tu-app.up.railway.app,tu-dominio.com
```

### Error: CSS / imágenes no cargan (página en HTML plano)

**Causa:** Archivos estáticos no configurados para producción.

**Solución:**
1. Verifica que WhiteNoise esté en MIDDLEWARE
2. Ejecuta `python manage.py collectstatic --noinput`
3. Verifica que `STATIC_ROOT` apunte a `staticfiles/`

### Error: WebSocket connection failed (chat no funciona)

**Causa 1:** `asgi.py` sin configuración de Channels.

**Solución:** Aplica el cambio del paso 2.1.

**Causa 2:** Nginx no está configurado para WebSockets.

**Solución:** Verifica que los headers `Upgrade` y `Connection` estén en la configuración de Nginx.

**Causa 3:** Redis no está disponible.

**Solución:** Verifica la conexión a Redis:
```bash
redis-cli -h HOST -p PORT ping
```

### Error: `OperationalError: (2003, "Can't connect to MySQL server")`

**Causa:** Las credenciales de MySQL son incorrectas o el servicio no está accesible.

**Solución:** Verifica las variables de entorno `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`.

### Error: `SMTPAuthenticationError` (correos no se envían)

**Causa:** La contraseña de app de Gmail es incorrecta o expiró.

**Solución:**
1. Genera una nueva contraseña de app en Google
2. Actualiza la variable `EMAIL_HOST_PASSWORD`

### Error: `Server Error (500)` sin detalles

**Causa:** `DEBUG=False` oculta los errores (comportamiento correcto en producción).

**Solución:** Revisa los logs del servidor para ver el error real:
- Railway: Dashboard → Logs
- VPS: `sudo tail -f /var/log/infosena/app.log`

### Error: La app tarda en cargar o se queda cargando

**Causa posible:** Migraciones pendientes o la BD no tiene datos.

**Solución:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 11. Mantenimiento post-despliegue

### Actualizar el código

**Railway (automático):**
```cmd
# En tu computadora local:
git add .
git commit -m "fix: corregir error en chat"
git push origin main
# Railway despliega automáticamente al detectar push a main
```

**VPS (manual):**
```bash
ssh root@IP_SERVIDOR
cd /home/infosena
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart infosena
```

### Backups de la base de datos

**Crear backup:**
```bash
# VPS
mysqldump -u infosena_user -p infosena_db > backup_$(date +%Y%m%d).sql

# Railway (exportar datos)
# Usa el panel de Railway → MySQL → Datos → Exportar
```

**Restaurar backup:**
```bash
mysql -u infosena_user -p infosena_db < backup_20260310.sql
```

### Monitoreo

| Qué monitorear | Herramienta | Para qué |
|---|---|---|
| Disponibilidad | UptimeRobot (gratis) | Te avisa si la app se cae |
| Errores | Sentry (gratis tier) | Captura errores de Python |
| Rendimiento | Railway metrics / htop | Ver uso de CPU y RAM |
| Logs | Logs de Railway o archivos de log | Debug de problemas |

---

## 12. Checklist Final

### Antes del despliegue

- [ ] `asgi.py` actualizado con ProtocolTypeRouter y Channels routing
- [ ] Procfile actualizado con Daphne en lugar de Gunicorn
- [ ] WhiteNoise instalado y configurado
- [ ] `requirements.txt` actualizado con todas las dependencias
- [ ] `runtime.txt` creado con la versión de Python
- [ ] `settings.py` lee variables de `.env` con `python-dotenv`
- [ ] Configuración de seguridad para producción (cuando `DEBUG=False`)
- [ ] `SECRET_KEY` nueva generada para producción
- [ ] Todos los cambios commiteados y pusheados a GitHub

### En la plataforma de despliegue

- [ ] Cuenta creada (Railway / VPS)
- [ ] MySQL configurado y accesible
- [ ] Redis configurado y accesible
- [ ] Variables de entorno configuradas (todas las del punto 6)
- [ ] Build completado sin errores
- [ ] App corriendo y accesible por URL

### Validación funcional

- [ ] Landing page carga con CSS y estilos
- [ ] HTTPS funciona (redirige de HTTP a HTTPS)
- [ ] Registro de usuario funciona
- [ ] Email de verificación llega
- [ ] Login funciona
- [ ] Feed/Home muestra contenido
- [ ] Chat en tiempo real funciona (WebSocket)
- [ ] Moderación de contenido funciona
- [ ] Subida de archivos funciona
- [ ] Admin de Django accesible

### Post-despliegue

- [ ] Superusuario creado en producción
- [ ] Monitoreo configurado (UptimeRobot o similar)
- [ ] Backup inicial de BD realizado
- [ ] Documentar las credenciales de producción en lugar seguro

---

## Pendientes antes del despliegue (resumen)

Estos son cambios que se recomiendan pero no están implementados actualmente:

| # | Pendiente | Prioridad | Estado |
|---|---|---|---|
| 1 | Almacenamiento en la nube para media (Cloudinary/S3) | Media | No implementado |
| 2 | Configuración de logging en producción | Media | No implementado |
| 3 | Tests automatizados | Baja | No implementado |
| 4 | CI/CD con GitHub Actions | Baja | No implementado |
| 5 | Template `dashboard.html` es placeholder minimal | Baja | Pendiente de desarrollo |
| 6 | Rate limiting para APIs | Media | No implementado |

---

> **Fin de la serie de manuales.**  
> Si completaste todos los pasos de los manuales 00 al 06, tu proyecto InfoSENA debería estar funcionando tanto en local como en producción.
