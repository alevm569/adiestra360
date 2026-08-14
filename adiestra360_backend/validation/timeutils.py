"""
Fechas locales a partir de datetimes, sin depender de la base de datos.

**Por qué existe este módulo.** El atajo natural de Django para agrupar por día
—`values_list('session_date__date')`— traduce a `CONVERT_TZ()` en MySQL, y
`CONVERT_TZ` devuelve **NULL** si el servidor no tiene cargadas las tablas de
zonas horarias (`mysql.time_zone_name`), que es el caso por defecto en MySQL y
en la mayoría de los MySQL gestionados. El resultado no es un error: es un NULL
silencioso que convierte "días activos por usuario" en 1 para todo el mundo.

En SQLite (que es donde corren los tests) el mismo lookup funciona, así que el
fallo solo aparece en producción. Por eso el día se calcula siempre en Python.
"""
from django.utils import timezone


def local_day(value):
    """Fecha (date) local de un datetime, o None."""
    if value is None:
        return None
    if timezone.is_aware(value):
        return timezone.localtime(value).date()
    return value.date()


def days_by_key(pairs):
    """
    Agrupa (clave, datetime) en {clave: set(fechas locales)}.

    Es el reemplazo de `values_list(..., 'campo__date').distinct()`: se traen
    los datetimes y se agrupan aquí.
    """
    result = {}
    for key, value in pairs:
        day = local_day(value)
        if day is not None:
            result.setdefault(key, set()).add(day)
    return result
