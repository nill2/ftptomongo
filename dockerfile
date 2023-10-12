# Use the official Python image as a parent image
FROM python:3.10

# Set the working directory to /appЗ
WORKDIR /app

# Set arguments as secrets from GHA
ARG SECRET_FTP_USER
ARG SECRET_FTP_PASS
ARG SECRET_MONGO_HOST
ARG SECRET_FTP_PORT

ARG IS_TEST

# Check it arguments were specified
RUN if [ -z "$SECRET_FTP_USER" ]; then \
      echo "SECRET_FTP_USER was not provided during the build"; \
      SECRET_FTP_USER="user"; \
    else \
      echo "SECRET_FTP_USER was provided with the value: $SECRET_FTP_USER"; \
    fi
RUN if [ -z "$SECRET_FTP_PASS" ]; then \
      echo "SECRET_FTP_PASS was not provided during the build"; \
      SECRET_FTP_PASS="password"; \
    else \
      echo "SECRET_FTP_PASS was provided with the value: $SECRET_FTP_PASS"; \
    fi
RUN if [ -z "$SECRET_MONGO_HOST" ]; then \
      echo "SECRET_MONGO_HOST was not provided during the build"; \
      SECRET_MONGO_HOST="localhost"; \
    else \
      echo "SECRET_MONGO_HOST was provided with the value: $SECRET_MONGO_HOST"; \
    fi
RUN if [ -z "$SECRET_FTP_PORT" ]; then \
      echo "SECRET_FTP_PORT was not provided during the build"; \
      SECRET_FTP_PORT=2121; \
    else \
      echo "SECRET_FTP_PORT was provided with the value: $SECRET_FTP_PORT"; \
    fi
    
RUN if [ -z "$IS_TEST" ]; then \
      echo "IS_TEST was not provided during the build = we create prod"; \
      IS_TEST="prod"; \
    else \
      echo "IS_TEST was provided with the value: $IS_TEST"; \
    fi

ENV IS_TEST=$IS_TEST
# Set environment variables for FTP and MongoDB configurations
ENV FTP_HOST=0.0.0.0
ENV FTP_PORT=$SECRET_FTP_PORT
ENV PORT 2121
ENV FTP_USER=$SECRET_FTP_USER
ENV FTP_PASS=$SECRET_FTP_PASS
ENV FTP_ROOT="./ftp"
ENV MONGO_HOST=$SECRET_MONGO_HOST
ENV MONGO_PORT=27017
ENV MONGO_DB="nill-home"
ENV MONGO_COLLECTION="nill-home-photos"

# Copy the Python script and requirements file into the container
COPY *.py /app
COPY requirements.txt /app
COPY environment.yml /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FTP and passive mode ports (e.g., 21 and 60000-60100)

EXPOSE 52000-52050
EXPOSE $FTP_PORT


# Run the Python script
CMD ["python", "ftptomongo.py"]
