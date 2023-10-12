'''
This it a config file that contains all the secrets for the app
'''
# config.py
import os
import subprocess

# FTP server configuration
FTP_ROOT = os.getenv("FTP_ROOT", os.path.expanduser("./"))
print("FTP_ROOT: " + FTP_ROOT)
FTP_PORT_STR = os.getenv("FTP_PORT", "")

# Check if the string is empty or not
if FTP_PORT_STR:
    # Convert the string to an integer if it's not empty
    FTP_PORT = int(FTP_PORT_STR)
else:
    # Use a default value (e.g., 2121) if the string is empty or not set
    FTP_PORT = 2121
FTP_HOST = "0.0.0.0"


# MongoDB configuration
MONGO_HOST = "localhost"
if "MONGO_HOST" in os.environ:
    MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
else:
    try:
        # Run the vlt command and capture its output
        VLT_COMMAND = "vlt secrets get --plaintext MONGO_HOST"
        MONGO_HOST = subprocess.check_output(VLT_COMMAND, shell=True, text=True)
        print("Value from hashicorp for MONGO_HOST: "+str(MONGO_HOST))
    except subprocess.CalledProcessError as hashi_e:
        # Handle errors, e.g., if the secret does not exist
        print(f"Error: {hashi_e}")

# Check if the code is running in a test environment
if "IS_TEST" in os.environ:
    # Use localhost address for tests
    if os.environ.get('IS_TEST') == "GHA":
        MONGO_HOST = "localhost"
        print("You are running in a GHA test environment: "+MONGO_HOST)
    else:
        print("You are running in a local test environment: "+MONGO_HOST)
    ERROR_LVL = "debug"
    MONGO_DB = "nill-test"
    FTP_USER = "user"
    FTP_PASSWORD = "password"
else:
    MONGO_DB = "nill-home"
    ERROR_LVL = "production"
    FTP_USER = os.getenv("FTP_USER", "user")
    FTP_PASSWORD = os.getenv("FTP_PASSWORD", "password")
    print("You are running in a prod environment: " + MONGO_HOST)
MONGO_PORT = 27017
MONGO_COLLECTION = "nill-home-photos"
