# fast-app-kube
Test application using FastAPI with Docker and Kubernetes 

## Build
To build cd into the src directory:
example
`cd User/home/fast-app-kube/src`

Then give the `startup.sh` script execute permission:
`chmod +x ./scripts/startup.sh`

Finally, run:
`bash scripts/startup.sh -p artifactory.charterlab.com/naas-eagles-docker-local/fast/rabbitmq/rabbitmq-publisher -c artifactory.charterlab.com/naas-eagles-docker-local/fast/rabbitmq/rabbitmq-consumer -v 1.6.25`

You can replace the version with another version if you wish
