# 00 — Análisis Tecnológico del Proyecto InfoSENA

> **Fecha del análisis:** Marzo 2026  
> **Proyecto:** InfoSENA — Red social institucional para el SENA  
> **Ubicación del proyecto:** `info/`

---

## 1. Resumen Ejecutivo

**InfoSENA** es una red social web institucional desarrollada para el **Servicio Nacional de Aprendizaje (SENA)** de Colombia. Permite a aprendices, instructores y personal de bienestar registrarse, conectar entre sí, publicar contenido, chatear en tiempo real y recibir notificaciones. Incluye un sistema de moderación automática de contenido con inteligencia artificial (Google Perspective API y OpenAI).

El proyecto es una **aplicación web monolítica fullstack** construida con **Django 5.2.8** (Python), que sirve tanto el backend (API, lógica de negocio, base de datos) como el frontend (templates HTML con Tailwind CSS desde CDN y JavaScript inline). Usa **MySQL** como base de datos, **Redis** para comunicación en tiempo real vía WebSockets (Django Channels), y **Gmail SMTP** para envío de correos.

---

## 2. Tipo de Aplicación

| Aspecto | Valor |
|---|---|
| **Tipo** | Aplicación web monolítica fullstack (Server-Side Rendered) |
| **Patrón** | MVC (Django MTV: Model-Template-View) |
| **Renderizado** | Server-Side Rendering (SSR) con Django Templates |
| **Frontend** | Django Templates + Tailwind CSS (CDN) + JS inline |
| **Backend** | Django 5.2.8 (Python 3.13) |
| **Tiempo real** | Django Channels + WebSockets + Redis |
| **Base de datos** | MySQL 8.x (via PyMySQL) |

---

## 3. Stack Tecnológico Completo

### 3.1. Backend

| Tecnología | Versión | Propósito |
|---|---|---|
| Python | 3.13.5 | Lenguaje principal |
| Django | 5.2.8 | Framework web |
| Django Channels | 4.0.0 | WebSockets y comunicación en tiempo real |
| Daphne | 4.0.0 | Servidor ASGI (para WebSockets) |
| Gunicorn | 23.0.0 | Servidor WSGI (para HTTP en producción) |
| PyMySQL | 1.1.2 | Conector MySQL para Python |
| Redis | 5.0.1 (cliente Python) | Backend para Channel Layers |
| channels-redis | 4.1.0 | Integración Channels ↔ Redis |
| python-dotenv | — | Carga de variables de entorno desde `.env` |
| python-dateutil | 2.8.2 | Manejo avanzado de fechas |
| openai | ≥1.0.0 | API de moderación de contenido (imágenes) |

### 3.2. Frontend

| Tecnología | Versión | Propósito |
|---|---|---|
| Django Templates | (integrado) | Motor de plantillas HTML |
| Tailwind CSS | CDN (última) | Framework de estilos CSS |
| CSS personalizado | — | `static/css/estilos.css` |
| JavaScript (inline) | Vanilla | Interactividad (AJAX, notificaciones, chat) |

### 3.3. Infraestructura / Servicios

| Servicio | Propósito |
|---|---|
| MySQL 8.x | Base de datos relacional |
| Redis | Channel Layer para WebSockets |
| Gmail SMTP | Envío de correos (verificación, recuperación) |
| Google Perspective API | Moderación de texto (toxicidad, insultos, amenazas) |
| OpenAI Moderation API | Moderación de imágenes (opcional) |

---

## 4. Estructura del Proyecto

