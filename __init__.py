# __init__.py

# Import symbols from ftptomongo module
from .ftptomongo import run_ftp_server

# Import symbols from config module in the same directory
from . import config

# Define __all__ to control what is imported when using "from package import *"
__all__ = [
    'run_ftp_server',
    'config'
]

# Initialization code (optional)
print("Initializing your_package...")