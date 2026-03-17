# CODI — Sistema de Gestión de Información Electoral

Herramienta de escritorio para el procesamiento, validación y cargue de archivos electorales. Construido con Python + PySide6.

---

## Requisitos previos

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — gestor de paquetes y entornos virtuales
- [PostgreSQL 14+](https://www.postgresql.org/download/) corriendo localmente

---

## Instalación desde cero (después de clonar)

```bash
# 1. Clonar el repositorio
git clone https://github.com/JsMorales0301/data-codi.git
cd data-codi

# 2. Instalar dependencias y crear el entorno virtual automáticamente
uv sync

# 3. Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL
```

### Contenido de `.env`
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nombre_de_tu_base
DB_USER=postgres
DB_PASSWORD=tu_password
```

---

## Ejecutar la aplicación

```bash
uv run codi
```

---

## Estructura del proyecto

```
src/codi/
├── assets/          # Recursos estáticos (logo, íconos)
├── core/            # Lógica de negocio y utilidades
├── db/              # Conexión y modelos ORM (SQLAlchemy)
│   ├── connection.py
│   └── models.py
└── ui/              # Interfaz gráfica (PySide6)
    ├── main_window.py
    ├── styles.py
    └── views/
```

---

## Flujo de ramas (Git Flow simplificado)

| Rama     | Propósito                          |
|----------|------------------------------------|
| `dev`    | Desarrollo activo del día a día    |
| `main`   | Integración — candidatos a release |
| `master` | Producción — código estable        |

**Flujo normal:**
1. Trabajar en `dev` (o en una rama `feature/xxx` que luego se une a `dev`)
2. Cuando `dev` está estable → abrir **PR: `dev` → `main`**
3. Cuando `main` está probado → abrir **PR: `main` → `master`**

---

## Dependencias principales

| Paquete           | Versión  | Uso                        |
|-------------------|----------|----------------------------|
| PySide6           | ≥ 6.10   | Interfaz gráfica           |
| polars            | ≥ 1.39   | Procesamiento de datos     |
| SQLAlchemy        | ≥ 2.0    | ORM / acceso a BD          |
| psycopg2-binary   | ≥ 2.9    | Driver PostgreSQL          |
| python-dotenv     | ≥ 1.0    | Variables de entorno       |
