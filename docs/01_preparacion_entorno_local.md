# 01 — Preparación del Entorno Local

> **Proyecto:** InfoSENA — Red social institucional SENA  
> **Stack:** Django 5.2.8 + MySQL + Redis + Channels  
> **Requisito previo:** Ninguno. Este manual parte desde cero.

---

## Tabla de Contenidos

1. [¿Qué necesitas instalar?](#1-qué-necesitas-instalar)
2. [Instalar Python 3.13](#2-instalar-python-313)
3. [Instalar MySQL](#3-instalar-mysql)
4. [Instalar Redis](#4-instalar-redis)
5. [Instalar Visual Studio Code](#5-instalar-visual-studio-code)
6. [Abrir el proyecto en VS Code](#6-abrir-el-proyecto-en-vs-code)
7. [Entender la estructura del proyecto](#7-entender-la-estructura-del-proyecto)
8. [Crear y activar el entorno virtual](#8-crear-y-activar-el-entorno-virtual)
9. [Instalar dependencias Python](#9-instalar-dependencias-python)
10. [Crear la base de datos MySQL](#10-crear-la-base-de-datos-mysql)
11. [Crear archivo .env](#11-crear-archivo-env)
12. [Configurar settings.py para usar .env](#12-configurar-settingspy-para-usar-env)
13. [Ejecutar migraciones](#13-ejecutar-migraciones)
14. [Crear superusuario](#14-crear-superusuario)
15. [Ejecutar el proyecto localmente](#15-ejecutar-el-proyecto-localmente)
16. [Validar que todo funciona](#16-validar-que-todo-funciona)
17. [Errores comunes y soluciones](#17-errores-comunes-y-soluciones)
18. [Checklist final](#18-checklist-final)

---

## 1. ¿Qué necesitas instalar?

Antes de ejecutar el proyecto, necesitas las siguientes herramientas en tu computadora:

| Herramienta | Versión mínima | Para qué sirve |
|---|---|---|
| **Python** | 3.12+ (recomendado 3.13) | Lenguaje de programación del backend |
| **pip** | (viene con Python) | Instalador de paquetes Python |
| **MySQL** | 8.0+ | Base de datos del proyecto |
| **Redis** | 7.0+ | Mensajería en tiempo real (chat WebSocket) |
| **VS Code** | Última versión | Editor de código |
| **Git** | 2.40+ | Control de versiones (ver manual 02) |

---

## 2. Instalar Python 3.13

### Windows

1. Ve a [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Descarga **Python 3.13.x** (el botón amarillo grande)
3. Ejecuta el instalador
4. **MUY IMPORTANTE:** Marca la casilla **"Add Python to PATH"** antes de instalar
5. Click en **"Install Now"**
6. Espera a que termine

**Verificar instalación:** Abre una terminal (CMD o PowerShell) y ejecuta:

```cmd
python --version
```

Debe mostrar algo como: `Python 3.13.5`

```cmd
pip --version
```

Debe mostrar algo como: `pip 24.x.x from ...`

### macOS

```bash
# Opción 1: Instalador oficial
# Descarga desde https://www.python.org/downloads/

# Opción 2: Con Homebrew
brew install python@3.13
```

Verificar:

```bash
python3 --version
pip3 --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip
```

Verificar:

```bash
python3 --version
pip3 --version
```

---

## 3. Instalar MySQL

### Windows

1. Ve a [https://dev.mysql.com/downloads/installer/](https://dev.mysql.com/downloads/installer/)
2. Descarga **MySQL Installer for Windows**
3. Ejecuta el instalador
4. Selecciona **"Developer Default"** o **"Server only"**
5. Durante la configuración:
   - Puerto: **3306** (dejar por defecto)
   - Usuario root: **root**
   - Contraseña root: **root** (para desarrollo local)
6. Finaliza la instalación

**Verificar instalación:**

```cmd
mysql --version
```

**Verificar conexión:**

```cmd
mysql -u root -p
```

Ingresa la contraseña `root`. Si ves el prompt `mysql>`, funciona correctamente. Escribe `exit` para salir.

### macOS

```bash
brew install mysql
brew services start mysql
mysql_secure_installation
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo mysql_secure_installation
```

---

## 4. Instalar Redis

Redis es necesario para el chat en tiempo real (WebSockets).

### Windows

Redis no tiene soporte oficial para Windows, pero hay opciones:

**Opción A — Memurai (Recomendada para Windows):**

1. Ve a [https://www.memurai.com/get-memurai](https://www.memurai.com/get-memurai)
2. Descarga la versión gratuita (Developer Edition)
3. Instala y se ejecutará como servicio automáticamente en puerto 6379

**Opción B — WSL (Windows Subsystem for Linux):**

1. Abre PowerShell como administrador:

```powershell
wsl --install
```

2. Reinicia tu computadora
3. Abre Ubuntu (WSL) y ejecuta:

```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Verificar que Redis funciona:**

```cmd
redis-cli ping
```

Debe responder: `PONG`

### macOS

```bash
brew install redis
brew services start redis
redis-cli ping
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
redis-cli ping
```

---

## 5. Instalar Visual Studio Code

1. Ve a [https://code.visualstudio.com/](https://code.visualstudio.com/)
2. Descarga e instala la versión para tu sistema operativo
3. Extensiones recomendadas para este proyecto:

| Extensión | Propósito |
|---|---|
| **Python** (Microsoft) | Soporte Python, depuración, linting |
| **Pylance** | Autocompletado inteligente para Python |
| **Django** (Baptiste Darthenay) | Resaltado de sintaxis para templates Django |
| **MySQL** (Weijan Chen) | Gestor visual de MySQL |

---

## 6. Abrir el proyecto en VS Code

1. Abre VS Code
2. Ve a **Archivo → Abrir Carpeta** (o `Ctrl + K, Ctrl + O`)
3. Navega a la carpeta del proyecto. La carpeta que debes abrir es:

```
C:\Users\TuUsuario\...\SENA\
```

> **Importante:** Abre la carpeta `SENA` (que contiene `pyvenv.cfg`, `info/`, `Lib/`, etc.), no subcarpetas.

4. Deberías ver la estructura del proyecto en el explorador lateral izquierdo.

---

## 7. Entender la estructura del proyecto

```
SENA/                           ← Raíz del proyecto (entorno virtual)
├── info/                       ← 🔹 AQUÍ ESTÁ EL CÓDIGO DEL PROYECTO
│   ├── manage.py               ← Comando principal de Django
│   ├── requirements.txt        ← Lista de dependencias
│   ├── Procfile                ← Config de despliegue
│   ├── info/                   ← Configuración central
│   │   └── settings.py         ← ⚠️ Archivo más importante de configuración
│   ├── applications/           ← Las 11 apps del proyecto
│   ├── templates/              ← Plantillas HTML
│   ├── static/                 ← CSS, imágenes
│   └── media/                  ← Archivos subidos
├── Lib/                        ← Paquetes Python (NO tocar)
├── Scripts/                    ← Ejecutables del venv (NO tocar)
└── pyvenv.cfg                  ← Config del venv
```

> **Regla clave:** Todos los comandos de Django se ejecutan DENTRO de la carpeta `info/`, donde está `manage.py`.

---

## 8. Crear y activar el entorno virtual

El proyecto ya incluye un entorno virtual (`SENA/` es el venv), pero puede que esté configurado para otro equipo. Es mejor crear uno nuevo.

### Opción A — Usar el venv existente (si ya funciona)

**Windows (CMD):**

```cmd
cd C:\Users\TuUsuario\...\SENA
Scripts\activate
```

**Windows (PowerShell):**

```powershell
cd C:\Users\TuUsuario\...\SENA
.\Scripts\Activate.ps1
```

> Si PowerShell da error de permisos, ejecuta primero:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**macOS/Linux:**

```bash
cd /ruta/a/SENA
source bin/activate
```

Cuando el venv está activo, verás `(SENA)` al inicio de la línea de tu terminal.

### Opción B — Crear un venv nuevo (recomendado si hay problemas)

```cmd
cd C:\Users\TuUsuario\...\
python -m venv SENA_env
cd SENA_env
Scripts\activate
```

Luego copia la carpeta `info/` dentro de `SENA_env/`.

---

## 9. Instalar dependencias Python

Con el entorno virtual **activado**, navega a la carpeta `info/` e instala las dependencias:

```cmd
cd info
pip install -r requirements.txt
```

Este comando lee el archivo `requirements.txt` e instala todos los paquetes necesarios:

| Paquete | Propósito |
|---|---|
| Django==5.2.8 | Framework web |
| channels==4.0.0 | WebSockets |
| daphne==4.0.0 | Servidor ASGI |
| gunicorn==23.0.0 | Servidor WSGI producción |
| PyMySQL==1.1.2 | Conector MySQL |
| redis==5.0.1 | Cliente Redis |
| channels-redis==4.1.0 | Channels ↔ Redis |
| openai>=1.0.0 | API moderación |
| python-dotenv | Variables de entorno |
| Pillow==11.1.0 | Procesamiento de imágenes (fotos de perfil, archivos) |

> ⚠️ **IMPORTANTE:** Si `Pillow` no aparece en tu `requirements.txt`, agrégalo manualmente antes de ejecutar `pip install`. Sin Pillow, Django no puede manejar campos `ImageField` (fotos de perfil, fotos de grupo, archivos de publicaciones).

**Verificar que Django se instaló correctamente:**

```cmd
python -m django --version
```

Debe mostrar: `5.2.8`

---

## 10. Crear la base de datos MySQL

Necesitas crear la base de datos antes de ejecutar el proyecto.

**Paso 1:** Abre MySQL desde la terminal:

```cmd
mysql -u root -p
```

Ingresa la contraseña (por defecto: `root`).

**Paso 2:** Crea la base de datos:

```sql
CREATE DATABASE infosena_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Paso 3:** Verifica que se creó:

```sql
SHOW DATABASES;
```

Debes ver `infosena_db` en la lista.

**Paso 4:** Sal de MySQL:

```sql
exit
```

---

## 11. Crear archivo .env

El proyecto actualmente tiene secretos hardcodeados en `settings.py`. Vamos a crear un archivo `.env` para manejarlos de forma segura.

**Ubicación:** Crea el archivo en `info/.env` (al lado de `manage.py`)

```env
# ============================================
# CONFIGURACIÓN DE INFOSENA - ENTORNO LOCAL
# ============================================

# Django
SECRET_KEY=django-insecure-h2*$b!#5upbewe)h)c0s074)!675xs#zj4sj$sx3yd*bn55k!1
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos MySQL
DB_NAME=infosena_db
DB_USER=root
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=3306

# Redis (para WebSockets / Chat)
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Email (Gmail SMTP)
EMAIL_HOST_USER=perezpolancocarlosmario@gmail.com
EMAIL_HOST_PASSWORD=zdotpwzoijuwwsts

# API de Moderación - Google Perspective
PERSPECTIVE_API_KEY=AIzaSyClFIfrYfiMOtH3nDTgBtYNSxS08en0fH4

# API de Moderación - OpenAI (opcional)
OPENAI_API_KEY=
```

> ⚠️ **SEGURIDAD:** Este archivo `.env` **NUNCA** debe subirse a GitHub. Lo protegeremos con `.gitignore` en el manual 02.

---

## 12. Configurar settings.py para usar .env

> **Nota:** Este paso es una **sugerencia de mejora**. El proyecto funciona sin este cambio, pero es una buena práctica de seguridad para cuando se despliegue en producción.

Si deseas que `settings.py` lea las variables del archivo `.env`, modifica las siguientes líneas en `info/info/settings.py`:

**Al inicio del archivo, después de los imports, añade:**

```python
from dotenv import load_dotenv
load_dotenv()
```

**Luego reemplaza los valores hardcodeados por variables de entorno:**

```python
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-por-defecto')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

```python
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

```python
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
PERSPECTIVE_API_KEY = os.getenv('PERSPECTIVE_API_KEY', '')
```

> **Recuerda:** `python-dotenv` ya está en `requirements.txt`, así que no necesitas instalar nada adicional.

---

## 13. Ejecutar migraciones

Las **migraciones** son instrucciones que Django usa para crear las tablas en la base de datos a partir de los modelos Python.

**Asegúrate de estar en la carpeta `info/` con el venv activado:**

```cmd
cd info
```

**Paso 1:** Crear archivos de migración (si no existen):

```cmd
python manage.py makemigrations
```

**Paso 2:** Aplicar migraciones a la base de datos:

```cmd
python manage.py migrate
```

Deberías ver una lista de migraciones aplicándose:

```
Applying contenttypes.0001_initial... OK
Applying auth.0001_initial... OK
Applying registro.0001_initial... OK
...
```

Si ves errores de conexión a MySQL, revisa que:
- MySQL esté corriendo
- La base de datos `infosena_db` exista
- El usuario y contraseña en `settings.py` sean correctos

---

## 14. Crear superusuario

El **superusuario** es la cuenta de administrador de Django. Te permite acceder al panel de administración en `/admin/`.

```cmd
python manage.py createsuperuser
```

Te pedirá:
- **Username:** elige uno (ej: `admin`)
- **Email:** tu correo
- **Password:** una contraseña segura (mínimo 8 caracteres)

---

## 15. Ejecutar el proyecto localmente

### Paso 1: Verificar que MySQL esté corriendo

```cmd
mysql -u root -p -e "SELECT 1"
```

### Paso 2: Verificar que Redis esté corriendo

```cmd
redis-cli ping
```

Debe responder `PONG`.

### Paso 3: Ejecutar el servidor de desarrollo

Desde la carpeta `info/`:

```cmd
python manage.py runserver
```

Deberías ver:

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
March 10, 2026 - 00:00:00
Django version 5.2.8, using settings 'info.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Paso 4: Abrir en el navegador

Abre tu navegador y ve a:

| URL | Qué muestra |
|---|---|
| `http://127.0.0.1:8000/` | Página de inicio (landing) |
| `http://127.0.0.1:8000/sesion/login/` | Formulario de login |
| `http://127.0.0.1:8000/registro/` | Formulario de registro |
| `http://127.0.0.1:8000/admin/` | Panel de administración Django |

> **Nota sobre el chat:** El chat en tiempo real (WebSocket) solo funcionará si ejecutas el servidor con Daphne en lugar de `runserver`. Para desarrollo normal, `runserver` es suficiente, pero si quieres probar el chat:
>
> ```cmd
> daphne -b 127.0.0.1 -p 8000 info.asgi:application
> ```

---

## 16. Validar que todo funciona

Realiza estas pruebas paso a paso:

| # | Prueba | Resultado esperado |
|---|---|---|
| 1 | Abrir `http://127.0.0.1:8000/` | Se muestra la landing page con el logo InfoSENA |
| 2 | Abrir `http://127.0.0.1:8000/admin/` | Se muestra el panel de admin de Django |
| 3 | Login en admin con superusuario | Accedes al panel de administración |
| 4 | Ir a `http://127.0.0.1:8000/registro/` | Se muestra el formulario de registro |
| 5 | Crear un usuario Aprendiz | Se envía código de verificación al email |
| 6 | Verificar código | Cuenta creada correctamente |
| 7 | Login con documento + contraseña | Accedes al home/feed |
| 8 | Ver la lista de amigos | Muestra sugerencias de amigos |

---

## 17. Errores comunes y soluciones

### Error: `ModuleNotFoundError: No module named 'django'`

**Causa:** El entorno virtual no está activado o Django no está instalado.

**Solución:**
```cmd
Scripts\activate
pip install -r requirements.txt
```

### Error: `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`

**Causa:** MySQL no está corriendo o la configuración de conexión es incorrecta.

**Solución:**
1. Verifica que MySQL esté corriendo:
   - Windows: Busca "Servicios" → MySQL → Iniciar
   - Linux: `sudo systemctl start mysql`
2. Verifica las credenciales en `settings.py`

### Error: `django.db.utils.OperationalError: (1049, "Unknown database 'infosena_db'")`

**Causa:** La base de datos no existe.

**Solución:**
```cmd
mysql -u root -p -e "CREATE DATABASE infosena_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Error: `redis.exceptions.ConnectionError: Error connecting to localhost:6379`

**Causa:** Redis no está corriendo.

**Solución:**
- Windows: Inicia Memurai o Redis en WSL
- Linux: `sudo systemctl start redis-server`
- macOS: `brew services start redis`

> **Nota:** Si no necesitas probar el chat en tiempo real, puedes comentar temporalmente la configuración de `CHANNEL_LAYERS` en `settings.py` para que el proyecto arranque sin Redis.

### Error: `ImportError: No module named 'pymysql'`

**Causa:** PyMySQL no está instalado.

**Solución:**
```cmd
pip install PyMySQL==1.1.2
```

### Error en PowerShell: `Scripts\Activate.ps1 cannot be loaded because running scripts is disabled`

**Causa:** Política de ejecución de PowerShell restrictiva.

**Solución:**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Error: `No changes detected` al hacer `makemigrations`

**Causa:** Las apps no están registradas en `INSTALLED_APPS` o las migraciones ya existen.

**Solución:** Verifica que todas las apps estén en `INSTALLED_APPS` en `settings.py`. Si las migraciones ya existen, solo ejecuta `migrate`.

---

## 18. Checklist Final

Antes de continuar con el siguiente manual, verifica:

- [ ] Python 3.12+ instalado y en PATH
- [ ] MySQL instalado y corriendo
- [ ] Redis instalado y corriendo (o Memurai en Windows)
- [ ] VS Code instalado con extensiones Python y Django
- [ ] Proyecto abierto en VS Code
- [ ] Entorno virtual activado (ves `(SENA)` en la terminal)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Base de datos `infosena_db` creada en MySQL
- [ ] Archivo `.env` creado en `info/.env`
- [ ] Migraciones ejecutadas sin errores
- [ ] Superusuario creado
- [ ] Servidor corriendo en `http://127.0.0.1:8000/`
- [ ] Landing page visible en el navegador
- [ ] Panel de admin accesible en `/admin/`

---

> **Siguiente paso:** [02_inicializacion_git.md](02_inicializacion_git.md) — Inicialización de Git y control de versiones
