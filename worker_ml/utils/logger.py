"""
Logger estructurado para el Worker ML.

En GitHub Actions los logs van a stdout y se indexan por nivel.
El formato incluye timestamp, nivel, módulo y mensaje para facilitar
el debug post-mortem cuando el worker corre a las 3am sin supervisión.
"""

import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Retorna un logger configurado con el nombre del módulo.
    Es idempotente: múltiples llamadas con el mismo nombre devuelven
    el mismo logger sin duplicar handlers.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",      
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger