"""Creación y migraciones del esquema de base de datos + datos seed."""
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from .config import Config
from .db import get_db


def init_db():
    """Crea tablas si no existen, aplica migraciones aditivas, garantiza admin."""
    db  = get_db()
    cur = db.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            nombre      VARCHAR(100) NOT NULL,
            apellido    VARCHAR(100) NOT NULL,
            email       VARCHAR(255) UNIQUE NOT NULL,
            password    VARCHAR(255) NOT NULL,
            rol         VARCHAR(20)  NOT NULL DEFAULT 'paciente',
            avisos      INT          NOT NULL DEFAULT 0,
            baneado     TINYINT(1)   NOT NULL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    for col, ddl in (
        ('avisos',  'INT NOT NULL DEFAULT 0'),
        ('baneado', 'TINYINT(1) NOT NULL DEFAULT 0'),
    ):
        cur.execute('''
            SELECT COUNT(*) AS c FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = %s
        ''', (Config.DB_NAME, col))
        if cur.fetchone()['c'] == 0:
            cur.execute(f'ALTER TABLE usuarios ADD COLUMN {col} {ddl}')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS medicos (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id       INT  NOT NULL UNIQUE,
            especialidad     VARCHAR(100) NOT NULL,
            matricula        VARCHAR(50),
            descripcion      TEXT,
            precio_consulta  DECIMAL(10,2) NULL,
            notas            TEXT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    for col, ddl in (
        ('precio_consulta', 'DECIMAL(10,2) NULL'),
        ('notas',           'TEXT NULL'),
    ):
        cur.execute('''
            SELECT COUNT(*) AS c FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'medicos' AND COLUMN_NAME = %s
        ''', (Config.DB_NAME, col))
        if cur.fetchone()['c'] == 0:
            cur.execute(f'ALTER TABLE medicos ADD COLUMN {col} {ddl}')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS turnos (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            medico_id   INT  NOT NULL,
            fecha       DATE NOT NULL,
            hora_inicio TIME NOT NULL,
            hora_fin    TIME NOT NULL,
            estado      VARCHAR(20) NOT NULL DEFAULT 'disponible',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (medico_id) REFERENCES medicos(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            turno_id      INT  NOT NULL UNIQUE,
            paciente_id   INT  NOT NULL,
            motivo        TEXT,
            estado        VARCHAR(20) NOT NULL DEFAULT 'confirmada',
            fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (turno_id)    REFERENCES turnos(id),
            FOREIGN KEY (paciente_id) REFERENCES usuarios(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS avisos (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            paciente_id  INT  NOT NULL,
            medico_id    INT  NULL,
            reserva_id   INT  NULL,
            tipo         VARCHAR(30) NOT NULL,
            motivo       TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (paciente_id) REFERENCES usuarios(id),
            FOREIGN KEY (medico_id)   REFERENCES medicos(id) ON DELETE SET NULL
        )
    ''')

    db.commit()

    cur.execute('SELECT COUNT(*) AS count FROM usuarios')
    if cur.fetchone()['count'] == 0:
        _seed(db)

    cur.execute("SELECT COUNT(*) AS count FROM usuarios WHERE rol = 'admin'")
    if cur.fetchone()['count'] == 0:
        pw = generate_password_hash('admin123')
        cur.execute(
            'INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s,%s,%s,%s,%s)',
            ('Admin', 'Sistema', 'admin@turnosalud.com', pw, 'admin')
        )
        db.commit()

    cur.close()
    db.close()


def _seed(db):
    cur     = db.cursor()
    doctors = [
        ('Carlos', 'Rodríguez', 'carlos@turnosalud.com', 'Cardiología',   'MN 12345',
         'Especialista en cardiología clínica con 15 años de experiencia.'),
        ('Ana',    'Martínez',  'ana@turnosalud.com',    'Pediatría',     'MN 23456',
         'Pediatra con enfoque en medicina preventiva y desarrollo infantil.'),
        ('Luis',   'García',    'luis@turnosalud.com',   'Traumatología', 'MN 34567',
         'Especialista en lesiones deportivas y cirugía ortopédica.'),
        ('María',  'López',     'maria@turnosalud.com',  'Dermatología',  'MN 45678',
         'Dermatóloga clínica y estética.'),
    ]
    for nombre, apellido, email, esp, mat, desc in doctors:
        pw = generate_password_hash('medico123')
        cur.execute('INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s,%s,%s,%s,%s)',
                    (nombre, apellido, email, pw, 'medico'))
        uid = cur.lastrowid
        cur.execute('INSERT INTO medicos (usuario_id, especialidad, matricula, descripcion) VALUES (%s,%s,%s,%s)',
                    (uid, esp, mat, desc))

    pw = generate_password_hash('paciente123')
    cur.execute('INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s,%s,%s,%s,%s)',
                ('Juan', 'Pérez', 'juan@email.com', pw, 'paciente'))

    cur.execute('SELECT id FROM medicos')
    medico_ids = [r['id'] for r in cur.fetchall()]

    today    = date.today()
    weekdays = 0
    offset   = 1
    while weekdays < 10:
        d = today + timedelta(days=offset)
        if d.weekday() < 5:
            for mid in medico_ids:
                for hour in ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
                             '14:00', '14:30', '15:00', '15:30', '16:00', '16:30']:
                    h, m  = map(int, hour.split(':'))
                    total = h * 60 + m + 30
                    end   = f"{total // 60:02d}:{total % 60:02d}"
                    cur.execute(
                        'INSERT INTO turnos (medico_id, fecha, hora_inicio, hora_fin) VALUES (%s,%s,%s,%s)',
                        (mid, d.isoformat(), hour, end)
                    )
            weekdays += 1
        offset += 1

    db.commit()
    cur.close()
