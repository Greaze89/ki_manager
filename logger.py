"""
Logging-System für KI Manager
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = "ki_manager", 
                level: int = logging.INFO,
                log_dir: str = "Logs") -> logging.Logger:
    """
    Richtet Logger mit File- und Console-Handler ein
    
    Args:
        name: Name des Loggers
        level: Logging-Level
        log_dir: Verzeichnis für Log-Dateien
        
    Returns:
        Konfigurierter Logger
    """
    
    # Log-Verzeichnis erstellen
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Logger erstellen
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Verhindere doppelte Handler
    if logger.handlers:
        return logger
    
    # Formatter definieren
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler (Rotating)
    log_file = log_path / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Nur Warnings+ auf Console
    console_handler.setFormatter(formatter)
    
    # Handler hinzufügen
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_function_call(func):
    """Decorator für Function-Call-Logging"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("ki_manager")
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

def log_performance(func):
    """Decorator für Performance-Monitoring"""
    import time
    
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("ki_manager")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f} seconds: {e}")
            raise
            
    return wrapper