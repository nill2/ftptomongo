# syntax=docker/dockerfile:1
# Use the official Python image as a parent image
FROM python:3.10

# Set the working directory to /appЗ
WORKDIR /app

# Set arguments as secrets from GHA
# Define default values for secrets (when building locally)
ARG SECRET_FTP_USER="user"
ARG SECRET_FTP_PASS="password"
ARG SECRET_MONGO_HOST="localhost"
ARG SECRET_FTP_PORT="2121"
ARG IS_TEST="prod"

# Check if secrets are provided and use them
#RUN if [ -f /run/secrets/SECRET_FTP_USER ]; then \
#      SECRET_FTP_USER=$(cat /run/secrets/SECRET_FTP_USER); \
#    else \
#      echo "no /run/secrets/SECRET_FTP_USER"; \
#    fi


#RUN if [ -f /run/secrets/SECRET_FTP_PASS ]; then \
#      SECRET_FTP_PASS=$(cat /run/secrets/SECRET_FTP_PASS); \
#    fi

#RUN if [ -f /run/secrets/SECRET_MONGO_HOST ]; then \
#      SECRET_MONGO_HOST=$(cat /run/secrets/SECRET_MONGO_HOST); \
#    fi

#RUN if [ -f /run/secrets/SECRET_FTP_PORT ]; then \
#      SECRET_FTP_PORT=$(cat /run/secrets/SECRET_FTP_PORT); \
#    fi

# Output the secrets for debugging
RUN echo "SECRET_FTP_USER: $SECRET_FTP_USER"; \
    echo "SECRET_FTP_PASS: $SECRET_FTP_PASS"; \
    echo "SECRET_MONGO_HOST: $SECRET_MONGO_HOST"; \
    echo "SECRET_FTP_PORT: $SECRET_FTP_PORT"
    

ENV IS_TEST=$IS_TEST

RUN echo "IS_TEST=$IS_TEST"
# Set environment variables for FTP and MongoDB configurations
ENV FTP_HOST=0.0.0.0
ENV FTP_PORT=$SECRET_FTP_PORT

ENV PORT=$SECRET_FTP_PORT

ENV FTP_USER=$SECRET_FTP_USER
ENV FTP_PASS=$SECRET_FTP_PASS
#ENV FTP_ROOT=""
ENV MONGO_HOST=$SECRET_MONGO_HOST
ENV MONGO_PORT=27017
ENV MONGO_DB="nill-home"
ENV MONGO_COLLECTION="nill-home-photos"

# Copy the Python script and requirements file into the container
COPY *.py /app/
COPY requirements.txt /app/
COPY environment.yml /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FTP and passive mode ports (e.g., 21 and 60000-60100)

EXPOSE $FTP_PORT
EXPOSE 52000-52003

# Run the Python script
CMD ["python", "__main__.py"]
