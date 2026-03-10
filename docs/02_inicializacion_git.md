# 02 — Inicialización de Git

> **Proyecto:** InfoSENA — Red social institucional SENA  
> **Stack:** Django 5.2.8 + MySQL + Redis + Channels  
> **Requisito previo:** Manual 01 completado (entorno local funcionando)

---

## Tabla de Contenidos

1. [IMPORTANTE: Dónde trabajar en este proyecto](#1-importante-dónde-trabajar-en-este-proyecto)
2. [¿Qué es Git?](#2-qué-es-git)
3. [¿Para qué sirve Git?](#3-para-qué-sirve-git)
4. [Instalar Git](#4-instalar-git)
5. [Configuración inicial de Git](#5-configuración-inicial-de-git)
6. [Crear el archivo .gitignore correcto](#6-crear-el-archivo-gitignore-correcto)
7. [Inicializar el repositorio](#7-inicializar-el-repositorio)
8. [Verificar el estado con git status](#8-verificar-el-estado-con-git-status)
9. [Agregar archivos con git add](#9-agregar-archivos-con-git-add)
10. [Hacer el primer commit](#10-hacer-el-primer-commit)
11. [Ver el historial de commits](#11-ver-el-historial-de-commits)
12. [Comandos esenciales de Git](#12-comandos-esenciales-de-git)
13. [Errores comunes y soluciones](#13-errores-comunes-y-soluciones)
14. [Checklist final](#14-checklist-final)

---

## 1. IMPORTANTE: Dónde trabajar en este proyecto

> ⚠️ **ANTES DE HACER CUALQUIER COSA, lee esta sección.**

Este proyecto tiene una estructura especial. La carpeta `SENA/` es un **entorno virtual de Python** (venv). El código real está dentro de `SENA/info/`.

```
SENA/                    ← Entorno virtual (NO subir a Git)
├── Scripts/             ← Ejecutables del venv
├── Lib/                 ← Paquetes instalados
└── info/                ← 🔹 TU PROYECTO ESTÁ AQUÍ
    ├── manage.py
    ├── requirements.txt
    ├── Procfile
    ├── .gitignore
    ├── .env
    ├── applications/    ← Las 11 apps Django
    ├── info/            ← settings.py, urls.py, asgi.py
    ├── templates/
    └── static/
```

### Primer paso OBLIGATORIO: Ubicarse en `info/`

**Abre tu terminal cmd y ejecuta:**

```cmd
cd "C:\Users\Julian Andres\OneDrive\Desktop\Para Clase\InfoSena\SENA\info"
```

**TODOS** los comandos de Git de este manual se ejecutan desde la carpeta `info/`. Si no estás en `info/`, los comandos no funcionarán correctamente.

**Verificar que estás en el lugar correcto:**
```cmd
dir manage.py
```

Si ves `manage.py` en la lista, estás en la carpeta correcta. Si dice "no se encontró", ejecuta el `cd` de arriba.

**¿Por qué `info/` y no `SENA/`?** Porque `SENA/` contiene el entorno virtual (`Lib/`, `Scripts/`, `Include/`) que pesa cientos de MB y **nunca debe subirse a GitHub**. Al inicializar Git dentro de `info/`, solo versionamos el código del proyecto.

---

## 2. ¿Qué es Git?

**Git** es un **sistema de control de versiones distribuido**. En palabras simples:

- Es una herramienta que **guarda un historial de todos los cambios** que haces en tu código.
- Cada vez que "guardas" un cambio en Git (se llama **commit**), Git crea una **foto** del estado de tu proyecto en ese momento.
- Puedes **volver atrás** a cualquier versión anterior si algo se rompe.
- Permite que **varias personas trabajen** en el mismo proyecto sin pisarse los cambios.

**Analogía:** Piensa en Git como el "Ctrl+Z" más poderoso del mundo. No solo deshace el último cambio, sino que guarda **cada versión** de tu proyecto y te deja navegar entre ellas.

---

## 3. ¿Para qué sirve Git?

| Beneficio | Explicación |
|---|---|
| **Historial completo** | Puedes ver qué cambió, cuándo y quién lo cambió |
| **Reversión** | Si algo se rompe, vuelves a una versión que funcionaba |
| **Trabajo en equipo** | Cada persona trabaja en su copia y luego se combinan los cambios |
| **Ramas** | Puedes experimentar con nuevas funciones sin afectar el código principal |
| **Respaldo** | Si se daña tu computadora, el código está en GitHub (nube) |
| **Documentación** | Los mensajes de commit documentan qué se hizo y por qué |

---

## 4. Instalar Git

### Windows

1. Ve a [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Descarga el instalador (se descarga automáticamente)
3. Ejecuta el instalador
4. Durante la instalación, acepta las opciones por defecto **EXCEPTO:**
   - En "Adjusting your PATH environment" → selecciona **"Git from the command line and also from 3rd-party software"**
   - En "Configuring the line ending conversions" → selecciona **"Checkout Windows-style, commit Unix-style line endings"**
5. Finaliza la instalación

**Verificar instalación:**

```cmd
git --version
```

Debe mostrar algo como: `git version 2.47.1.windows.1`

### macOS

```bash
# Git viene preinstalado en macOS. Verifica:
git --version

# Si no está instalado:
xcode-select --install
# O con Homebrew:
brew install git
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install git
git --version
```

---

## 5. Configuración inicial de Git

Antes de usar Git, debes decirle tu nombre y correo. Esto aparecerá en cada commit que hagas.

**Abre una terminal y ejecuta estos comandos** (reemplaza con TUS datos):

```cmd
git config --global user.name "Tu Nombre Completo"
git config --global user.email "tu.correo@ejemplo.com"
```

**Ejemplo real:**

```cmd
git config --global user.name "Julian Andres"
git config --global user.email "julian.andres@misena.edu.co"
```

**Configuraciones adicionales recomendadas:**

```cmd
git config --global init.defaultBranch main
git config --global core.autocrlf true
```

Estas líneas hacen:
- `init.defaultBranch main` → La rama principal se llama `main` (no `master`)
- `core.autocrlf true` → Maneja correctamente las diferencias de fin de línea entre Windows y Linux

**Verificar tu configuración:**

```cmd
git config --list
```

---

## 6. Crear el archivo .gitignore correcto

> ⚠️ **NOTA:** Existe un `.gitignore` en la carpeta `SENA/` pero fue generado por el venv y contiene solo `*` (bloquea todo). Necesitamos crear uno nuevo y correcto dentro de `info/`.

El archivo `.gitignore` le dice a Git qué archivos y carpetas **NO debe rastrear**. Esto es crucial para:
- No subir archivos con contraseñas (`.env`)
- No subir el entorno virtual
- No subir archivos temporales o de caché
- No subir archivos de la base de datos

**Crea el archivo `info/.gitignore`** con este contenido:

```gitignore
# =============================================
# .gitignore para InfoSENA (Django + MySQL + Redis)
# =============================================

# ---- Entorno Virtual de Python ----
venv/
env/
.venv/
ENV/
SENA/
Lib/
Scripts/
Include/
pyvenv.cfg

# ---- Python ----
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
dist/
build/
*.egg

# ---- Variables de entorno (SECRETOS) ----
.env
.env.local
.env.production
.env.*.local

# ---- Django ----
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
staticfiles/

# ---- Media (archivos subidos por usuarios) ----
media/chat_archivos/
media/grupos/
media/perfiles/
media/perfils/
media/publicaciones/

# ---- MySQL ----
*.sql
*.sql.gz

# ---- IDE / Editor ----
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# ---- Sistema Operativo ----
*.tmp
*.bak
*.orig
```

### ¿Qué excluye cada sección?

| Sección | Qué excluye | Por qué |
|---|---|---|
| **Entorno Virtual** | `Lib/`, `Scripts/`, etc. | Pesan mucho y se regeneran con `pip install` |
| **Python** | `__pycache__/`, `.pyc` | Archivos compilados temporales |
| **Variables de entorno** | `.env` | ⚠️ **CONTIENE CONTRASEÑAS Y CLAVES API** |
| **Django** | `staticfiles/`, logs | Archivos generados automáticamente |
| **Media** | Archivos de `media/` | Fotos y archivos subidos por usuarios |
| **IDE** | `.vscode/`, `.idea/` | Configuración personal del editor |
| **Sistema** | `.DS_Store`, `Thumbs.db` | Archivos del sistema operativo |

> ⚠️ **ADVERTENCIA DE SEGURIDAD:** El archivo `.env` contiene contraseñas de Gmail, claves API y la clave secreta de Django. **Si se sube a GitHub, cualquiera puede ver tus credenciales.** Por eso **DEBE** estar en `.gitignore`.

---

## 7. Inicializar el repositorio

> ⚠️ **Recuerda:** Debes estar en la carpeta `info/` (ver sección 1).

Ahora sí, vamos a crear el repositorio Git.

**Abre la terminal en VS Code** (`Ctrl + Ñ` o `Ctrl + Backtick`) y ejecuta:

```cmd
cd info
git init
```

Deberías ver:

```
Initialized empty Git repository in .../info/.git/
```

Esto crea una carpeta oculta `.git/` dentro de `info/` que contiene todo el historial de Git.

### Si dice "Reinitialized existing Git repository..."

Eso significa que **ya existía un repositorio Git** en esa carpeta (alguien lo creó antes). En ese caso debes verificar a dónde apunta:

```cmd
git remote -v
```

**Si no muestra nada** → No hay remote configurado. Perfecto, lo configurarás en el Manual 03.

**Si muestra una URL de GitHub** → Ya está conectado a un repositorio. Ejemplo:

```
origin  https://github.com/OtroUsuario/OtroRepo.git (fetch)
origin  https://github.com/OtroUsuario/OtroRepo.git (push)
```

Si esa URL **no es tu cuenta de GitHub**, y quieres subirlo a tu propia cuenta:

```cmd
git remote set-url origin https://github.com/TU-USUARIO/TU-REPO.git
```

Verifica que cambió:
```cmd
git remote -v
```

> ⚠️ **IMPORTANTE:** Si el repositorio fue clonado de la cuenta de otro compañero, es necesario cambiar el remote para que apunte a TU cuenta antes de hacer `git push`. Si no, intentará subir al repositorio del otro.

---

## 8. Verificar el estado con `git status`

El comando `git status` te muestra qué archivos han cambiado, cuáles están listos para commit y cuáles no están rastreados.

```cmd
git status
```

Verás algo como:

```
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .gitignore
        Procfile
        applications/
        fix_usuarios.py
        info/
        manage.py
        media/
        requirements.txt
        static/
        templates/
```

**"Untracked files"** significa que Git ve estos archivos pero aún no los está rastreando. Necesitamos agregarlos.

> **Nota:** Si ves archivos como `__pycache__/` o `.env` en la lista, tu `.gitignore` no está funcionando. Revisa que esté guardado correctamente.

---

## 9. Agregar archivos con `git add`

El comando `git add` "prepara" archivos para ser incluidos en el próximo commit. Es como poner cartas en un sobre antes de enviarlo.

### Agregar todos los archivos (excepto los del .gitignore):

```cmd
git add .
```

El punto (`.`) significa "todo lo que esté en el directorio actual".

### Verificar qué se agregó:

```cmd
git status
```

Ahora verás los archivos en color **verde** bajo "Changes to be committed":

```
Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   Procfile
        new file:   applications/amistades/__init__.py
        new file:   applications/amistades/admin.py
        ...
```

### Si agregaste un archivo por error:

```cmd
git rm --cached nombre_del_archivo
```

Esto quita el archivo del staging sin eliminarlo de tu computadora.

---

## 10. Hacer el primer commit

Un **commit** es una "foto" del estado actual de tu proyecto con un mensaje descriptivo.

```cmd
git commit -m "feat: configuración inicial del proyecto InfoSENA"
```

Deberías ver algo como:

```
[main (root-commit) a1b2c3d] feat: configuración inicial del proyecto InfoSENA
 85 files changed, 5400 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 Procfile
 create mode 100644 applications/amistades/__init__.py
 ...
```

### ¿Qué significa el mensaje del commit?

- `feat:` → indica que es una nueva funcionalidad (convención "Conventional Commits")
- El texto describe **QUÉ** hiciste, no **CÓMO**

### Buenas prácticas para mensajes de commit:

| Prefijo | Cuándo usarlo | Ejemplo |
|---|---|---|
| `feat:` | Nueva funcionalidad | `feat: agregar sistema de chat grupal` |
| `fix:` | Corrección de errores | `fix: corregir error en login por documento` |
| `docs:` | Cambios en documentación | `docs: actualizar README con instrucciones` |
| `style:` | Formato, espacios, comas | `style: formatear código de views.py` |
| `refactor:` | Restructurar código sin cambiar funcionalidad | `refactor: simplificar lógica de moderación` |
| `chore:` | Tareas de mantenimiento | `chore: actualizar requirements.txt` |

---

## 11. Ver el historial de commits

```cmd
git log
```

Muestra el historial de commits:

```
commit a1b2c3d4e5f6... (HEAD -> main)
Author: Julian Andres <julian.andres@misena.edu.co>
Date:   Mon Mar 10 10:00:00 2026 -0500

    feat: configuración inicial del proyecto InfoSENA
```

**Versión compacta (una línea por commit):**

```cmd
git log --oneline
```

```
a1b2c3d feat: configuración inicial del proyecto InfoSENA
```

**Ver historial con gráfico de ramas:**

```cmd
git log --oneline --graph --all
```

---

## 12. Comandos esenciales de Git

Referencia rápida de los comandos más usados:

| Comando | Qué hace | Cuándo usarlo |
|---|---|---|
| `git init` | Crea un repositorio nuevo | Solo una vez al inicio |
| `git status` | Muestra el estado actual | Antes de cada commit para ver qué cambió |
| `git add .` | Agrega todos los archivos al staging | Cuando quieres preparar todos los cambios |
| `git add archivo.py` | Agrega un archivo específico | Cuando quieres commitear solo ciertos archivos |
| `git commit -m "mensaje"` | Crea un commit con un mensaje | Cada vez que completas un cambio lógico |
| `git log` | Muestra historial de commits | Para ver qué se hizo antes |
| `git log --oneline` | Historial resumido | Vista rápida del historial |
| `git diff` | Muestra cambios no agregados | Para ver exactamente qué modificaste |
| `git diff --staged` | Muestra cambios ya agregados | Para revisar antes de hacer commit |
| `git restore archivo.py` | Descarta cambios de un archivo | Cuando quieres revertir un cambio no commiteado |
| `git rm --cached archivo` | Quita un archivo del rastreo | Cuando agregaste algo por error |

### Flujo típico de trabajo:

```
1. Haces cambios en el código
2. git status           → Ves qué cambió
3. git add .            → Preparas los cambios
4. git commit -m "..."  → Guardas la "foto"
5. Repites
```

---

## 13. Errores comunes y soluciones

### Error: `fatal: not a git repository`

**Causa:** No estás dentro de una carpeta con Git inicializado.

**Solución:** Asegúrate de estar en la carpeta `info/`:
```cmd
cd info
git status
```

### Error: `warning: LF will be replaced by CRLF`

**Causa:** Diferencias de fin de línea entre Windows y Linux/macOS.

**Solución:** No es un error grave. Para ocultarlo:
```cmd
git config --global core.autocrlf true
```

### Error: Archivos que deberían estar ignorados aparecen en `git status`

**Causa:** Los archivos fueron rastreados antes de crear `.gitignore`.

**Solución:**
```cmd
git rm -r --cached .
git add .
git commit -m "fix: aplicar .gitignore correctamente"
```

> Esto quita todos los archivos del rastreo y los vuelve a agregar respetando `.gitignore`.

### Error: `Please tell me who you are` al hacer commit

**Causa:** No configuraste tu nombre y correo en Git.

**Solución:**
```cmd
git config --global user.name "Tu Nombre"
git config --global user.email "tu@correo.com"
```

### Error: Subiste `.env` o secretos a Git por error

**Causa:** El `.gitignore` no tenía `.env` o fue agregado tarde.

**Solución:**
```cmd
git rm --cached .env
git commit -m "fix: remover .env del rastreo de Git"
```

> ⚠️ **IMPORTANTE:** Aunque lo quites ahora, si ya hiciste push a GitHub, el archivo queda en el historial. Deberás **cambiar todas las contraseñas y claves API** que estaban en ese archivo.

---

## 14. Checklist Final

Antes de continuar con el siguiente manual, verifica:

- [ ] Git instalado (`git --version` muestra la versión)
- [ ] Nombre y correo configurados en Git
- [ ] Rama por defecto configurada como `main`
- [ ] Repositorio inicializado en la carpeta `info/` (existe `info/.git/`)
- [ ] Archivo `.gitignore` creado con todas las exclusiones correctas
- [ ] `.env` está listado en `.gitignore`
- [ ] `media/` está listado en `.gitignore`
- [ ] `__pycache__/` está listado en `.gitignore`
- [ ] Primer commit realizado exitosamente
- [ ] `git log` muestra el commit
- [ ] `git status` muestra "working tree clean" (sin cambios pendientes)

---

> **Siguiente paso:** [03_creacion_repo_github.md](03_creacion_repo_github.md) — Crear repositorio en GitHub y hacer push
