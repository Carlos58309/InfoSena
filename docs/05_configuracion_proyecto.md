# 05 — Configuración de Servicios Externos del Proyecto

> **Proyecto:** InfoSENA — Red social institucional SENA  
> **Requisito previo:** Manuales 01-04 completados  
> **Objetivo:** Configurar correctamente cada servicio externo para que funcione en local y producción

---

## Tabla de Contenidos

1. [Servicios externos detectados](#1-servicios-externos-detectados)
2. [MySQL — Base de datos](#2-mysql--base-de-datos)
3. [Redis — Canal de WebSockets](#3-redis--canal-de-websockets)
4. [Gmail SMTP — Envío de correos](#4-gmail-smtp--envío-de-correos)
5. [Google Perspective API — Moderación de texto](#5-google-perspective-api--moderación-de-texto)
6. [OpenAI Moderation API — Moderación de imágenes](#6-openai-moderation-api--moderación-de-imágenes)
7. [Archivo .env completo](#7-archivo-env-completo)
8. [Actualizar settings.py para usar .env](#8-actualizar-settingspy-para-usar-env)
9. [Pruebas locales de cada servicio](#9-pruebas-locales-de-cada-servicio)
10. [Checklist final](#10-checklist-final)

---

## 1. Servicios externos detectados

El proyecto InfoSENA utiliza los siguientes servicios externos:

| # | Servicio | Propósito | ¿Obligatorio? |
|---|---|---|---|
| 1 | **MySQL** | Base de datos relacional | ✅ Sí |
| 2 | **Redis** | Channel Layer para WebSockets (chat) | ✅ Sí (para el chat) |
| 3 | **Gmail SMTP** | Envío de correos (verificación, recuperación) | ✅ Sí |
| 4 | **Google Perspective API** | Moderación de texto (toxicidad) | ⚠️ Recomendado |
| 5 | **OpenAI Moderation API** | Moderación de imágenes | ❌ Opcional |

---

## 2. MySQL — Base de datos

### ¿Para qué se usa?

MySQL almacena toda la información del proyecto: usuarios, publicaciones, chats, amistades, notificaciones, etc.

### Configuración actual en el proyecto

| Parámetro | Valor (desarrollo) |
|---|---|
| Motor | MySQL 8.x |
| Nombre BD | `infosena_db` |
| Usuario | `root` |
| Contraseña | `root` |
| Host | `localhost` |
| Puerto | `3306` |

### Verificar que MySQL funciona

```cmd
mysql -u root -p -e "SHOW DATABASES;"
```

Deberías ver `infosena_db` en la lista. Si no existe, créala:

```sql
CREATE DATABASE infosena_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Checklist MySQL

- [ ] MySQL instalado y corriendo
- [ ] Base de datos `infosena_db` creada
- [ ] Puede conectarse con `root`/`root`
- [ ] Migraciones aplicadas (`python manage.py migrate`)

---

## 3. Redis — Canal de WebSockets

### ¿Para qué se usa?

Redis actúa como **message broker** para Django Channels. Cuando un usuario envía un mensaje en el chat, Redis distribuye ese mensaje a todos los participantes conectados por WebSocket en tiempo real.

### Configuración actual en el proyecto

| Parámetro | Valor |
|---|---|
| Host | `127.0.0.1` |
| Puerto | `6379` |
| Backend | `channels_redis.core.RedisChannelLayer` |

### Instalar Redis (si no lo hiciste en manual 01)

**Windows (Memurai):**
1. Descarga desde [https://www.memurai.com/get-memurai](https://www.memurai.com/get-memurai)
2. Instala el ejecutable
3. Memurai se ejecuta como servicio de Windows automáticamente

**Windows (WSL):**
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Verificar que Redis funciona

```cmd
redis-cli ping
```

Respuesta esperada: `PONG`

### ¿Qué pasa si Redis no está corriendo?

El proyecto puede funcionar sin Redis, pero **el chat en tiempo real no funcionará**. Las demás funcionalidades (registro, login, publicaciones, amistades) sí funcionarán.

Si quieres desarrollar sin Redis temporalmente, puedes cambiar la configuración de Channel Layers en `settings.py` a una versión en memoria (solo para desarrollo):

```python
# SOLO PARA DESARROLLO SIN REDIS
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

> ⚠️ **No uses InMemoryChannelLayer en producción.** No escala y pierde mensajes.

### Checklist Redis

- [ ] Redis instalado
- [ ] Redis corriendo en puerto 6379
- [ ] `redis-cli ping` responde `PONG`

---

## 4. Gmail SMTP — Envío de correos

### ¿Para qué se usa?

Gmail SMTP envía correos electrónicos en dos flujos del proyecto:

1. **Verificación de registro:** Envía un código de 6 dígitos al correo del nuevo usuario
2. **Recuperación de contraseña:** Envía un código para restablecer la contraseña

### Configuración actual

| Parámetro | Valor |
|---|---|
| Host | `smtp.gmail.com` |
| Puerto | `587` |
| TLS | ✅ Activado |
| Email | `perezpolancocarlosmario@gmail.com` |
| Password | Contraseña de app de Gmail |

### Crear tu propia contraseña de app de Gmail

> ⚠️ **La contraseña que ves en `settings.py` es una "contraseña de aplicación"**, NO la contraseña real de Gmail. Google genera estas contraseñas especiales para que apps externas puedan enviar correos.

**Paso 1:** Habilitar verificación en 2 pasos

1. Ve a [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. En "Cómo accedes a Google", busca **"Verificación en dos pasos"**
3. Actívala si no está activada (sigue las instrucciones de Google)

**Paso 2:** Crear contraseña de aplicación

1. Ve a [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Si no ves esta opción, es porque la verificación en 2 pasos no está activada
3. En "Selecciona la app", escribe un nombre: **InfoSENA**
4. Click en **"Crear"**
5. Google te mostrará una **contraseña de 16 caracteres** (ejemplo: `abcd efgh ijkl mnop`)
6. **Copia esta contraseña** — es la que usarás como `EMAIL_HOST_PASSWORD`

**Paso 3:** Colocar en `.env`

```env
EMAIL_HOST_USER=tu.correo@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

> ⚠️ **SEGURIDAD:** La contraseña de app solo sirve para enviar correos desde Gmail. No da acceso completo a tu cuenta. Aun así, **no la compartas ni la subas a GitHub.**

### Probar que los correos se envían

Desde la carpeta `info/`, ejecuta:

```cmd
python manage.py shell
```

Luego en el shell de Python:

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Prueba InfoSENA',
    'Este es un correo de prueba desde InfoSENA.',
    settings.DEFAULT_FROM_EMAIL,
    ['tu.correo.personal@gmail.com'],  # Pon TU correo aquí
    fail_silently=False,
)
```

Si no da error y recibes el correo, funciona. Si da error `SMTPAuthenticationError`, revisa:
- Que la verificación en 2 pasos esté activada
- Que la contraseña de app sea correcta
- Que el correo en `EMAIL_HOST_USER` sea correcto

Escribe `exit()` para salir del shell.

### Checklist Gmail SMTP

- [ ] Verificación en 2 pasos activada en Google
- [ ] Contraseña de aplicación generada
- [ ] `EMAIL_HOST_USER` con tu correo Gmail en `.env`
- [ ] `EMAIL_HOST_PASSWORD` con la contraseña de app en `.env`
- [ ] Prueba de envío de correo exitosa

---

## 5. Google Perspective API — Moderación de texto

### ¿Para qué se usa?

La **Perspective API** de Google analiza texto y le asigna puntajes de toxicidad, insultos, amenazas, etc. InfoSENA la usa para **moderar automáticamente** mensajes de chat, publicaciones y comentarios.

### Pipeline de moderación de InfoSENA

```
Texto del usuario
        │
        ▼
┌─ FILTRO LOCAL (siempre) ─┐
│  • Detección leetspeak    │
│  • 40+ palabras prohibidas│
│  • Normalización unicode  │
└──────────┬────────────────┘
           │ Si no detecta nada
           ▼
┌─ PERSPECTIVE API ────────┐
│  • TOXICITY: 0.55        │
│  • SEVERE_TOXICITY: 0.50 │
│  • INSULT: 0.55          │
│  • PROFANITY: 0.55       │
│  • THREAT: 0.50          │
│  • IDENTITY_ATTACK: 0.50 │
└──────────┬────────────────┘
           │
           ▼
      ¿Bloqueado?
      Sí → No se publica
      No → Se publica
```

### Obtener una API Key de Google Perspective

**Paso 1:** Crear un proyecto en Google Cloud

1. Ve a [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Crea una cuenta si no tienes (es gratuita, no pide tarjeta para Perspective API)
3. Click en **"Seleccionar proyecto"** → **"Nuevo proyecto"**
4. Nombre: **InfoSENA** → **Crear**

**Paso 2:** Habilitar la API

1. Ve a [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)
2. Busca: **"Perspective Comment Analyzer API"**
3. Click en el resultado
4. Click en **"Habilitar"** (Enable)

**Paso 3:** Crear credenciales

1. Ve a [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Click en **"+ CREAR CREDENCIALES"** → **"Clave de API"**
3. Se generará una API Key (ejemplo: `AIzaSyC...`)
4. Copia esta clave

**Paso 4:** (Recomendado) Restringir la API Key

1. Click en la API Key que acabas de crear
2. En "Restricciones de API":
   - Selecciona **"Restringir clave"**
   - Marca solo **"Perspective Comment Analyzer API"**
3. Guarda los cambios

**Paso 5:** Solicitar acceso a Perspective API

1. Ve a [https://developers.perspectiveapi.com/s/request-api](https://developers.perspectiveapi.com/s/request-api)
2. Llena el formulario con tu información
3. Espera la aprobación (generalmente es automática para proyectos educativos)

**Paso 6:** Agregar al `.env`

```env
PERSPECTIVE_API_KEY=AIzaSyC_tu_clave_aquí
```

### ¿Qué pasa si no tienes la API Key?

El sistema tiene un **fallback local**. Si Perspective API no está disponible o falla:
- El filtro de leetspeak y palabras prohibidas **siempre funciona**
- Solo se pierde el análisis semántico avanzado de Google

### Límites de uso

| Aspecto | Valor |
|---|---|
| Requests/segundo | 1 (free tier) |
| Requests/día | 1,000+ (varía) |
| Costo | Gratuito para proyectos pequeños |

### Checklist Perspective API

- [ ] Proyecto creado en Google Cloud Console
- [ ] Perspective Comment Analyzer API habilitada
- [ ] API Key creada y copiada
- [ ] API Key restringida solo a Perspective API
- [ ] Acceso aprobado por Google
- [ ] `PERSPECTIVE_API_KEY` en `.env`

---

## 6. OpenAI Moderation API — Moderación de imágenes

### ¿Para qué se usa?

La API de moderación de OpenAI se usa como **respaldo opcional** para moderar imágenes subidas al proyecto. No es la moderación principal (esa es Perspective API para texto).

### Obtener una API Key de OpenAI

**Paso 1:** Crear cuenta en OpenAI

1. Ve a [https://platform.openai.com/signup](https://platform.openai.com/signup)
2. Crea una cuenta
3. Verifica tu correo y teléfono

**Paso 2:** Crear API Key

1. Ve a [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click en **"+ Create new secret key"**
3. Nombre: **InfoSENA Moderation**
4. Copia la clave inmediatamente (solo se muestra una vez)

**Paso 3:** Agregar crédito (si es necesario)

- La moderación de OpenAI tiene un costo mínimo
- Puedes agregar $5-10 USD como crédito inicial
- Ve a [https://platform.openai.com/account/billing](https://platform.openai.com/account/billing)

**Paso 4:** Agregar al `.env`

```env
OPENAI_API_KEY=sk-tu_clave_aquí
```

### ¿Es obligatorio?

**No.** El proyecto funciona sin OpenAI. La moderación principal es Google Perspective + filtro local para texto. OpenAI solo se usa como fallback opcional para imágenes.

### Checklist OpenAI

- [ ] Cuenta creada en OpenAI (opcional)
- [ ] API Key generada (opcional)
- [ ] Crédito cargado si es necesario (opcional)
- [ ] `OPENAI_API_KEY` en `.env` (puede quedar vacío)

---

## 7. Archivo .env completo

Con toda la configuración de servicios, tu archivo `info/.env` debe verse así:

```env
# =============================================
# CONFIGURACIÓN DE INFOSENA
# Archivo: info/.env
# =============================================
# ⚠️ NUNCA subas este archivo a GitHub
# ⚠️ Cada desarrollador debe tener su propio .env
# =============================================

# ---- Django ----
SECRET_KEY=django-insecure-h2*$b!#5upbewe)h)c0s074)!675xs#zj4sj$sx3yd*bn55k!1
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ---- Base de datos MySQL ----
DB_NAME=infosena_db
DB_USER=root
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=3306

# ---- Redis (WebSockets / Chat) ----
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# ---- Email (Gmail SMTP) ----
EMAIL_HOST_USER=tu.correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_de_app_16_caracteres

# ---- Google Perspective API (Moderación de texto) ----
PERSPECTIVE_API_KEY=AIzaSyC_tu_clave_aquí

# ---- OpenAI (Moderación de imágenes - Opcional) ----
OPENAI_API_KEY=

# ---- Admin ----
ADMIN_EMAIL=tu.correo@gmail.com
```

### Crear archivo .env.example

Se recomienda crear un archivo `.env.example` que **SÍ se sube a GitHub** como referencia para otros desarrolladores. Este archivo muestra qué variables se necesitan pero **sin valores reales**:

Crea `info/.env.example`:

```env
# =============================================
# CONFIGURACIÓN DE INFOSENA - PLANTILLA
# Copia este archivo como .env y llena los valores
# =============================================

# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos MySQL
DB_NAME=infosena_db
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Email (Gmail SMTP)
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Google Perspective API
PERSPECTIVE_API_KEY=

# OpenAI (Opcional)
OPENAI_API_KEY=

# Admin
ADMIN_EMAIL=
```

---

## 8. Actualizar settings.py para usar .env

Para que Django lea las variables del archivo `.env`, necesitas modificar `info/info/settings.py`.

### Cambios necesarios

**1. Al inicio del archivo, después de los imports existentes, agregar:**

```python
from dotenv import load_dotenv
load_dotenv()
```

**2. Reemplazar SECRET_KEY:**

```python
# ANTES:
SECRET_KEY = 'django-insecure-h2*$b!#5upbewe)h)c0s074)!675xs#zj4sj$sx3yd*bn55k!1'

# DESPUÉS:
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-por-defecto-solo-desarrollo')
```

**3. Reemplazar DEBUG:**

```python
# ANTES:
DEBUG = True

# DESPUÉS:
DEBUG = os.getenv('DEBUG', 'True') == 'True'
```

**4. Reemplazar ALLOWED_HOSTS:**

```python
# ANTES:
ALLOWED_HOSTS = ["*", "infosena.site"]

# DESPUÉS:
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

**5. Reemplazar DATABASES:**

```python
# DESPUÉS:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'infosena_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}
```

**6. Reemplazar CHANNEL_LAYERS:**

```python
# DESPUÉS:
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.getenv('REDIS_HOST', '127.0.0.1'), int(os.getenv('REDIS_PORT', 6379)))],
        },
    },
}
```

**7. Reemplazar configuración de email:**

```python
# DESPUÉS:
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', EMAIL_HOST_USER)
```

**8. Reemplazar API keys:**

```python
# DESPUÉS:
PERSPECTIVE_API_KEY = os.getenv('PERSPECTIVE_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
```

> **Nota:** `python-dotenv` ya está en `requirements.txt`, no necesitas instalar nada adicional.

---

## 9. Pruebas locales de cada servicio

### 9.1. Probar MySQL

```cmd
cd info
python manage.py shell
```

```python
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT 1")
print("MySQL OK:", cursor.fetchone())
exit()
```

Resultado esperado: `MySQL OK: (1,)`

### 9.2. Probar Redis

```cmd
redis-cli ping
```

Resultado esperado: `PONG`

Prueba desde Django:

```cmd
python manage.py shell
```

```python
import redis
r = redis.Redis(host='127.0.0.1', port=6379)
r.set('test', 'InfoSENA funciona')
print(r.get('test'))
exit()
```

Resultado esperado: `b'InfoSENA funciona'`

### 9.3. Probar Gmail SMTP

```cmd
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test InfoSENA',
    'Correo de prueba.',
    settings.DEFAULT_FROM_EMAIL,
    ['tu@correo.com'],
    fail_silently=False,
)
print("Correo enviado correctamente")
exit()
```

Revisa tu bandeja de entrada (y la carpeta de spam).

### 9.4. Probar Perspective API

```cmd
python manage.py shell
```

```python
from applications.moderacion.perspective_service import PerspectiveService

service = PerspectiveService()
resultado = service.analizar_texto("esto es una prueba normal")
print("Resultado:", resultado)

resultado2 = service.analizar_texto("eres un idiota estúpido")
print("Resultado tóxico:", resultado2)
exit()
```

Resultado esperado:
- Texto normal → `bloqueado: False`
- Texto tóxico → `bloqueado: True`

### 9.5. Probar el servidor completo

```cmd
python manage.py runserver
```

1. Abre `http://127.0.0.1:8000/` → Landing page
2. Abre `http://127.0.0.1:8000/admin/` → Panel admin
3. Registra un usuario → Debe llegar correo de verificación
4. Ingresa el código → Cuenta creada
5. Login → Acceso al feed

---

## 10. Checklist Final

### Servicios obligatorios

- [ ] **MySQL:** Corriendo en localhost:3306, BD `infosena_db` creada, migraciones aplicadas
- [ ] **Redis:** Corriendo en localhost:6379, `redis-cli ping` → `PONG`
- [ ] **Gmail SMTP:** Contraseña de app generada, correos de prueba enviados correctamente

### Servicios opcionales

- [ ] **Google Perspective API:** Proyecto creado en Google Cloud, API habilitada, clave generada
- [ ] **OpenAI Moderation API:** Cuenta creada, API Key generada (o campo vacío en .env)

### Configuración

- [ ] Archivo `.env` creado en `info/.env` con todos los valores
- [ ] Archivo `.env.example` creado en `info/.env.example` (sin valores reales)
- [ ] `settings.py` actualizado para leer de `.env` con `python-dotenv`
- [ ] `.env` está en `.gitignore` (NO se sube a GitHub)
- [ ] `.env.example` NO está en `.gitignore` (SÍ se sube a GitHub)

### Pruebas

- [ ] Conexión a MySQL verificada desde Django shell
- [ ] Conexión a Redis verificada
- [ ] Envío de correo con Gmail verificado
- [ ] Moderación de texto verificada (si tienes Perspective API Key)
- [ ] Servidor ejecutándose sin errores

---

> **Siguiente paso:** [06_despliegue_produccion.md](06_despliegue_produccion.md) — Despliegue en producción