```
SENA/                           ← Entorno virtual Python (venv)
├── pyvenv.cfg                  ← Configuración del venv
├── .gitignore                  ← ⚠️ Actualmente bloquea todo (necesita corrección)
├── Include/                    ← Headers del venv
├── Lib/                        ← Paquetes instalados (venv)
├── Scripts/                    ← Ejecutables del venv (activate, pip)
└── info/                       ← 🔹 PROYECTO DJANGO (directorio principal)
    ├── manage.py               ← Punto de entrada de Django
    ├── fix_usuarios.py         ← Script de reparación de usuarios
    ├── Procfile                ← Configuración de despliegue (Heroku/Railway)
    ├── requirements.txt        ← Dependencias Python
    ├── info/                   ← Configuración central de Django
    │   ├── __init__.py
    │   ├── settings.py         ← Configuración principal
    │   ├── urls.py             ← Rutas principales
    │   ├── asgi.py             ← Configuración ASGI
    │   └── wsgi.py             ← Configuración WSGI
    ├── applications/           ← 🔹 11 aplicaciones Django
    │   ├── amistades/          ← Sistema de amistades
    │   ├── busqueda/           ← Búsqueda de usuarios
    │   ├── chat/               ← Chat en tiempo real (WebSockets)
    │   ├── index/              ← Página de inicio (landing)
    │   ├── moderacion/         ← Moderación automática de contenido
    │   ├── notificaciones/     ← Sistema de notificaciones
    │   ├── perfil/             ← Gestión de perfiles
    │   ├── publicaciones/      ← Publicaciones/posts
    │   ├── registro/           ← Registro de usuarios
    │   ├── sesion/             ← Autenticación e inicio de sesión
    │   └── usuarios/           ← Modelo unificado de usuario
    ├── templates/              ← Plantillas HTML
    ├── static/                 ← Archivos estáticos (CSS, imágenes)
    └── media/                  ← Archivos subidos por usuarios
```

---

## 5. Frontend Detectado

| Aspecto | Detalle |
|---|---|
| **Tipo** | No es SPA. Es Server-Side Rendering con Django Templates |
| **Estilización** | Tailwind CSS vía CDN + archivo `estilos.css` personalizado |
| **JavaScript** | Vanilla JS embebido en las plantillas (AJAX, WebSocket, DOM) |
| **Interactividad** | AJAX para likes, comentarios, búsqueda, notificaciones en tiempo real |
| **No se usa** | React, Vue, Angular, Vite, Next.js, ni ningún framework JS |

### Plantillas HTML detectadas (22 archivos):

| Plantilla | Propósito |
|---|---|
| `index.html` | Landing page pública |
| `login.html` | Formulario de inicio de sesión |
| `registrar.html` | Formulario de registro |
| `verificar_codigo.html` | Verificación de código por email |
| `esperando_aprobacion.html` | Pantalla de espera de aprobación admin |
| `inputs_generales.html` | Campos comunes del registro |
| `inputs_aprendiz.html` | Campos específicos para aprendices |
| `home.html` | Feed principal (muro/noticias) |
| `dashboard.html` | Panel de control (⚠️ placeholder mínimo) |
| `perfil.html` | Perfil del usuario |
| `ver_perfil.html` | Ver perfil de otros usuarios |
| `editar_perfil.html` | Editar perfil propio |
| `eliminar_perfil.html` | Eliminar cuenta |
| `crear_publicacion.html` | Crear publicación |
| `chat.html` | Interfaz de chat en tiempo real |
| `listar_chat.html` | Lista de conversaciones |
| `crear_grupo.html` | Crear grupo de chat |
| `amigos.html` | Lista de amigos, solicitudes y sugerencias |
| `notificaciones.html` | Centro de notificaciones |
| `solicitar_correo.html` | Solicitar recuperación de contraseña |
| `codigo_restablecer_contraseña.html` | Código para restablecer contraseña |
| `restablecer_password.html` | Formulario nueva contraseña |
| `panel_aprobacion.html` | Panel admin para aprobar usuarios |

---

## 6. Backend Detectado

### 6.1. Aplicaciones Django (11)

