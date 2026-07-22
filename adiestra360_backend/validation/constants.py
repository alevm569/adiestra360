"""
Constantes de la fase de validación:

- El cuestionario SUS (System Usability Scale), estándar de usabilidad de 10
  ítems con escala Likert 1–5, adaptado a Adiestra360 y en español.
- El cálculo del puntaje SUS (0–100) y su interpretación cualitativa.
- La convención para marcar datos SIMULADOS: los usuarios simulados usan un
  dominio de email reservado, de modo que las métricas puedan separar los
  datos reales (los ~15 usuarios de la prueba) de los sintéticos.

Fuente de verdad única: el frontend pide las preguntas al endpoint de la
encuesta, así el texto y la polaridad no se duplican.
"""

# --- Cuestionario SUS ---------------------------------------------------------
# `positive=True`  -> ítem redactado en positivo (mejor = 5).
# `positive=False` -> ítem redactado en negativo (mejor = 1).
# El orden importa: q1..q10 se corresponden 1 a 1 con los campos del modelo.
SUS_QUESTIONS = [
    {'id': 1,  'positive': True,
     'text': 'Creo que me gustaría usar Adiestra360 con frecuencia.'},
    {'id': 2,  'positive': False,
     'text': 'Encontré Adiestra360 innecesariamente complejo.'},
    {'id': 3,  'positive': True,
     'text': 'Pensé que Adiestra360 era fácil de usar.'},
    {'id': 4,  'positive': False,
     'text': 'Creo que necesitaría ayuda de una persona con conocimientos técnicos '
             'para poder usar Adiestra360.'},
    {'id': 5,  'positive': True,
     'text': 'Encontré que las funciones de Adiestra360 estaban bien integradas.'},
    {'id': 6,  'positive': False,
     'text': 'Pensé que había demasiada inconsistencia en Adiestra360.'},
    {'id': 7,  'positive': True,
     'text': 'Imagino que la mayoría de la gente aprendería a usar Adiestra360 '
             'muy rápido.'},
    {'id': 8,  'positive': False,
     'text': 'Encontré Adiestra360 muy engorroso de usar.'},
    {'id': 9,  'positive': True,
     'text': 'Me sentí muy seguro/a usando Adiestra360.'},
    {'id': 10, 'positive': False,
     'text': 'Necesité aprender muchas cosas antes de poder empezar a usar '
             'Adiestra360.'},
]

# Escala de respuesta (1 = Totalmente en desacuerdo ... 5 = Totalmente de acuerdo).
SUS_SCALE = [
    {'value': 1, 'label': 'Totalmente en desacuerdo'},
    {'value': 2, 'label': 'En desacuerdo'},
    {'value': 3, 'label': 'Neutral'},
    {'value': 4, 'label': 'De acuerdo'},
    {'value': 5, 'label': 'Totalmente de acuerdo'},
]

SUS_ITEM_COUNT = len(SUS_QUESTIONS)  # 10


def compute_sus_score(answers):
    """
    Calcula el puntaje SUS (0–100) a partir de las 10 respuestas (1–5).

    `answers`: secuencia de 10 enteros en el orden q1..q10.
    - Ítems impares (positivos): aporte = valor - 1.
    - Ítems pares (negativos):  aporte = 5 - valor.
    - Suma de aportes (0–40) × 2.5 = puntaje 0–100.
    """
    if len(answers) != SUS_ITEM_COUNT:
        raise ValueError(f'SUS requiere {SUS_ITEM_COUNT} respuestas.')
    total = 0
    for question, value in zip(SUS_QUESTIONS, answers):
        value = int(value)
        if not 1 <= value <= 5:
            raise ValueError('Cada respuesta SUS debe estar entre 1 y 5.')
        total += (value - 1) if question['positive'] else (5 - value)
    return round(total * 2.5, 1)


def sus_adjective(score):
    """
    Interpretación cualitativa del puntaje SUS según la escala de adjetivos
    de Bangor et al. (2009). Útil para el informe de validación.
    """
    if score is None:
        return None
    if score >= 85:
        return 'Excelente'
    if score >= 72:
        return 'Bueno'
    if score >= 52:
        return 'Aceptable'  # ~ media de la industria (68)
    if score >= 39:
        return 'Pobre'
    return 'Deficiente'


# --- Marca de datos simulados -------------------------------------------------
# Los usuarios simulados se crean con emails @<dominio> reservado. Las métricas
# separan reales vs. simulados por este dominio, sin tocar el modelo Users.
SIMULATED_EMAIL_DOMAIN = 'sim.adiestra360.local'


def is_simulated_email(email):
    """True si el email pertenece a un usuario simulado (seed_validation)."""
    return bool(email) and email.lower().endswith('@' + SIMULATED_EMAIL_DOMAIN)
