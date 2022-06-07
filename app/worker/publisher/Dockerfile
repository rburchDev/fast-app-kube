# Location of python3 artifactory
FROM        artifactory.charterlab.com/docker-public/python:3.9.5

# Run updates on linux image before running Makefile
RUN         apt-get update
RUN         apt-get upgrade -y

# Make Dir
Cmd         mkdir "app" &&  \
            mkdir "app/services" && \
            mkdir "app/test" &&  \
            mkdir "app/worker" && \
            mkdir "app/services/rabbitmq" && \
            mkdir "app/worker/publisher"

# copy in makefile, requirements, fast.py
COPY        Makefile /app/
COPY        requirements.txt /app/
COPY        ./worker/publisher/publisher.py /app/worker/publisher/
COPY        ./worker/publisher/app.py /app/worker/publisher/
COPY        ./services/rabbitmq/rabb_conn.py /app/services/rabbitmq/
COPY        logger.py /app/

# Change working directory
WORKDIR     /app

# Run Makefile to start app
RUN         make venv/bin/activate

Cmd         ./venv/bin/python3 ./worker/publisher/app.py

EXPOSE      3000