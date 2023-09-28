'''
This it a config file that contains all the secrets for the app
'''

# config.py
import os

# FTP server configuration
FTP_ROOT = os.path.expanduser("~") # old "~/ftp/"
FTP_PORT = 2121
FTP_HOST = os.getenv("FTP_HOST", "localhost")
# change this to github secrets once move to production and use server deployments
FTP_USER = "user" # ${{ secrets.FTP_USER }}
FTP_PASSWORD = "password" # ${{ secrets.FTP_PASSWORD }}

# MongoDB configuration
# Check if the code is running in a test environment
if "GHA_TESTS" in os.environ:
    # Use localhost address for tests
    MONGO_HOST = ("localhost")
else:
    # Use the cloud-based MongoDB address for production
    MONGO_HOST = ("mongodb+srv://appUser:qovkm123@cluster0.qfjxdop.mongodb.net/"
    "?retryWrites=true&w=majority&appName=AtlasApp"
    )
# ${{ secrets.MONGO_HOST }}
MONGO_PORT = 27017
MONGO_DB = "nill-home"
MONGO_COLLECTION = "nill-home-photos"

ERROR_LVL = "debug"
