# 03 — Creación del Repositorio en GitHub

> **Proyecto:** InfoSENA — Red social institucional SENA  
> **Requisito previo:** Manual 02 completado (Git inicializado, primer commit hecho)

---

## Tabla de Contenidos

1. [¿Qué es GitHub?](#1-qué-es-github)
2. [Diferencia entre Git y GitHub](#2-diferencia-entre-git-y-github)
3. [Crear una cuenta en GitHub](#3-crear-una-cuenta-en-github)
4. [Crear un repositorio en GitHub](#4-crear-un-repositorio-en-github)
5. [Autenticación: Token de acceso personal](#5-autenticación-token-de-acceso-personal)
6. [Conectar el repositorio local con GitHub](#6-conectar-el-repositorio-local-con-github)
7. [Hacer el primer push](#7-hacer-el-primer-push)
8. [Validar que todo se subió correctamente](#8-validar-que-todo-se-subió-correctamente)
9. [Clonar el repositorio en otro equipo](#9-clonar-el-repositorio-en-otro-equipo)
10. [Errores comunes y soluciones](#10-errores-comunes-y-soluciones)
11. [Checklist final](#11-checklist-final)

---

## 1. ¿Qué es GitHub?

**GitHub** es una plataforma en la nube que almacena repositorios Git. Piensa en ella como:

- **Google Drive para código** — tu código vive en la nube, accesible desde cualquier computadora.
- **Red social para desarrolladores** — puedes compartir proyectos, colaborar con otros y mostrar tu portafolio.
- **Plataforma de colaboración** — gestiona tareas, reporta errores, revisa código de otros.

**No es obligatorio usar GitHub**, pero es la plataforma más popular y muchos servicios de despliegue (Railway, Render, Vercel) se conectan directamente con GitHub.

---

## 2. Diferencia entre Git y GitHub

Es muy común confundirlos. Aquí está la diferencia:

| Aspecto | Git | GitHub |
|---|---|---|
| **¿Qué es?** | Herramienta de control de versiones | Plataforma web para alojar repos Git |
| **¿Dónde vive?** | En tu computadora (local) | En la nube (internet) |
| **¿Es obligatorio?** | Sí, para control de versiones | No, pero es muy útil |
| **¿Tiene interfaz gráfica?** | No (es por terminal) | Sí (página web) |
| **¿Necesita internet?** | No | Sí |
| **Alternativas** | — | GitLab, Bitbucket, Azure DevOps |
| **Analogía** | El procesador de texto (Word) | Google Drive (donde guardas el archivo) |

**Resumen:** Git es la herramienta que usas en tu computadora. GitHub es donde subes el resultado para respaldarlo y compartirlo.

---

## 3. Crear una cuenta en GitHub

Si ya tienes cuenta, salta al paso 4.

1. Ve a [https://github.com](https://github.com)
2. Click en **"Sign up"**
3. Ingresa:
   - **Email:** tu correo (preferiblemente el mismo que configuraste en Git)
   - **Password:** una contraseña segura
   - **Username:** un nombre de usuario (será parte de la URL de tus proyectos)
4. Verifica tu correo electrónico
5. Selecciona el plan **"Free"** (es suficiente)

> **Consejo:** Usa un nombre de usuario profesional. Este aparecerá en tus proyectos y puede ser parte de tu portafolio. Ejemplo: `julian-andres` o `julian-dev`.

---

## 4. Crear un repositorio en GitHub

### Paso 1: Ir a crear repositorio

1. Inicia sesión en GitHub
2. Click en el botón verde **"New"** (esquina superior izquierda) o ve directamente a [https://github.com/new](https://github.com/new)

### Paso 2: Configurar el repositorio

| Campo | Valor recomendado | Explicación |
|---|---|---|
| **Repository name** | `InfoSena` | Nombre corto y descriptivo |
| **Description** | `Red social institucional del SENA — Gestión de perfiles, publicaciones, chat en tiempo real, moderación de contenido con IA y sistema de amistades. Django 5.2 + MySQL + Redis + WebSockets.` | Descripción del proyecto |
| **Visibility** | **Public** | Public = cualquiera puede ver el código. Railway se conecta más fácil con repos públicos. Si prefieres **Private**, también funciona pero necesitarás conectar tu cuenta de GitHub en Railway. |
| **Add a README file** | ❌ **NO marcar** | Ya tenemos código local. Si marcas esto, GitHub crea un commit y luego `git push` fallará con error de conflicto. |
| **Add .gitignore** | ❌ **NO seleccionar** | Ya creamos nuestro `.gitignore` en el manual 02. Si seleccionas uno aquí, se duplicará y puede causar conflictos. |
| **Choose a license** | ❌ **None** | Puedes agregar una después si lo necesitas. |

> ⚠️ **MUY IMPORTANTE:** El repositorio debe crearse **completamente vacío**. Si marcas cualquiera de las 3 opciones (README, .gitignore o license), GitHub creará un commit inicial y cuando intentes hacer `git push` desde tu terminal, dará error porque tu repositorio local ya tiene historial de commits.

### Paso 3: Crear

Click en **"Create repository"**.

GitHub te mostrará una página con instrucciones. **No cierres esta página**, la necesitarás en el paso 6.

Verás algo parecido a esto en la sección **"…or push an existing repository from the command line"**:

```
git remote add origin https://github.com/TU_USUARIO/infosena.git
git branch -M main
git push -u origin main
```

Guarda esta URL. La necesitarás.

---

## 5. Autenticación: Token de acceso personal

Desde 2021, GitHub **ya no acepta contraseñas normales** para autenticarse desde la terminal. Necesitas un **Token de Acceso Personal (PAT)**.

### Crear un token

1. Ve a [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Click en **"Generate new token"** → **"Generate new token (classic)"**
3. Configura:

| Campo | Valor |
|---|---|
| **Note** | `InfoSENA - acceso local` |
| **Expiration** | `90 days` (o "No expiration" si prefieres) |
| **Scopes** | Marca ✅ `repo` (acceso completo a repositorios) |

4. Click en **"Generate token"**
5. **COPIA EL TOKEN INMEDIATAMENTE** — GitHub solo lo muestra una vez

> ⚠️ **SEGURIDAD:** Guarda el token en un lugar seguro (un gestor de contraseñas, por ejemplo). No lo compartas ni lo pongas en tu código.

### Alternativa: Autenticación con GitHub CLI (más fácil)

Si prefieres no manejar tokens manualmente:

1. Descarga GitHub CLI desde [https://cli.github.com/](https://cli.github.com/)
2. Instálalo
3. Ejecuta:

```cmd
gh auth login
```

4. Sigue las instrucciones interactivas (selecciona GitHub.com → HTTPS → autenticar en navegador)

---

## 6. Conectar el repositorio local con GitHub

Ahora vamos a conectar tu repositorio local (el que creaste en el manual 02) con el repositorio de GitHub.

**Abre la terminal en VS Code, asegúrate de estar en la carpeta `info/`:**

```cmd
cd info
```

### Paso 0 (IMPORTANTE): Verificar si ya existe un remote

Antes de agregar un remote, verifica si ya hay uno configurado:

```cmd
git remote -v
```

**Si no muestra nada** → No hay remote. Ve al Paso 1.

**Si muestra una URL** → Ya existe un remote. Ejemplo:

```
origin  https://github.com/OtroUsuario/OtroRepo.git (fetch)
origin  https://github.com/OtroUsuario/OtroRepo.git (push)
```

Si esa URL **no es de tu cuenta**, cámbiala con:

```cmd
git remote set-url origin https://github.com/TU_USUARIO/InfoSena.git
```

Verifica que cambió:
```cmd
git remote -v
```

Si ya apunta a tu repo, salta directamente al **Paso 3**.

### Paso 1: Agregar el remoto

```cmd
git remote add origin https://github.com/TU_USUARIO/infosena.git
```

> Reemplaza `TU_USUARIO` por tu nombre de usuario de GitHub.

**¿Qué hace este comando?**
- `git remote add` → agrega una conexión remota
- `origin` → es el nombre que le damos a esa conexión (convención estándar)
- La URL → es la dirección de tu repositorio en GitHub

### Paso 2: Verificar que se agregó

```cmd
git remote -v
```

Debe mostrar:

```
origin  https://github.com/TU_USUARIO/infosena.git (fetch)
origin  https://github.com/TU_USUARIO/infosena.git (push)
```

### Paso 3: Asegurar que la rama se llame main

```cmd
git branch -M main
```

Esto renombra tu rama actual a `main` si tenía otro nombre.

---

## 7. Hacer el primer push

**Push** = Enviar tus commits locales a GitHub.

```cmd
git push -u origin main
```

**¿Qué hace cada parte?**
- `git push` → envía los commits
- `-u` → establece `origin/main` como la rama de seguimiento (solo necesitas usar `-u` la primera vez)
- `origin` → el remoto al que envías
- `main` → la rama que envías

### Autenticación durante el push

Cuando ejecutes el push, te pedirá credenciales:

**Si usas Token (PAT):**
- **Username:** tu usuario de GitHub
- **Password:** pega el token (NO tu contraseña de GitHub)

> **En Windows:** Es posible que aparezca la ventana del "Credential Manager" de Windows. Es normal. Ingresa tu usuario y token ahí. Windows lo guardará para que no tengas que ingresarlo cada vez.

**Si usas GitHub CLI:** Se autentica automáticamente si ya hiciste `gh auth login`.

### Resultado esperado:

```
Enumerating objects: 85, done.
Counting objects: 100% (85/85), done.
Delta compression using up to 8 threads
Compressing objects: 100% (75/75), done.
Writing objects: 100% (85/85), 45.23 KiB | 1024 bytes/s, done.
Total 85 (delta 5), reused 0 (delta 0)
remote: Resolving deltas: 100% (5/5), done.
To https://github.com/TU_USUARIO/infosena.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## 8. Validar que todo se subió correctamente

### En GitHub:

1. Ve a `https://github.com/TU_USUARIO/infosena`
2. Deberías ver toda la estructura del proyecto:

```
infosena/
├── .gitignore
├── Procfile
├── manage.py
├── requirements.txt
├── fix_usuarios.py
├── applications/
├── info/
├── static/
└── templates/
```

### Verificar que los archivos correctos están excluidos:

| Archivo/Carpeta | ¿Debería estar en GitHub? | ¿Está? |
|---|---|---|
| `manage.py` | ✅ Sí | Verificar |
| `requirements.txt` | ✅ Sí | Verificar |
| `applications/` | ✅ Sí | Verificar |
| `templates/` | ✅ Sí | Verificar |
| `static/css/` | ✅ Sí | Verificar |
| `.gitignore` | ✅ Sí | Verificar |
| `.env` | ❌ **NO** | Verificar que NO esté |
| `__pycache__/` | ❌ **NO** | Verificar que NO esté |
| `media/perfiles/` | ❌ **NO** | Verificar que NO esté |
| `Lib/` | ❌ **NO** | Verificar que NO esté |
| `Scripts/` | ❌ **NO** | Verificar que NO esté |

> ⚠️ Si ves `.env` o `__pycache__` en GitHub, tu `.gitignore` no funcionó correctamente. Revisa el manual 02.

### En tu terminal local:

```cmd
git status
```

Debe mostrar:

```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

---

## 9. Clonar el repositorio en otro equipo

Si necesitas trabajar desde otro computador, o si un compañero necesita el código:

```cmd
git clone https://github.com/TU_USUARIO/infosena.git
cd infosena
```

Después de clonar, el compañero debe:

1. Crear un entorno virtual:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
2. Instalar dependencias:
   ```cmd
   pip install -r requirements.txt
   ```
3. Crear su propio `.env` (copiando las variables del manual 01)
4. Crear la base de datos local
5. Ejecutar migraciones:
   ```cmd
   python manage.py migrate
   ```

---

## 10. Errores comunes y soluciones

### Error: `fatal: remote origin already exists`

**Causa:** Ya habías agregado un remoto con el nombre `origin`.

**Solución:**
```cmd
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/infosena.git
```

### Error: `remote: Repository not found`

**Causa:** La URL del repositorio es incorrecta o el repositorio no existe.

**Solución:**
1. Verifica la URL en GitHub
2. Verifica que el repositorio fue creado
3. Si es privado, asegúrate de estar autenticado

### Error: `Authentication failed` o `403 Forbidden`

**Causa:** Token incorrecto, expirado, o estás usando tu contraseña en vez del token.

**Solución:**
1. Genera un nuevo token en GitHub Settings → Developer settings → Personal access tokens
2. En Windows, abre "Credential Manager" (Administrador de Credenciales) → Windows Credentials → busca `github.com` → elimínalo → intenta push de nuevo

```cmd
# Limpiar credenciales almacenadas en Windows
cmdkey /delete:git:https://github.com
```

### Error: `failed to push some refs to`

**Causa:** El repositorio remoto tiene cambios que no tienes localmente (por ejemplo, si creaste README al crear el repo).

**Solución:**
```cmd
git pull origin main --allow-unrelated-histories
git push origin main
```

### Error: `src refspec main does not match any`

**Causa:** No has hecho ningún commit aún.

**Solución:** Primero haz un commit (ver manual 02) y luego intenta push de nuevo.

### Error: Timeout o conexión lenta

**Causa:** Archivos muy grandes o conexión de internet lenta.

**Solución:**
1. Verifica que no estés subiendo `Lib/`, `media/` o archivos grandes
2. Revisa tu `.gitignore`
3. Si hay archivos grandes en el historial:
   ```cmd
   git count-objects -vH
   ```

---

## 11. Checklist Final

Antes de continuar con el siguiente manual, verifica:

- [ ] Cuenta de GitHub creada y verificada
- [ ] Repositorio `infosena` creado en GitHub (privado o público)
- [ ] Token de acceso personal generado (o GitHub CLI configurado)
- [ ] Remoto `origin` configurado (`git remote -v` muestra la URL)
- [ ] Rama principal es `main`
- [ ] Push completado sin errores
- [ ] Código visible en GitHub (navega a tu repositorio en el navegador)
- [ ] `.env` **NO** está visible en GitHub
- [ ] `__pycache__` **NO** está visible en GitHub
- [ ] `Lib/` y `Scripts/` **NO** están visibles en GitHub
- [ ] `media/` (archivos de usuario) **NO** está visible en GitHub

---

> **Siguiente paso:** [04_flujo_trabajo_colaborativo.md](04_flujo_trabajo_colaborativo.md) — Flujo de trabajo colaborativo con Git y GitHub
