#! /bin/bash
###############
## Function ##
###############
instructions() {
  echo "Usage: $0 [-v VERSION]" >&2
  echo " -v Version you wish for the app's being built and pushed" >&2
}

###############
## VARIABLES ##
###############
if [ $# -eq 0 ]; then
  instructions
  exit 1
fi

while getopts :v:p:c: flag; do
  case "${flag}" in
    v) version=${OPTARG};;
    p) file_p=${OPTARG};;
    c) file_c=${OPTARG};;
    *) echo "Invalid Flag"; exit 1; ;;
  esac
done

###############
##  Docker  ##
###############
echo --------
echo "${version}"
echo "${file_p}"
echo "${file_c}"
echo --------
docker build -f worker/publisher/Dockerfile . -t "${file_p}":"${version}" --rm
p_result="$(docker ps -q -f name=rabbitmq-publisher:"${version}")"
if [[ "${p_result}" -eq 0 ]]; then
  echo SUCCESS
else
  FAILED
  exit 1
fi
docker build -f worker/consumer/Dockerfile . -t "${file_c}":"${version}" --rm
c_result="$(docker ps -q -f name=rabbitmq-consumer:"${version}")"
if [[ "${c_result}" -eq 0 ]]; then
  echo SUCCESS
else
  FAILED
  exit 1
fi
echo --------
docker push "${file_p}":"${version}"
# shellcheck disable=SC2181
if [[ $? -eq 0 ]]; then
  echo SUCCESS
else
  echo FAILED
  exit 1
fi
docker push "${file_c}":"${version}"
# shellcheck disable=SC2181
if [[ $? -eq 0 ]]; then
  echo SUCCESS
else
  echo FAILED
  exit 1
fi
echo --------

###############
##   Kube   ##
###############
echo UPDATING HELM CHART INSTALLED
helm upgrade rabbit-app ../rabbit-app --values ../rabbit-app/values.yaml --set deployment.tag.consumer="${version}" --set deployment.tag.publisher="${version}" --set appVersion="${version}"
# shellcheck disable=SC2181
if [[ $? -eq 0 ]]; then
  echo SUCCESS
else
  echo FAILED
  exit 1
fi
echo --------
echo FINISHED