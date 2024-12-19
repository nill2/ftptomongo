"""Initialize the package and provide access to its main functionality."""

import config

# Import symbols from ftptomongo module
from .ftptomongo import run_ftp_server

# Import symbols from config module in the same directory


# Define __all__ to control what is imported when using "from package import *"
__all__ = ["run_ftp_server", "config"]

# Initialization code (optional)
print("Initializing your_package...")
