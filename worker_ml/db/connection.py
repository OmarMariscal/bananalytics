"""
Gestión de la conexión a Neon (PostgreSQL serverless).

Decisiones de diseño:
  - NullPool: Neon es serverless; las conexiones persistentes se cobran y
    pueden agotarse. NullPool abre y cierra una conexión por operación,
    que es exactamente lo que necesita un CRON job que corre una vez al día.
  - get_session() como context manager: garantiza commit/rollback/close
    aunque ocurra cualquier excepción dentro del bloque.
  - verificar_conexion() se llama al inicio de main.py para abortar limpio
    si Neon no responde, antes de desperdiciar tiempo de cómputo en GitHub Actions.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()

# Engine
# NullPool para workloads batch y entornos serverless
engine = create_engine(
    _settings.database_url.unicode_string(),
    poolclass = NullPool,
    echo = False, # True para debug SQL; nunca en producción (logs masivos)
)

LocalSession = sessionmaker(bind=engine, autocommit = False, autoflush = False)

#Context Manager de Sessión

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Proporciona una sesión de SQLAlchemy con manejo automático de
    commit, rollback y cierre.

    Uso:
        with get_session() as session:
            session.add(objeto)
    """
    session: Session = LocalSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        
# Utilidades

def check_connection() -> bool:
    """
    Ping liviano a la BD. Se llama al inicio de main.py para fail-fast
    si Neon no está disponible, en lugar de fallar a mitad del proceso.
    """
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        logger.info("✅ Conexión a Neon verificada correctamente.")
        return True
    except Exception as e:
        logger.error(f"❌ Fallo en la conexión a Neon: {e}")
        return False

def create_tables() -> None:
    """
    Crea todas las tablas definidas en modelos.py si no existen.
    Idempotente: seguro de llamar en cada ejecución del worker.
    """
    from db.models import Base # Import local para evitar ciclos
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tablas verificadas/creadas en la base de datos.")