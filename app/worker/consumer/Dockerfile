# Location of python3 artifactory
FROM        artifactory.charterlab.com/docker-public/python:3.9.5

# Run updates on linux image before running Makefile
RUN         apt-get update
RUN         apt-get upgrade -y

# Make Dir
Cmd         mkdir "rabbitmq"

# copy in makefile, requirements, fast.py
COPY        Makefile /
COPY        requirements.txt /
COPY        ./worker/consumer/consumer.py /
COPY        ./services/rabbitmq/rabb_conn.py /rabbitmq/
COPY        logger.py /

# Run Makefile to start app
RUN         make venv/bin/activate

Cmd         ./venv/bin/python3 consumer.py