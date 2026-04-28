"""Catálogo de especialidades y sus colores Tailwind."""

ESPECIALIDADES = [
    'Alergología', 'Anestesiología', 'Cardiología', 'Cirugía General',
    'Cirugía Plástica', 'Clínica Médica', 'Dermatología', 'Endocrinología',
    'Fisiatría', 'Gastroenterología', 'Geriatría', 'Ginecología',
    'Hematología', 'Infectología', 'Inmunología', 'Medicina Familiar',
    'Medicina del Deporte', 'Nefrología', 'Neumología', 'Neurología',
    'Nutrición', 'Obstetricia', 'Odontología', 'Oftalmología',
    'Oncología', 'Otorrinolaringología', 'Pediatría', 'Psicología',
    'Psiquiatría', 'Radiología', 'Reumatología', 'Traumatología',
    'Urología',
]

# Cada entrada es una tupla: (bg_solid, bg_soft, text, border)
# Se escriben como strings literales para que Tailwind CDN las detecte.
ESPECIALIDADES_COLORES = {
    'Alergología':          ('bg-yellow-500',  'bg-yellow-50',  'text-yellow-700',  'border-yellow-200'),
    'Anestesiología':       ('bg-purple-500',  'bg-purple-50',  'text-purple-700',  'border-purple-200'),
    'Cardiología':          ('bg-rose-500',    'bg-rose-50',    'text-rose-700',    'border-rose-200'),
    'Cirugía General':      ('bg-red-600',     'bg-red-50',     'text-red-700',     'border-red-200'),
    'Cirugía Plástica':     ('bg-fuchsia-500', 'bg-fuchsia-50', 'text-fuchsia-700', 'border-fuchsia-200'),
    'Clínica Médica':       ('bg-blue-500',    'bg-blue-50',    'text-blue-700',    'border-blue-200'),
    'Dermatología':         ('bg-amber-500',   'bg-amber-50',   'text-amber-700',   'border-amber-200'),
    'Endocrinología':       ('bg-teal-500',    'bg-teal-50',    'text-teal-700',    'border-teal-200'),
    'Fisiatría':            ('bg-orange-600',  'bg-orange-50',  'text-orange-700',  'border-orange-200'),
    'Gastroenterología':    ('bg-lime-500',    'bg-lime-50',    'text-lime-700',    'border-lime-200'),
    'Geriatría':            ('bg-stone-500',   'bg-stone-50',   'text-stone-700',   'border-stone-200'),
    'Ginecología':          ('bg-pink-500',    'bg-pink-50',    'text-pink-700',    'border-pink-200'),
    'Hematología':          ('bg-red-500',     'bg-red-50',     'text-red-700',     'border-red-200'),
    'Infectología':         ('bg-green-500',   'bg-green-50',   'text-green-700',   'border-green-200'),
    'Inmunología':          ('bg-emerald-600', 'bg-emerald-50', 'text-emerald-700', 'border-emerald-200'),
    'Medicina Familiar':    ('bg-green-600',   'bg-green-50',   'text-green-700',   'border-green-200'),
    'Medicina del Deporte': ('bg-orange-700',  'bg-orange-50',  'text-orange-700',  'border-orange-200'),
    'Nefrología':           ('bg-emerald-500', 'bg-emerald-50', 'text-emerald-700', 'border-emerald-200'),
    'Neumología':           ('bg-sky-600',     'bg-sky-50',     'text-sky-700',     'border-sky-200'),
    'Neurología':           ('bg-violet-500',  'bg-violet-50',  'text-violet-700',  'border-violet-200'),
    'Nutrición':            ('bg-lime-600',    'bg-lime-50',    'text-lime-700',    'border-lime-200'),
    'Obstetricia':          ('bg-pink-600',    'bg-pink-50',    'text-pink-700',    'border-pink-200'),
    'Odontología':          ('bg-cyan-600',    'bg-cyan-50',    'text-cyan-700',    'border-cyan-200'),
    'Oftalmología':         ('bg-cyan-500',    'bg-cyan-50',    'text-cyan-700',    'border-cyan-200'),
    'Oncología':            ('bg-slate-600',   'bg-slate-50',   'text-slate-700',   'border-slate-200'),
    'Otorrinolaringología': ('bg-indigo-500',  'bg-indigo-50',  'text-indigo-700',  'border-indigo-200'),
    'Pediatría':            ('bg-sky-500',     'bg-sky-50',     'text-sky-700',     'border-sky-200'),
    'Psicología':           ('bg-fuchsia-600', 'bg-fuchsia-50', 'text-fuchsia-700', 'border-fuchsia-200'),
    'Psiquiatría':          ('bg-purple-600',  'bg-purple-50',  'text-purple-700',  'border-purple-200'),
    'Radiología':           ('bg-zinc-500',    'bg-zinc-50',    'text-zinc-700',    'border-zinc-200'),
    'Reumatología':         ('bg-red-700',     'bg-red-50',     'text-red-700',     'border-red-200'),
    'Traumatología':        ('bg-orange-500',  'bg-orange-50',  'text-orange-700',  'border-orange-200'),
    'Urología':             ('bg-blue-600',    'bg-blue-50',    'text-blue-700',    'border-blue-200'),
}

ESPECIALIDAD_COLOR_DEFAULT = ('bg-gray-500', 'bg-gray-50', 'text-gray-700', 'border-gray-200')


def color_especialidad(nombre):
    """Devuelve la tupla de clases Tailwind para una especialidad."""
    return ESPECIALIDADES_COLORES.get(nombre, ESPECIALIDAD_COLOR_DEFAULT)
