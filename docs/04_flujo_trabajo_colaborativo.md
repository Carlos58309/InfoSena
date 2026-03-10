# 04 — Flujo de Trabajo Colaborativo con Git y GitHub

> **Proyecto:** InfoSENA — Red social institucional SENA  
> **Requisito previo:** Manuales 02 y 03 completados (Git + GitHub configurados)

---

## Tabla de Contenidos

1. [¿Qué son las ramas?](#1-qué-son-las-ramas)
2. [Estrategia de ramas recomendada](#2-estrategia-de-ramas-recomendada)
3. [Crear y trabajar con ramas](#3-crear-y-trabajar-con-ramas)
4. [Conventional Commits](#4-conventional-commits)
5. [Pull Requests (PR)](#5-pull-requests-pr)
6. [Revisión de código](#6-revisión-de-código)
7. [Flujo diario de trabajo](#7-flujo-diario-de-trabajo)
8. [Resolución de conflictos](#8-resolución-de-conflictos)
9. [Buenas prácticas](#9-buenas-prácticas)
10. [Checklist final](#10-checklist-final)

---

## 1. ¿Qué son las ramas?

Una **rama** (branch) en Git es una línea independiente de desarrollo. Piensa en ella como una "copia paralela" de tu proyecto donde puedes experimentar sin afectar el código principal.

**Analogía:** Imagina que tienes un documento de Word y quieres hacer cambios grandes. En vez de editar el original, creas una copia, trabajas en ella, y cuando estás seguro de que todo funciona, reemplazas el original con la copia mejorada.

```
main ──────●────●────●──────────────●──── (código estable)
                      \            /
feature/chat ──────────●────●────●        (nueva función)
```

- La línea superior (`main`) siempre tiene código que **funciona**.
- La línea inferior (`feature/chat`) es donde se desarrolla una nueva función.
- Cuando la nueva función está lista, se **fusiona** (merge) con `main`.

---

## 2. Estrategia de ramas recomendada

Para un proyecto como **InfoSENA** (equipo pequeño, proyecto académico), se recomienda la estrategia **Git Flow simplificada**:

### Ramas principales

| Rama | Propósito | ¿Quién trabaja aquí? |
|---|---|---|
| `main` | Código estable, listo para producción | Solo se actualiza vía merge/PR |
| `develop` | Código en desarrollo activo | Se integran las features aquí |

### Ramas temporales

| Tipo | Nombre | Ejemplo | Cuándo usarla |
|---|---|---|---|
| **Feature** | `feature/nombre` | `feature/chat-grupal` | Desarrollar una función nueva |
| **Fix** | `fix/nombre` | `fix/login-documento` | Corregir un error |
| **Hotfix** | `hotfix/nombre` | `hotfix/seguridad-xss` | Corregir error urgente en producción |

### Flujo visual

```
main ─────────────────────●──────────────●────── (releases)
                         /              /
develop ────●────●────●─────●────●────●──────── (integración)
            \        /       \        /
feature/A ───●──●──●          \      /
                               \    /
feature/B ──────────────────────●──●
```

### Crear las ramas principales

Si solo tienes `main`, crea `develop`:

```cmd
git checkout main
git checkout -b develop
git push -u origin develop
```

---

## 3. Crear y trabajar con ramas

### Crear una rama nueva

Antes de empezar cualquier tarea, crea una rama desde `develop`:

```cmd
# 1. Asegúrate de estar en develop y actualizado
git checkout develop
git pull origin develop

# 2. Crea la nueva rama
git checkout -b feature/nombre-descriptivo
```

**Ejemplos de nombres de rama para InfoSENA:**

```cmd
git checkout -b feature/moderacion-imagenes
git checkout -b feature/notificaciones-push
git checkout -b fix/error-login-aprendiz
git checkout -b fix/chat-mensajes-duplicados
```

### Ver en qué rama estás

```cmd
git branch
```

La rama actual tiene un asterisco (*):

```
  develop
* feature/moderacion-imagenes
  main
```

### Cambiar de rama

```cmd
git checkout develop        # ir a develop
git checkout main           # ir a main
git checkout feature/chat   # ir a la rama de chat
```

> **Importante:** Antes de cambiar de rama, asegúrate de haber hecho commit de tus cambios o de haberlos guardado con `git stash`.

### Guardar cambios temporalmente (stash)

Si necesitas cambiar de rama pero no quieres hacer commit de cambios incompletos:

```cmd
# Guardar cambios temporalmente
git stash

# Cambiar de rama
git checkout otra-rama

# Recuperar los cambios guardados (al volver)
git checkout mi-rama
git stash pop
```

### Subir la rama a GitHub

```cmd
git push -u origin feature/nombre-descriptivo
```

### Eliminar una rama (después de merge)

```cmd
# Local
git branch -d feature/nombre-descriptivo

# Remoto
git push origin --delete feature/nombre-descriptivo
```

---

## 4. Conventional Commits

**Conventional Commits** es una convención para escribir mensajes de commit claros y estandarizados. Esto facilita:

- Entender qué se hizo sin leer el código
- Generar changelogs automáticos
- Buscar en el historial de manera eficiente

### Formato

```
tipo(alcance): descripción breve

[cuerpo opcional]

[notas de pie opcionales]
```

### Tipos de commit

| Tipo | Cuándo usarlo | Ejemplo para InfoSENA |
|---|---|---|
| `feat` | Nueva funcionalidad | `feat(chat): agregar soporte para mensajes de voz` |
| `fix` | Corrección de error | `fix(login): corregir validación de documento vacío` |
| `docs` | Documentación | `docs: agregar manual de despliegue` |
| `style` | Formato (no afecta lógica) | `style(templates): formatear indentación en home.html` |
| `refactor` | Reestructurar código | `refactor(moderacion): simplificar pipeline de filtros` |
| `test` | Agregar o modificar tests | `test(amistades): agregar test de solicitud duplicada` |
| `chore` | Mantenimiento | `chore: actualizar requirements.txt` |
| `perf` | Mejoras de rendimiento | `perf(busqueda): optimizar consulta de usuarios` |

### Reglas para buenos mensajes

1. **Usa imperativo:** "agregar", "corregir", "eliminar" (NO "agregué", "se corrigió")
2. **Máximo 72 caracteres** en la primera línea
3. **Sé específico:** "fix(chat): corregir envío de archivos mayores a 10MB" es mejor que "fix: arreglar bug"
4. **Un commit = un cambio lógico.** No mezcles cosas distintas en un solo commit.

### Ejemplos específicos para InfoSENA

```cmd
git commit -m "feat(registro): agregar validación de correo institucional SENA"
git commit -m "fix(chat): corregir error al enviar imagen en chat grupal"
git commit -m "feat(moderacion): implementar detección de leetspeak en comentarios"
git commit -m "fix(perfil): corregir carga de foto de perfil en formato WEBP"
git commit -m "refactor(notificaciones): separar lógica de señales en archivo propio"
git commit -m "chore: agregar Pillow a requirements.txt"
git commit -m "docs: crear manual de preparación de entorno local"
```

---

## 5. Pull Requests (PR)

Un **Pull Request** (PR) es una solicitud para **fusionar** los cambios de una rama a otra. Es el mecanismo principal de colaboración en GitHub.

### ¿Por qué usar Pull Requests?

- Otro miembro del equipo puede **revisar tu código** antes de fusionarlo
- Se documenta **qué se cambió y por qué**
- Se pueden automatizar verificaciones (tests, linting)
- Queda un historial claro de cada cambio

### Crear un Pull Request

**Paso 1:** Sube tu rama a GitHub (si no lo hiciste)

```cmd
git push -u origin feature/mi-nueva-funcion
```

**Paso 2:** Ve a GitHub y crea el PR

1. Ve a tu repositorio en GitHub
2. Verás un banner amarillo: **"feature/mi-nueva-funcion had recent pushes — Compare & pull request"**
3. Click en **"Compare & pull request"**

**Paso 3:** Llena el formulario

| Campo | Qué poner |
|---|---|
| **Title** | Mismo formato que Conventional Commits: `feat(chat): agregar chat grupal` |
| **Base branch** | `develop` (la rama donde quieres fusionar) |
| **Compare branch** | `feature/mi-nueva-funcion` (tu rama) |
| **Description** | Describe qué hiciste, por qué y cómo probarlo |

**Ejemplo de descripción:**

```markdown
## ¿Qué cambia este PR?
Se agrega la funcionalidad de crear grupos de chat con múltiples participantes.

## Cambios realizados
- Nuevo modelo `Chat` con campo `is_group`
- Vista `crear_grupo` en chat/views.py
- Template `crear_grupo.html`
- Ruta `/chat/crear-grupo/`

## Cómo probar
1. Iniciar sesión como cualquier usuario
2. Ir a /chat/
3. Click en "Crear grupo"
4. Seleccionar 2+ participantes
5. Verificar que el grupo aparece en la lista de chats

## Capturas de pantalla
(Pegar imágenes si es un cambio visual)
```

**Paso 4:** Click en **"Create pull request"**

### Fusionar un Pull Request

Después de la revisión (si trabajan en equipo) o directamente (si trabajas solo):

1. Click en **"Merge pull request"** (botón verde)
2. Click en **"Confirm merge"**
3. Opcionalmente, elimina la rama: **"Delete branch"**

### Actualizar tu entorno local después del merge

```cmd
git checkout develop
git pull origin develop
```

---

## 6. Revisión de código

Si trabajan en equipo, la revisión de código es fundamental para mantener la calidad.

### ¿Qué revisar?

| Aspecto | Preguntas clave |
|---|---|
| **Funcionalidad** | ¿El código hace lo que dice el PR? |
| **Seguridad** | ¿Hay contraseñas hardcodeadas? ¿Hay inyección SQL? ¿Se valida la entrada del usuario? |
| **Legibilidad** | ¿Se entiende el código? ¿Tiene nombres descriptivos? |
| **Eficiencia** | ¿Las consultas a la BD son eficientes? ¿Hay N+1 queries? |
| **Templates** | ¿Se usa `{% csrf_token %}` en los formularios? |
| **Archivos** | ¿Se subieron archivos que no deberían estar (`.env`, `__pycache__`)? |

### Cómo hacer una revisión en GitHub

1. En el PR, ve a la pestaña **"Files changed"**
2. Revisa línea por línea
3. Para comentar en una línea específica, click en el `+` azul que aparece al pasar el cursor
4. Escribe tu comentario
5. Al terminar, click en **"Review changes"** → selecciona:
   - **Comment:** solo dejo comentarios
   - **Approve:** apruebo los cambios
   - **Request changes:** hay cosas que deben corregirse

---

## 7. Flujo diario de trabajo

Siguiendo esta rutina diaria, mantendrás un flujo de trabajo ordenado:

### Al iniciar el día

```cmd
# 1. Activar entorno virtual
cd SENA
Scripts\activate
cd info

# 2. Ir a develop y actualizar
git checkout develop
git pull origin develop

# 3. Si estás continuando una tarea, ir a tu rama
git checkout feature/mi-tarea

# 4. Si empiezas algo nuevo, crear rama
git checkout -b feature/nueva-tarea
```

### Durante el trabajo

```cmd
# Cada vez que completes un cambio lógico:
git status                          # Ver qué cambió
git add .                           # Agregar cambios
git commit -m "feat(app): descripción"  # Commitear
```

**¿Cada cuánto hacer commit?**
- Después de completar cada función o corrección
- Antes de salir a comer o pausar el trabajo
- Nunca esperes a tener "todo listo" — haz commits frecuentes y pequeños

### Al finalizar el día

```cmd
# Subir cambios a GitHub
git push origin feature/mi-tarea
```

### Al completar una tarea

```cmd
# 1. Subir rama
git push origin feature/mi-tarea

# 2. Crear Pull Request en GitHub (desde el navegador)
# 3. Fusionar el PR (después de revisión si trabajan en equipo)

# 4. Volver a develop y actualizar
git checkout develop
git pull origin develop

# 5. Eliminar rama local
git branch -d feature/mi-tarea
```

---

## 8. Resolución de conflictos

Los **conflictos** ocurren cuando dos personas modifican las mismas líneas del mismo archivo. Git no sabe cuál de las dos versiones conservar y te pide que decidas.

### ¿Cuándo ocurren?

- Al hacer `git merge` de dos ramas que tocaron el mismo archivo
- Al hacer `git pull` cuando tu compañero y tú editaron lo mismo
- Al fusionar un PR en GitHub

### Cómo resolver un conflicto

**Paso 1:** Git te muestra el conflicto así:

```python
def login_view(request):
<<<<<<< HEAD
    # Tu versión (actual)
    usuario = Usuario.objects.get(documento=request.POST['documento'])
=======
    # Versión de tu compañero (entrante)
    usuario = Usuario.objects.filter(documento=request.POST.get('documento')).first()
>>>>>>> feature/otra-rama
```

**Paso 2:** Decide qué versión mantener:

- **Opción A:** Quedarte con tu versión (borrar las líneas del compañero)
- **Opción B:** Quedarte con la versión del compañero (borrar tus líneas)
- **Opción C:** Combinar ambas (lo más común — tomar lo mejor de cada una)

**Paso 3:** Edita el archivo eliminando los marcadores `<<<<<<<`, `=======`, `>>>>>>>` y dejando solo el código final:

```python
def login_view(request):
    # Versión combinada
    usuario = Usuario.objects.filter(documento=request.POST.get('documento')).first()
```

**Paso 4:** Guarda y comunica a Git que resolviste el conflicto:

```cmd
git add archivo_con_conflicto.py
git commit -m "fix: resolver conflicto en login_view"
```

### Resolver conflictos en VS Code

VS Code tiene una interfaz visual para conflictos. Cuando detecta uno, te muestra:

- **Accept Current Change** → tu versión
- **Accept Incoming Change** → la versión entrante
- **Accept Both Changes** → incluir ambas
- **Compare Changes** → ver lado a lado

Es más fácil y visual que editar manualmente.

### Prevenir conflictos

- Comunícate con tu equipo sobre quién trabaja en qué archivo
- Haz commits frecuentes y pequeños
- Haz `git pull` antes de empezar a trabajar cada día
- Divide el trabajo por features/apps, no por archivos

---

## 9. Buenas prácticas

### Para Git

| Práctica | Razón |
|---|---|
| Haz commits pequeños y frecuentes | Más fácil de revisar y revertir |
| Escribe mensajes descriptivos | Facilita el historial |
| Nunca trabajes directamente en `main` | Mantener código estable |
| Actualiza tu rama con `develop` frecuentemente | Menos conflictos |
| Revisa `git status` antes de cada commit | Asegurarte de no incluir archivos no deseados |
| Usa `.gitignore` desde el inicio | Prevenir subir archivos sensibles |

### Para Pull Requests

| Práctica | Razón |
|---|---|
| Un PR = una feature o fix | Más fácil de revisar |
| Describe qué cambiaste y cómo probarlo | Ayuda al revisor |
| No dejes PRs abiertos más de 2-3 días | Evita conflictos acumulados |
| Responde a los comentarios de revisión | Comunicación clara |

### Para el equipo

| Práctica | Razón |
|---|---|
| Definir estándar de commits (Conventional Commits) | Consistencia |
| Usar un tablero de tareas (GitHub Projects) | Organización |
| No modificar `settings.py` sin avisar | Afecta a todos |
| Compartir el `.env.example` (sin valores reales) | Saber qué variables se necesitan |

---

## 10. Checklist Final

Antes de continuar con el siguiente manual, verifica que:

- [ ] Entiendes qué son las ramas y para qué sirven
- [ ] Tienes las ramas `main` y `develop` creadas
- [ ] Sabes crear una rama: `git checkout -b feature/nombre`
- [ ] Sabes cambiar entre ramas: `git checkout nombre`
- [ ] Conoces la convención de Conventional Commits
- [ ] Sabes crear un Pull Request en GitHub
- [ ] Sabes fusionar un PR
- [ ] Sabes resolver conflictos básicos
- [ ] Conoces el flujo diario: pull → trabajar → commit → push → PR

---

> **Siguiente paso:** [05_configuracion_proyecto.md](05_configuracion_proyecto.md) — Configuración de servicios externos
