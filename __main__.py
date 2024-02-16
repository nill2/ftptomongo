import os
import sys
import signal  # Import the signal module
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
print(sys.path)

from config import FTP_USER, FTP_ROOT, FTP_PORT, MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION
from config import FTP_PASSWORD, ERROR_LVL, FTP_HOST, FTP_PASSIVE_PORT_FROM, FTP_PASSIVE_PORT_TO
import ftptomongo 

def signal_handler(sig, frame):
    """
    Signal handler function to handle KeyboardInterrupt (Ctrl+C).
    """
    print("Ctrl+C detected. Exiting...")
    sys.exit(0)

def main():
    print("Executing ftptomongo package as a script")
    
    # Set the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Your main application logic goes here
    ftptomongo.run_ftp_server()

if __name__ == "__main__":
    main()