| App | Responsabilidad | Modelos | Señales | WebSocket |
|---|---|---|---|---|
| `registro` | Registro de usuarios, verificación email, aprobación | Aprendiz, Instructor, Bienestar | ✅ Sync a Usuario | ❌ |
| `usuarios` | Modelo unificado de usuario | Usuario | ✅ Auto-crear | ❌ |
| `sesion` | Login, logout, recuperación contraseña | Sesion, CodigoRecuperacion | ❌ | ❌ |
| `index` | Página de inicio (landing) | — | ❌ | ❌ |
| `perfil` | Gestión de perfiles | — (usa Usuario) | ❌ | ❌ |
| `publicaciones` | CRUD publicaciones, likes, comentarios | Publicacion, ArchivoPublicacion, Like, Comentario | ✅ Moderación | ❌ |
| `chat` | Chat 1-a-1 y grupal en tiempo real | Chat, Mensaje, MensajeVisto, etc. | ❌ | ✅ |
| `amistades` | Sistema de amistades | Amistad | ❌ | ❌ |
| `notificaciones` | Notificaciones del sistema | Notificacion, ChatSilenciado | ✅ Auto-crear | ❌ |
| `busqueda` | Búsqueda de usuarios | — (usa sesión) | ❌ | ❌ |
| `moderacion` | Moderación automática IA | RegistroModeracion, UsuarioSancionado, PalabraProhibida | ✅ Pre-save | ❌ |

### 6.2. Flujo de Roles de Usuario

```
Registro → Verificación Email → [Aprobación Admin*] → Login → Dashboard/Home
                                     ↑
                      * Solo para Instructor y Bienestar
```

**3 tipos de usuario:**
- **Aprendiz:** Estudiante del SENA. Puede comentar, dar like, chatear.
- **Instructor:** Docente del SENA. Requiere aprobación admin. Puede comentar, dar like, chatear.
- **Bienestar:** Personal de bienestar. Requiere aprobación admin. **Único rol que puede crear publicaciones.**

---

## 7. Base de Datos Detectada

| Aspecto | Detalle |
|---|---|
| **Motor** | MySQL 8.x |
| **Conector Python** | PyMySQL 1.1.2 |
| **Nombre BD** | `infosena_db` |
| **Usuario BD** | `root` |
| **Contraseña BD** | `root` (⚠️ solo para desarrollo) |
| **Host** | `localhost` |
| **Puerto** | `3306` |
| **SQL Mode** | `STRICT_TRANS_TABLES` |

### Tablas principales (por modelos detectados):

| Modelo | App | Campos clave |
|---|---|---|
| `Usuario` | usuarios | documento, tipo, nombre, email, foto, es_admin, user (FK) |
| `Aprendiz` | registro | documento, nombre, correo_personal, correo_institucional, ficha, foto, verificado |
| `Instructor` | registro | documento, nombre, correo_institucional, aprobado, verificado |
| `Bienestar` | registro | documento, nombre, correo_institucional, aprobado, verificado |
| `Amistad` | amistades | emisor, receptor, estado (pendiente/aceptada/rechazada) |
| `Publicacion` | publicaciones | autor (Bienestar), titulo, contenido, categoria, activa |
| `ArchivoPublicacion` | publicaciones | publicacion (FK), archivo |
| `Like` | publicaciones | publicacion (FK), content_type, object_id (GenericFK) |
| `Comentario` | publicaciones | publicacion (FK), content_type, object_id (GenericFK), contenido |
| `Chat` | chat | participantes (M2M), is_group, nombre_grupo, admin_grupo |
| `Mensaje` | chat | chat (FK), autor, contenido, archivo, tipo_archivo, visto |
| `MensajeVisto` | chat | mensaje (FK), usuario, visto_en |
| `Notificacion` | notificaciones | destinatario, emisor, tipo, mensaje, leida |
| `ChatSilenciado` | notificaciones | usuario, silenciado |
| `RegistroModeracion` | moderacion | contenido, resultado, metodo, fecha |
| `UsuarioSancionado` | moderacion | usuario, razon, fecha |
| `PalabraProhibida` | moderacion | palabra |
| `Sesion` | sesion | usuario, token, activa |
| `CodigoRecuperacion` | sesion | email, codigo, creado_en |

---

## 8. Autenticación y Seguridad Detectadas

