# Use the official Python image as a parent image
FROM python:3.8-slim

# Set environment variables for FTP and MongoDB configurations
ENV FTP_HOST=localhost
ENV FTP_PORT=21
ENV FTP_USER="user"
ENV FTP_PASS="password"
ENV FTP_ROOT="/"
ENV MONGO_HOST="mongodb+srv://appUser:qovkm123@cluster0.qfjxdop.mongodb.net/?retryWrites=true&w=majority&appName=AtlasApp"
ENV MONGO_PORT=27017
ENV MONGO_DB="nill-home"
ENV MONGO_COLLECTION="nill-home-photos"

# Copy the Python script and requirements file into the container
COPY ftptomongo.py /app/ftptomongo.py
COPY config.py /app/config.py
COPY requirements.txt /app/requirements.txt

# Set the working directory to /appЗ
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FTP and passive mode ports (e.g., 21 and 60000-60100)
EXPOSE $FTP_PORT 60000-60100

# Run the Python script
CMD ["python", "ftptomongo.py"]
