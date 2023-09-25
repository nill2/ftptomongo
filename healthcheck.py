from flask import Flask
from config import FTP_ROOT, FTP_PORT, MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION
import os

app = Flask(__name__)

@app.route("/health")
def health_check():
    try:
        # Check FTP root directory
        if os.path.exists(FTP_ROOT):
            return "FTP server is healthy\n", 200
        else:
            return "FTP server is not healthy\n", 500
    except Exception as e:
        return f"Error: {str(e)}\n", 500

if __name__ == "__main__":
    if not os.path.exists(FTP_ROOT):
        os.makedirs(FTP_ROOT)
    
    try:
        run_ftp_server()
    except KeyboardInterrupt:
        print("FTP server stopped.")
