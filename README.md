# TurnoSalud — Sistema de gestión de turnos médicos

Aplicación web para gestionar turnos médicos con tres roles: **administrador**, **médico** y **paciente**.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3 + Flask |
| Base de datos | MySQL (via PyMySQL) |
| Frontend | Tailwind CSS (CDN) + Alpine.js (CDN) + Inter (Google Fonts) |
| Templates | Jinja2 |

No requiere bundler ni pasos de build para el frontend.

---

## Requisitos previos

- **Python 3.8 o superior** — https://www.python.org/downloads/
- **XAMPP** (recomendado), WAMP o Laragon — traen MySQL + phpMyAdmin listos para usar
  - Descargar XAMPP: https://www.apachefriends.org/
  - Una vez instalado, abrí el **XAMPP Control Panel** y arrancá los módulos **Apache** y **MySQL**
- phpMyAdmin se accede desde el navegador en `http://localhost/phpmyadmin`

> **No hace falta** MySQL Workbench, ni cliente de línea de comandos, ni nada más. Toda la administración de la base se hace desde phpMyAdmin en el navegador.

---

## Setup completo (primera vez en una máquina)

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd turnosalud2-main
```

### 2. Crear y activar el entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

El prompt debería mostrar `(venv)` al inicio.

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Arrancar MySQL desde XAMPP

1. Abrí el **XAMPP Control Panel**
2. Click en **Start** al lado de **Apache**
3. Click en **Start** al lado de **MySQL**
4. Ambos tienen que estar en verde

> Si MySQL no arranca por conflicto de puerto (otro MySQL como servicio de Windows ocupando el 3306), XAMPP suele asignarlo al **3308**. Anotá ese número, lo vas a necesitar más abajo.

### 5. Crear la base de datos en phpMyAdmin

1. Andá a `http://localhost/phpmyadmin` en el navegador
2. Click en la pestaña **"Bases de datos"** (arriba)
3. Nombre: `turnosalud`
4. Cotejamiento: `utf8mb4_unicode_ci`
5. Click en **Crear**

### 6. Crear el archivo `.env`

Copiá `.env.example` a `.env`:

**Windows:**
```bash
copy .env.example .env
```

**Mac / Linux:**
```bash
cp .env.example .env
```

Abrí `.env` y editá los valores:

```
FLASK_SECRET_KEY=<una-string-larga-y-random>
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=turnosalud
FLASK_ENV=development
```

**Generar una `FLASK_SECRET_KEY` random:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Sobre `DB_PORT`:** poné el puerto que muestra MySQL en el XAMPP Control Panel. Default `3306`, pero si XAMPP lo asignó al `3308`, usá ese.

> ⚠️ El `.env` está en `.gitignore` — nunca se sube al repo. Cada máquina tiene el suyo.

### 7. Correr la app

```bash
python app.py
```

La **primera vez** Flask crea automáticamente todas las tablas y carga datos de prueba (médicos, paciente, turnos).

Abrí el navegador en:

```
http://127.0.0.1:5000
```

---

## Levantar la app después del setup inicial

Cada vez que querés trabajar:

1. Abrí XAMPP Control Panel → **Start** Apache + MySQL
2. En la terminal:
   ```bash
   venv\Scripts\activate
   python app.py
   ```
3. Navegador → `http://127.0.0.1:5000`

---

