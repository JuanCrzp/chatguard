Persistencia (opcional)
=======================

El proyecto incluye un módulo opcional `src/storage/db.py` con SQLAlchemy.
No se usa por defecto; los repos siguen en memoria. Para producción, puedes:

- Definir `DB_URL` en `.env` (MySQL, Postgres o SQLite).
- Crear tablas y usar repositorios que consuman la sesión SQLAlchemy.

Ejemplo de uso de sesión:

```python
from src.storage.db import get_session

with get_session() as s:
    # s.add(...)
    # s.query(...)
    pass
```

Alembic (sugerido)
------------------

1) Instala alembic y genera estructura:
   - pip install alembic
   - alembic init infra/alembic

2) Configura `sqlalchemy.url` en `infra/alembic/alembic.ini` usando tu `DB_URL`.

3) Genera una migración:
   - alembic revision -m "init tables"
   - edita el archivo para crear tablas según tus modelos
   - alembic upgrade head

Esto permite versionar cambios en esquema sin afectar la lógica actual.
