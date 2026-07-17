from django.db import models


class CharUUIDField(models.CharField):
    """
    Clave de 36 caracteres como CHAR (no VARCHAR).

    El esquema original de la BD se creó con SQL a mano usando `char(36)` para
    los ids. Django, en cambio, genera `varchar(36)` para un CharField.

    MySQL 8 usa collations NO PAD (utf8mb4_0900_ai_ci), donde los espacios de
    relleno del CHAR son significativos: una FK `varchar(36)` → `char(36)`
    nunca hace match y falla al insertar con el error 1452
    ("foreign key constraint fails"), aunque la FK se haya creado (Django
    desactiva los chequeos de FK durante `migrate`).

    Declarando CHAR aquí, las tablas que crea Django calzan con las que ya
    existen, y la BD de tests (que Django construye desde las migraciones)
    queda igual que la real.
    """

    def db_type(self, connection):
        return 'char(%s)' % self.max_length

    def rel_db_type(self, connection):
        # Tipo que usarán las columnas FK que apunten a este campo.
        return self.db_type(connection)
