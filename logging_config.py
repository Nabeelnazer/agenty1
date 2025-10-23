"""
Comprehensive logging configuration for Xandy Learning AI Mentor System
"""
import logging
import os
from datetime import datetime
from typing import Optional
import json

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class XandyLogger:
    """Centralized logging system for Xandy Learning"""
    
    def __init__(self, name: str = "xandy_learning", log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for all logs
        os.makedirs('logs', exist_ok=True)
        file_handler = logging.FileHandler(
            f'logs/xandy_learning_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(
            f'logs/errors_{datetime.now().strftime("%Y%m%d")}.log'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional context"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with additional context"""
        if kwargs:
            context = json.dumps(kwargs, default=str)
            message = f"{message} | Context: {context}"
        
        self.logger.log(level, message)
    
    def log_user_action(self, user_id: str, action: str, details: dict = None):
        """Log user actions for audit trail"""
        self.info(f"User Action: {action}", user_id=user_id, details=details or {})
    
    def log_ai_interaction(self, mentor_id: str, student_id: str, interaction_type: str, details: dict = None):
        """Log AI interactions for monitoring"""
        self.info(f"AI Interaction: {interaction_type}", 
                 mentor_id=mentor_id, student_id=student_id, details=details or {})
    
    def log_database_operation(self, operation: str, table: str, record_id: str = None, details: dict = None):
        """Log database operations"""
        self.debug(f"Database: {operation}", table=table, record_id=record_id, details=details or {})
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log performance metrics"""
        self.info(f"Performance: {operation}", duration=f"{duration:.3f}s", details=details or {})

# Global logger instance
logger = XandyLogger()

# Convenience functions
def log_user_action(user_id: str, action: str, details: dict = None):
    """Log user action"""
    logger.log_user_action(user_id, action, details)

def log_ai_interaction(mentor_id: str, student_id: str, interaction_type: str, details: dict = None):
    """Log AI interaction"""
    logger.log_ai_interaction(mentor_id, student_id, interaction_type, details)

def log_database_operation(operation: str, table: str, record_id: str = None, details: dict = None):
    """Log database operation"""
    logger.log_database_operation(operation, table, record_id, details)

def log_performance(operation: str, duration: float, details: dict = None):
    """Log performance metric"""
    logger.log_performance(operation, duration, details)