| Aspecto | Implementación |
|---|---|
| **Tipo de autenticación** | Basada en sesiones de Django (session-based) |
| **Identificador de login** | Documento de identidad + contraseña |
| **Verificación de email** | Código de 6 dígitos (expira en 15 minutos) |
| **Aprobación administrativa** | Requerida para Instructor y Bienestar |
| **Validación de contraseña** | 8-12 caracteres, mayúscula, minúscula, 3+ números, carácter especial |
| **Validación de dominio email** | Solo correos institucionales SENA |
| **Recuperación de contraseña** | Código por email + token temporal |
| **Protección CSRF** | Middleware de Django activado |
| **Clickjacking** | XFrameOptionsMiddleware activado |
| **Moderación contenido** | Google Perspective API + OpenAI + filtro local leetspeak |

### ⚠️ Problemas de Seguridad Detectados (Desarrollo)

| Problema | Ubicación | Riesgo |
|---|---|---|
| `SECRET_KEY` hardcodeada en settings.py | `info/settings.py` | **CRÍTICO** en producción |
| `DEBUG = True` | `info/settings.py` | **ALTO** en producción |
| `ALLOWED_HOSTS = ["*"]` | `info/settings.py` | **ALTO** en producción |
| Contraseña de BD hardcodeada (`root`/`root`) | `info/settings.py` | **ALTO** |
| Contraseña de app Gmail hardcodeada | `info/settings.py` | **CRÍTICO** |
| API Key de Perspective hardcodeada | `info/settings.py` | **MEDIO** |
| No se usa `python-dotenv` a pesar de estar en requirements | `info/settings.py` | **MEDIO** |

> **Nota:** Estos problemas son aceptables en desarrollo local, pero **deben resolverse antes del despliegue en producción**. Ver manual `05_configuracion_proyecto.md` y `06_despliegue_produccion.md`.

---

## 9. Servicios Externos Detectados

| Servicio | Uso | Configuración Actual |
|---|---|---|
| **Gmail SMTP** | Envío de correos (verificación, recuperación) | `smtp.gmail.com:587` con contraseña de app |
| **Google Perspective API** | Moderación de texto (toxicidad, insultos, amenazas) | API Key hardcodeada en settings |
| **OpenAI API** | Moderación de imágenes (opcional) | API Key vía variable de entorno |
| **Redis** | Channel Layer para WebSockets | `localhost:6379` |

---

## 10. Variables de Entorno Requeridas

Actualmente **no existe archivo `.env`**. Se recomienda crear uno con las siguientes variables:

```env
# Django
SECRET_KEY=una-clave-secreta-segura-de-50-caracteres
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos MySQL
DB_NAME=infosena_db
DB_USER=root
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Email (Gmail SMTP)
EMAIL_HOST_USER=correo@gmail.com
EMAIL_HOST_PASSWORD=contraseña-de-app-gmail

# APIs de moderación
OPENAI_API_KEY=sk-...
PERSPECTIVE_API_KEY=AIzaSy...

# Admin
ADMIN_EMAIL=correo@gmail.com
```

---

## 11. Scripts de Ejecución

| Comando | Propósito | Directorio |
|---|---|---|
| `python manage.py runserver` | Ejecutar servidor de desarrollo (HTTP) | `info/` |
| `python manage.py migrate` | Aplicar migraciones a la BD | `info/` |
| `python manage.py makemigrations` | Crear migraciones desde modelos | `info/` |
| `python manage.py createsuperuser` | Crear usuario administrador | `info/` |
| `python fix_usuarios.py` | Reparar usuarios faltantes en tabla Usuario | `info/` |
| `daphne info.asgi:application` | Ejecutar servidor ASGI (WebSockets) | `info/` |
| `gunicorn info.wsgi` | Ejecutar servidor WSGI en producción | `info/` |

---

## 12. Puertos Utilizados

| Puerto | Servicio | Contexto |
|---|---|---|
| **8000** | Django dev server | Desarrollo local |
| **3306** | MySQL | Base de datos |
| **6379** | Redis | Channel Layer (WebSockets) |
| **587** | Gmail SMTP (TLS) | Envío de correos |

---

