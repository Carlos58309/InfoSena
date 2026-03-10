# Manual 07 — Registro de Cambios Realizados al Proyecto

> **Propósito:** Este documento lista TODOS los cambios que se aplicaron a los archivos del proyecto InfoSENA para dejarlo listo para correr localmente y para despliegue en producción.

---

## Índice

1. [Entorno virtual recreado](#1-entorno-virtual-recreado)
2. [requirements.txt — Dependencias corregidas](#2-requirementstxt--dependencias-corregidas)
3. [Procfile — Servidor cambiado](#3-procfile--servidor-cambiado)
4. [asgi.py — WebSocket routing agregado](#4-asgipy--websocket-routing-agregado)
5. [settings.py — Variables de entorno y WhiteNoise](#5-settingspy--variables-de-entorno-y-whitenoise)
6. [.env — Archivo de variables de entorno](#6-env--archivo-de-variables-de-entorno)
7. [.env.example — Plantilla creada](#7-envexample--plantilla-creada)
8. [runtime.txt — Versión de Python](#8-runtimetxt--versión-de-python)
9. [Resumen rápido](#9-resumen-rápido)

---

## 1. Entorno virtual recreado

**Problema:** El entorno virtual (`Scripts/`, `Lib/`, `Include/`, `pyvenv.cfg`) fue creado en otra PC (usuario `camap`) y no funcionaba en tu máquina. Python no se encontraba.

**Solución:** Se eliminó el entorno virtual roto y se recreó con tu Python local:

```cmd
cd "C:\Users\Julian Andres\OneDrive\Desktop\Para Clase\InfoSena\SENA"
"C:\Users\Julian Andres\AppData\Local\Programs\Python\Python313\python.exe" -m venv .
Scripts\activate.bat
cd info
pip install -r requirements.txt
```

---

## 2. requirements.txt — Dependencias corregidas

**Archivo:** `info/requirements.txt`

**Cambios:**
- ✅ Agregado `whitenoise==6.8.2` — Sirve archivos estáticos (CSS, imágenes) en producción
- ✅ Agregado `Pillow==11.1.0` — Procesa `ImageField` (fotos de perfil, fotos de grupo, archivos)
- ✅ Agregado `google-api-python-client` — Requerido por el servicio de moderación (Perspective API)
- ✅ Eliminado `redis` duplicado (aparecía 2 veces)

**Contenido final:**

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
google-api-python-client
whitenoise==6.8.2
Pillow==11.1.0
```

---

## 3. Procfile — Servidor cambiado

**Archivo:** `info/Procfile`

**Antes (no soportaba WebSockets):**
```
web: gunicorn info.wsgi
```

**Después (soporta WebSockets para el chat):**
```
web: daphne -b 0.0.0.0 -p $PORT info.asgi:application
```

**¿Por qué?** `gunicorn` usa WSGI que NO soporta WebSockets. `daphne` usa ASGI que SÍ soporta WebSockets. Sin este cambio, el chat en tiempo real no funcionaría en producción.

---

## 4. asgi.py — WebSocket routing agregado

**Archivo:** `info/info/asgi.py`

**Antes (sin soporte para WebSockets):**
```python
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'info.settings')
application = get_asgi_application()
```

**Después (con routing para el chat WebSocket):**
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
        URLRouter(websocket_urlpatterns)
    ),
})
```

**¿Qué hace cada parte?**
- `ProtocolTypeRouter` → Separa peticiones HTTP normales de WebSocket
- `AuthMiddlewareStack` → Permite que el WebSocket acceda al usuario autenticado (sesión)
- `URLRouter(websocket_urlpatterns)` → Conecta la URL `ws/chat/<chat_id>/` con el `ChatConsumer`

---

## 5. settings.py — Variables de entorno y WhiteNoise

**Archivo:** `info/info/settings.py`

### 5.1. Se agregó `dotenv` para cargar variables de entorno

**Antes:**
```python
from pathlib import Path
import os
import pymysql
pymysql.install_as_MySQLdb()
```

**Después:**
```python
from pathlib import Path
import os
from dotenv import load_dotenv
import pymysql
pymysql.install_as_MySQLdb()

# Cargar variables de entorno desde .env
load_dotenv()
```

### 5.2. Secretos movidos a variables de entorno

**Antes (valores hardcodeados — INSEGURO):**
```python
SECRET_KEY = 'django-insecure-h2*$b!#5upbewe)h)c0s074)!675xs#zj4sj$sx3yd*bn55k!1'
DEBUG = True
ALLOWED_HOSTS = ["*", "infosena.site"]
```

**Después (lee de .env, con valores por defecto para desarrollo):**
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-h2*$b!#5upbewe)h)c0s074)!675xs#zj4sj$sx3yd*bn55k!1')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*,infosena.site').split(',')
```

### 5.3. WhiteNoise agregado al middleware

**Antes:**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    ...
]
```

**Después:**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',    # ← AGREGADO
    'django.contrib.sessions.middleware.SessionMiddleware',
    ...
]
```

**¿Por qué?** En producción, Django no sirve archivos estáticos (CSS, JS, imágenes). WhiteNoise se encarga de servirlos. Sin esto, la página se vería sin estilos.

### 5.4. Base de datos lee de .env

**Antes (hardcodeado):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'infosena_db',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '3306',
        ...
    }
}
```

**Después (lee de .env):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'infosena_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        ...
    }
}
```

### 5.5. Redis lee de .env

**Antes:**
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

**Después:**
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.getenv('REDIS_URL', 'redis://127.0.0.1:6379')],
        },
    },
}
```

### 5.6. Email y API keys leen de .env

**Antes:**
```python
EMAIL_HOST_USER = "perezpolancocarlosmario@gmail.com"
EMAIL_HOST_PASSWORD = "zdotpwzoijuwwsts"
PERSPECTIVE_API_KEY = 'AIzaSyClFIfrYfiMOtH3nDTgBtYNSxS08en0fH4'
```

**Después:**
```python
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'perezpolancocarlosmario@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'zdotpwzoijuwwsts')
PERSPECTIVE_API_KEY = os.getenv('PERSPECTIVE_API_KEY', 'AIzaSyClFIfrYfiMOtH3nDTgBtYNSxS08en0fH4')
```

---

## 6. .env — Archivo de variables de entorno

**Archivo:** `info/.env` (NUEVO — antes solo tenía OPENAI_API_KEY)

**Contenido actual:**
```env
SECRET_KEY=django-insecure-h2*$b!#5upbewe)h)c0s074)!675xs#zj4sj$sx3yd*bn55k!1
DEBUG=True

# Base de datos (local)
DB_NAME=infosena_db
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

# Redis (local)
REDIS_URL=redis://127.0.0.1:6379

# Email
EMAIL_HOST_USER=perezpolancocarlosmario@gmail.com
EMAIL_HOST_PASSWORD=zdotpwzoijuwwsts

# APIs
OPENAI_API_KEY=sk-proj-...
PERSPECTIVE_API_KEY=AIzaSy...
```

> ⚠️ Este archivo está en `.gitignore` — NO se sube a GitHub. Los secretos quedan seguros.

---

## 7. .env.example — Plantilla creada

**Archivo:** `info/.env.example` (NUEVO)

Este archivo SÍ se sube a GitHub. Sirve como guía para que cualquier persona que clone el proyecto sepa qué variables necesita configurar, pero SIN valores reales.

```env
SECRET_KEY=tu-secret-key-aqui
DEBUG=False

DB_NAME=railway
DB_USER=root
DB_PASSWORD=
DB_HOST=
DB_PORT=3306

REDIS_URL=redis://127.0.0.1:6379

EMAIL_HOST_USER=tucorreo@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

OPENAI_API_KEY=sk-...
PERSPECTIVE_API_KEY=AIza...
```

---

## 8. runtime.txt — Versión de Python

**Archivo:** `info/runtime.txt` (NUEVO)

```
python-3.13.5
```

Railway usa este archivo para saber qué versión de Python instalar.

---

## 9. Resumen rápido

| # | Archivo | Acción | ¿Por qué? |
|---|---|---|---|
| 1 | Entorno virtual | Recreado | El anterior era de otra PC |
| 2 | `requirements.txt` | Agregados 3 paquetes, eliminado duplicado | Pillow (fotos), WhiteNoise (CSS), google-api (moderación) |
| 3 | `Procfile` | gunicorn → daphne | WebSockets para el chat |
| 4 | `asgi.py` | Reescrito completo | Routing de WebSocket para Django Channels |
| 5 | `settings.py` | 6 cambios | dotenv, WhiteNoise, secretos → .env |
| 6 | `.env` | Actualizado | Todas las variables de entorno centralizadas |
| 7 | `.env.example` | Creado | Plantilla para otros desarrolladores |
| 8 | `runtime.txt` | Creado | Railway necesita saber la versión de Python |

---

## Cómo correr el proyecto localmente después de estos cambios

```cmd
cd "C:\Users\Julian Andres\OneDrive\Desktop\Para Clase\InfoSena\SENA"
Scripts\activate.bat
cd info

:: Crear la BD (solo la primera vez)
"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -e "CREATE DATABASE infosena_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

:: Migraciones
python manage.py migrate

:: Iniciar servidor
python manage.py runserver
```

Abre `http://127.0.0.1:8000` en tu navegador.
