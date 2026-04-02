# Guía de Contribución para BanAnalytics

Este documento establece los lineamientos técnicos y el flujo de trabajo para el desarrollo del proyecto BanAnalytics. Todos los miembros del equipo deben seguir estas instrucciones para mantener la consistencia del código y evitar conflictos en el repositorio.

## 1. Arquitectura del Repositorio (Monorepo)

El proyecto está estructurado en tres directorios principales, cada uno con su propio entorno virtual (`venv`) y archivo de dependencias (`requirements.txt`).

* **`api_gateway/`**: Contiene el Backend. Desarrollado con FastAPI, gestiona la conexión a la base de datos PostgreSQL (Neon) y la autenticación.
* **`cliente_local/`**: Contiene el Frontend (Aplicación de escritorio). Desarrollado con Flet, consume los endpoints expuestos por el `api_gateway`.
* **`worker_ml/`**: Contiene los scripts de Machine Learning. Desarrollado con Pandas y Scikit-Learn para el entrenamiento de modelos predictivos.

**Para el aislamiento de dependencias:** No se deben crear entornos virtuales (`venv`) ni archivos de variables de entorno (`.env`) en la raíz del repositorio. Todo aislamiento de dependencias debe realizarse exclusivamente dentro del subdirectorio correspondiente.

## 2. Flujo de Trabajo (GitHub Flow)

El desarrollo se gestionará mediante ramas (branches). No se harán *commits* directos a la rama `main` si no que a su propia rama de trabajo.

### Pasos para contribuir:

1.  **Sincronizar el repositorio local:**
    ```bash
    git checkout main
    git pull origin main
    ```
2.  **Crear una rama de trabajo:**
    Utiliza convenciones de nomenclatura estándar:
    * Para nuevas características: `git checkout -b feat/nombre-de-la-caracteristica`
    * Para corrección de errores: `git checkout -b fix/nombre-del-error`
3.  **Activar el entorno virtual:** (Ver sección 3).
4.  **Realizar Commits:**
    Agrega los cambios en tu directorio y redacta mensajes de commit descriptivos:
    ```bash
    git add .
    git commit -m "feat: Descripción técnica y concisa de los cambios realizados"
    ```
5.  **Subir la rama al repositorio remoto:**
    ```bash
    git push origin nombre-de-la-rama
    ```
6.  **Crear un Pull Request (PR):**
    Cuando consideres que tu trabajo está listo, debes abrir un pull request a la rama main. En GitHub, si te metes al repositorio original, verás la opción "compare & pull request" y ahí puedes enviar tus cambios a revisión.

## 3. Inicialización del Entorno de Desarrollo

Cada vez que se clona el repositorio, es necesario sincronizar el entorno virtual. Ejecuta los siguientes comandos en tu terminal (PowerShell) para asegurar la compatibilidad de las versiones. Esto es si no tienes el entorno virtual por ser tu primera ejecución:

1.  Navega al directorio correspondiente (ej. `cd api_gateway`).
2.  Crea el entorno virtual: 
    ```powershell
    python -m venv venv
    ```
3.  Activa el entorno virtual:
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
4.  Actualiza las herramientas base de empaquetado:
    ```powershell
    python -m pip install --upgrade pip setuptools wheel
    ```
5.  Instala las dependencias listadas:
    ```powershell
    pip install -r requirements.txt
    ```

*(Nota: Si instalas una nueva dependencia durante tu desarrollo, debes actualizar el archivo ejecutando `pip freeze > requirements.txt` e incluir este cambio en tu próximo commit).*

## 4. Directrices Técnicas por Módulo

### Para `cliente_local` (Frontend)
* **Modularidad:** La activación del entorno virtual no la debes hacer en tu carpeta de trabajo directamente (ej: `frontend`) sino que la debes hacer en la propia carpeta `app_local`
* **Variables de Entorno:** La URL base de la API debe almacenarse en el archivo `.env` local (`API_URL`). No codifiques URLs en duro (hardcoding) dentro de los archivos de Python.

### Para `api_gateway` (Backend)
* **Seguridad:** Las credenciales de conexión a la base de datos (`DATABASE_URL`) y las claves de encriptación (JWT Secrets) deben residir exclusivamente en el archivo `.env` local.
* **Documentación de API:** Define claramente los esquemas de entrada/salida (modelos de Pydantic) para facilitar la integración de los endpoints con el equipo de Frontend.

### Para `worker_ml` (Machine Learning)
* **Gestión de Modelos:** Los scripts deben exportar los modelos entrenados en formatos serializados (ej. `.pkl`). Estos archivos binarios deben ser excluidos del control de versiones asegurando su registro en el `.gitignore`.
* **Entregables:** El código de producción final debe entregarse como scripts ejecutables de Python (`.py`), no como celdas interactivas en Jupyter Notebooks (`.ipynb`).