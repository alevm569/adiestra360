"""
Fuente de verdad de los ejercicios de Nivel 1.

Para renombrar un ejercicio, cámbialo SOLO aquí (y agrega una migración de
datos que actualice la BD).

- `slug`: cómo se referencia el ejercicio en el código y en el quiz.
- `name`: cómo se muestra y cómo se guarda en la BD.

OJO: el emparejamiento código↔BD se hace por substring en minúsculas
(`slug.lower() in name.lower()`), así que el slug debe estar contenido en el
name — cuidado con las tildes ('aqui' NO calza con 'Aquí').

Este módulo no importa modelos a propósito, para que cualquier app pueda
importarlo sin riesgo de imports circulares.
"""

SIENTATE = 'siéntate'
ECHATE = 'échate'
AQUI = 'aquí'
QUEDATE = 'quédate'
LUGAR = 'lugar'
JUNTO = 'junto'

# Ejercicios de Nivel 1 en orden de dificultad: (slug, nombre para mostrar).
NIVEL1 = [
    (SIENTATE, 'Siéntate'),
    (ECHATE, 'Échate'),
    (AQUI, 'Aquí'),
    (QUEDATE, 'Quédate'),
    (LUGAR, 'Lugar'),
    (JUNTO, 'Junto'),
]

NIVEL1_SLUGS = [slug for slug, _ in NIVEL1]
NIVEL1_NAMES = {slug: name for slug, name in NIVEL1}
