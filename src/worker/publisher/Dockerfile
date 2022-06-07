# Location of python3 artifactory
FROM        artifactory.charterlab.com/docker-public/python:3.9.5

# Run updates on linux image before running Makefile
RUN         apt-get update
RUN         apt-get upgrade -y

# Make Dir
Cmd         mkdir "rabbit" && \
            mkdir "src" &&  \
            mkdir "src/services" && \
            mkdir "src/test" &&  \
            mkdir "src/worker" && \
            mkdir "src/services/rabbitmq" && \
            mkdir "src/worker/publisher"

# copy in makefile, requirements, fast.py
COPY        Makefile /rabbit/
COPY        requirements.txt /rabbit/
COPY        __init__.py /rabbit/src/
COPY        ./worker/__init__.py /rabbit/src/worker/
COPY        ./worker/publisher/__init__.py /rabbit/src/worker/publisher/
COPY        ./services/__init__.py /rabbit/src/services/
COPY        ./services/rabbitmq/__init__.py /rabbit/src/services/rabbitmq/
COPY        ./worker/publisher/publish.py /rabbit/src/worker/publisher/
COPY        ./worker/app.py /rabbit/src/worker/
COPY        ./services/rabbitmq/rabb_conn.py /rabbit/src/services/rabbitmq/
COPY        logger.py /rabbit/src/

ENV         PYTHONPATH "${PYTHONPATH}:/rabbit/"

WORKDIR     "/rabbit/"

# Run Makefile to start src
RUN         make venv/bin/activate

Cmd         ./venv/bin/python3 src/worker/app.py

EXPOSE      3000