## Cuentas de prueba

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@turnosalud.com` | `admin123` |
| Médico | `carlos@turnosalud.com` | `medico123` |
| Médico | `ana@turnosalud.com` | `medico123` |
| Médico | `luis@turnosalud.com` | `medico123` |
| Médico | `maria@turnosalud.com` | `medico123` |
| Paciente | `juan@email.com` | `paciente123` |

---

## Roles y funcionalidades

### Administrador (`admin@turnosalud.com`)
- Dashboard con estadísticas globales (médicos, pacientes, turnos, reservas)
- Crear cuentas de médicos (especialidad se elige de un catálogo fijo de 33 especialidades)
- Eliminar médicos (solo si no tienen reservas futuras activas)
- Ver listado de pacientes registrados

### Médico (panel de gestión de agenda)
- Dashboard personal con stats y próximas reservas
- Agregar turnos en modo **simple** (uno) o **bloque** (múltiples con preview en vivo)
- Editar fecha y horario de un turno
- Habilitar / deshabilitar turnos sin eliminarlos
- Eliminar turnos sin paciente asignado
- Ver todas las reservas de sus pacientes
- **Mi perfil**: definir precio de consulta, reglas de convivencia y descripción profesional (se muestran al paciente al reservar)

### Paciente
- Registro propio con email y contraseña
- Buscar turnos disponibles filtrando por especialidad, médico y fecha (el dropdown de médico se filtra al elegir especialidad)
- Solo ve turnos cuya fecha+hora todavía no pasó
- Modal de reserva con precio visible, reglas de convivencia del médico y aviso si el día tiene alta demanda (>=70% reservado)
- Ver historial de turnos propios (próximos e historial cancelado)
- Cancelar una reserva confirmada

---

## Estructura del proyecto

```
turnosalud2-main/
├── app.py                          # Punto de entrada del servidor de desarrollo
├── wsgi.py                         # Punto de entrada para producción (waitress / gunicorn)
├── requirements.txt                # Dependencias Python
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore
├── turnosalud/                     # Paquete principal de la app
│   ├── __init__.py                 # App factory (create_app)
│   ├── config.py                   # Configuración desde variables de entorno
│   ├── constants.py                # Especialidades, colores, catálogos fijos
│   ├── db.py                       # Helpers de conexión a MySQL (PyMySQL)
│   ├── decorators.py               # Guards de sesión / roles
│   ├── filters.py                  # Filtros y helpers de Jinja
│   ├── schema.py                   # Creación de tablas + datos seed
│   ├── services.py                 # Lógica de negocio
│   └── blueprints/                 # Rutas separadas por rol
│       ├── public.py               # Landing, login, register
│       ├── paciente.py
│       ├── medico.py
│       └── admin.py
├── templates/                      # Vistas Jinja
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── admin/
│   ├── medico/
│   └── paciente/
└── tests/                          # Tests con pytest
    ├── conftest.py
    ├── test_auth.py
    ├── test_medico_admin.py
    └── test_paciente.py
```

---

## Base de datos

### Tablas

| Tabla | Descripción |
|---|---|
| `usuarios` | Pacientes, médicos y administradores |
| `medicos` | Especialidad, matrícula, descripción, **precio_consulta** y **notas** (reglas de convivencia) |
| `turnos` | Fecha, horario y estado de cada turno |
| `reservas` | Relación paciente ↔ turno con motivo y estado |
| `avisos` | Avisos / faltas registradas a un paciente |

### Estados de un turno

| Estado | Descripción |
|---|---|
| `disponible` | Visible y reservable por pacientes |
| `ocupado` | Tiene una reserva confirmada |
| `deshabilitado` | Ocultado por el médico, no reservable |

### Estados de una reserva

| Estado | Descripción |
|---|---|
| `confirmada` | Reserva activa |
| `cancelada` | Cancelada por el paciente |

### Catálogo de especialidades

Definido en [turnosalud/constants.py](turnosalud/constants.py) como `ESPECIALIDADES` (lista) y `ESPECIALIDADES_COLORES` (dict con clases Tailwind por especialidad). Incluye 33 especialidades médicas, cada una con su color asignado. Para agregar una nueva: editar ambas estructuras.

---

## Comandos útiles

**Levantar la app (cada vez):**
```bash
venv\Scripts\activate
python app.py
```

**Reinstalar dependencias:**
```bash
pip install -r requirements.txt
```

**Correr los tests:**
```bash
pytest
```

**Ver tablas en phpMyAdmin:**
Entrá a `http://localhost/phpmyadmin`, hacé click en `turnosalud` en el panel izquierdo y navegá las tablas (`usuarios`, `medicos`, `turnos`, `reservas`, `avisos`).

**Resetear la base de datos** (perdés todo):
1. En phpMyAdmin → click en `turnosalud` → pestaña **"Operaciones"** → **Eliminar la base de datos**
2. Volvé a crearla siguiendo el paso 5 del setup
3. `python app.py` la vuelve a llenar con datos seed

---

## Troubleshooting

| Error | Causa | Solución |
|---|---|---|
| `RuntimeError: Falta FLASK_SECRET_KEY` | No existe el `.env` o no tiene la key | Crear `.env` desde `.env.example` y completar |
| `Can't connect to MySQL server` | MySQL no arrancado o puerto incorrecto | XAMPP → Start MySQL. Verificar que `DB_PORT` del `.env` coincida con el del XAMPP Control Panel |
| `Unknown database 'turnosalud'` | No creaste la base en phpMyAdmin | Paso 5 del setup |
| `Access denied for user 'root'@'localhost'` | MySQL tiene contraseña | Editar `DB_PASSWORD` en el `.env` |
| `mysqli::real_connect HY000/2002` en phpMyAdmin | MySQL no está corriendo, o phpMyAdmin apunta a un puerto distinto al de MySQL | XAMPP → Start MySQL. Si MySQL está en 3308 pero phpMyAdmin busca 3306, editar `phpMyAdmin/config.inc.php` y agregar `$cfg['Servers'][$i]['port'] = '3308';` |
