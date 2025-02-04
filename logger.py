import logging

# Global logger configuration
_global_logger = None


def set_global_logger(logger):
    """
    Set a global logger to redirect print statements

    Args:
        logger (callable): A function that takes a string and logs it
    """
    global _global_logger
    _global_logger = logger


def log_level_pretty(level) -> str:
    if level == logging.DEBUG:
        return "DEBUG"
    if level == logging.INFO:
        return "INFO"
    if level == logging.WARNING:
        return "WARNING"
    if level == logging.ERROR:
        return "ERROR"
    if level == logging.CRITICAL:
        return "CRITICAL"
    return "UNKNOWN"


def log_message(level, the_message):
    """
    Log a message using the global logger or print if no logger is set

    Args:
        level (int): Logging level (e.g., logging.INFO)
        message (str): Message to log
    """
    message = the_message
    if message[-1] == "^M":
        message = message[:-1]
    if _global_logger:
        if isinstance(_global_logger, logging.Logger):
            _global_logger.log(level, message)
        else:
            # If using Qt logger (not a standard logger), pass both level and message
            _global_logger(level, message)
    else:
        print(f"{log_level_pretty(level)}: {message}")