## 13. Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTE (Navegador)                   │
│          HTML/CSS (Tailwind CDN) + JS inline            │
└────────────────┬──────────────────┬─────────────────────┘
                 │ HTTP              │ WebSocket
                 ▼                   ▼
┌────────────────────────┐ ┌────────────────────────┐
│   Django Views (WSGI)  │ │  Django Channels (ASGI)│
│   • Registro           │ │  • ChatConsumer        │
│   • Login/Sesión       │ │  • Typing indicators   │
│   • Publicaciones      │ │  • Mark as read        │
│   • Perfil             │ └───────────┬────────────┘
│   • Amistades          │             │
│   • Búsqueda           │             ▼
│   • Notificaciones     │    ┌────────────────┐
└────────────┬───────────┘    │   Redis 6379   │
             │                │  Channel Layer │
             ▼                └────────────────┘
    ┌────────────────┐
    │  MySQL 3306    │
    │  infosena_db   │
    └────────────────┘
             │
    ┌────────┴────────────────────────────┐
    │         Servicios Externos          │
    ├─────────────────────────────────────┤
    │  Gmail SMTP (correos)              │
    │  Google Perspective API (moderación)│
    │  OpenAI API (moderación imágenes)  │
    └─────────────────────────────────────┘
```

---

## 14. Flujo de Funcionamiento del Sistema

### 14.1. Registro y Verificación

```
1. Usuario accede a /registro/
2. Selecciona tipo: Aprendiz / Instructor / Bienestar
3. Completa formulario con documento, datos, foto
4. Sistema envía código de verificación al email
5. Usuario ingresa código (15 min de validez)
6. Si es Aprendiz → se crea cuenta automáticamente
7. Si es Instructor/Bienestar → queda "pendiente de aprobación"
8. Admin aprueba desde panel → se crea cuenta
9. Signal sincroniza datos a tabla Usuario unificada
```

### 14.2. Autenticación

```
1. Usuario accede a /sesion/login/
2. Ingresa documento + contraseña
3. Sistema verifica: existe, verificado, aprobado (si aplica)
4. Se crea sesión de Django
5. Redirige a /sesion/home/ (feed principal)
```

### 14.3. Publicaciones

```
1. Solo usuarios Bienestar pueden crear publicaciones
2. Al crear → moderación automática (Perspective + filtro local)
3. Si contenido es tóxico → se bloquea
4. Si pasa → se publica y envía notificación a amigos
5. Cualquier usuario puede dar like y comentar
6. Comentarios también pasan por moderación
```

### 14.4. Chat en Tiempo Real

```
1. Usuario accede a /chat/ → ve lista de conversaciones
2. Click en conversación → abre chat (WebSocket)
3. Mensajes se envían por WebSocket (ChatConsumer)
4. Soporte: texto, imágenes, videos, documentos
5. Mensajes se moderan al guardar (signal pre_save)
6. Indicador de escritura ("typing...")
7. Marcar como leído
8. Eliminar para mí / eliminar para todos (24h)
```

### 14.5. Amistades

```
1. Sistema sugiere amigos (algoritmo inteligente)
2. Usuario envía solicitud → notificación al receptor
3. Receptor acepta/rechaza
4. Si acepta → ambos aparecen como amigos
5. Se puede eliminar amigo en cualquier momento
```

---

## 15. Estrategia de Despliegue Recomendada

### 15.1. Recomendación Principal: Railway

| Componente | Plataforma | Razón |
|---|---|---|
| **Backend Django** | **Railway** | Soporte Python, MySQL addon, Redis addon, Procfile compatible |
| **Base de datos** | **Railway MySQL** | Provisioning automático, backups |
| **Redis** | **Railway Redis** | Addon integrado |
| **Archivos estáticos** | **WhiteNoise** | Middleware de Django para servir estáticos en producción |
| **Archivos media** | **Cloudinary / AWS S3** | Storage externo (pendiente de implementar) |

### 15.2. Alternativa Secundaria: VPS (DigitalOcean / Contabo)

| Componente | Configuración |
|---|---|
| **Servidor web** | Nginx (proxy reverso) |
| **App server HTTP** | Gunicorn |
| **App server WS** | Daphne |
| **Base de datos** | MySQL instalado en el VPS |
| **Redis** | Redis instalado en el VPS |
| **Process manager** | Supervisor o systemd |
| **SSL** | Let's Encrypt (Certbot) |

### ⚠️ Problemas Críticos Antes del Despliegue

| # | Problema | Prioridad |
|---|---|---|
| 1 | `asgi.py` no tiene configuración de Channels/WebSocket routing | **CRÍTICA** |
| 2 | Procfile usa `gunicorn` (WSGI) pero el chat necesita `daphne` (ASGI) | **CRÍTICA** |
| 3 | Secretos hardcodeados en `settings.py` | **CRÍTICA** |
| 4 | No existe archivo `.env` | **ALTA** |
| 5 | `.gitignore` bloquea todos los archivos (`*`) — es del venv | **ALTA** |
| 6 | No hay configuración de storage externo para media files | **MEDIA** |
| 7 | `dashboard.html` es un placeholder sin contenido real | **BAJA** |

---

## 16. Checklist de Comprensión

Antes de continuar con los siguientes manuales, verifica que entiendes:

- [ ] InfoSENA es una app Django monolítica (no tiene frontend separado)
- [ ] Usa MySQL como base de datos (no PostgreSQL, no SQLite)
- [ ] Necesita Redis corriendo para el chat en tiempo real
- [ ] Tiene 3 tipos de usuarios: Aprendiz, Instructor, Bienestar
- [ ] Solo Bienestar puede crear publicaciones
- [ ] El chat usa WebSockets (Django Channels + Daphne)
- [ ] La moderación usa Google Perspective API + filtros locales
- [ ] Los correos se envían por Gmail SMTP
- [ ] No hay framework JS (React, Vue, Angular) — es Django Templates
- [ ] El archivo `asgi.py` necesita actualización antes del despliegue
- [ ] Hay secretos hardcodeados que deben moverse a `.env`

---

## 17. Glosario de Conceptos Clave

| Término | Definición |
|---|---|
| **Django** | Framework web de Python que sigue el patrón MTV (Model-Template-View) |
| **ASGI** | Interfaz de servidor asíncrona para Python. Necesaria para WebSockets |
| **WSGI** | Interfaz de servidor síncrona para Python. Para peticiones HTTP normales |
| **Django Channels** | Extensión de Django que añade soporte para WebSockets y protocolos asíncronos |
| **Daphne** | Servidor ASGI de referencia para Django Channels |
| **Gunicorn** | Servidor WSGI de producción para Django (solo HTTP, no WebSocket) |
| **Redis** | Base de datos en memoria usada como message broker para WebSockets |
| **Channel Layer** | Capa de comunicación entre instancias de Django vía Redis |
| **WebSocket** | Protocolo de comunicación bidireccional en tiempo real |
| **PyMySQL** | Conector Python para MySQL |
| **Tailwind CSS** | Framework CSS de utilidades, usado vía CDN en este proyecto |
| **SMTP** | Protocolo para envío de correos electrónicos |
| **Google Perspective API** | API de Google para detectar contenido tóxico/ofensivo |
| **OpenAI Moderation** | API de OpenAI para moderar contenido (texto e imágenes) |
| **GenericForeignKey** | Mecanismo de Django para crear relaciones polimórficas |
| **Signal (Django)** | Evento que se dispara automáticamente cuando ocurre algo (ej: guardar modelo) |
| **Procfile** | Archivo que define cómo ejecutar la app en plataformas como Heroku/Railway |
| **venv** | Entorno virtual de Python para aislar dependencias |
| **Leetspeak** | Escritura que reemplaza letras por números/símbolos (ej: m13rd4) |
| **SENA** | Servicio Nacional de Aprendizaje — entidad educativa colombiana |

---

> **Siguiente paso:** Continuar con [01_preparacion_entorno_local.md](01_preparacion_entorno_local.md)
