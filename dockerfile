# Use the official Python image as a parent image
FROM python:3.10

# Set arguments as secrets from GHA
ARG SECRET_FTP_USER
ARG SECRET_FTP_PASS
ARG SECRET_MONGO_HOST


# Set environment variables for FTP and MongoDB configurations
ENV FTP_HOST=localhost
ENV FTP_PORT=2121
ENV FTP_USER=$SECRET_FTP_USER
ENV FTP_PASS=$SECRET_FTP_PASS
ENV FTP_ROOT="~"
ENV MONGO_HOST=$SECRET_MONGO_HOST
ENV MONGO_PORT=27017
ENV MONGO_DB="nill-home"
ENV MONGO_COLLECTION="nill-home-photos"

# Copy the Python script and requirements file into the container
COPY *.py /app
COPY requirements.txt /app/requirements.txt
COPY environment.yml /app/environment.yml

# Set the working directory to /appЗ
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FTP and passive mode ports (e.g., 21 and 60000-60100)
EXPOSE $FTP_PORT 60000-60100

# Run the Python script
CMD ["python", "ftptomongo.py"]
