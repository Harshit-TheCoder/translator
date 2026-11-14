# Official Jenkins LTS (Java 17). Floating tag on purpose: the plugin installer
# needs a recent Jenkins core. After it works, pin the version you got.
FROM jenkins/jenkins:lts-jdk17 
# Root is neeeded to install system packages 
USER root 
#python3 for tests, redis-server for the eval, docker CLI (docker.io) to build 
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip redis-server docker.io git \
    && rm -rf /var/lib/apt/lists/*

# Go back to the noral jenkins user (compose overrides this for the socket). 
USER jenkins
# Plugins the Jenkinsfile uses: pipelines, git, credentials, SonarQube, tests.
RUN jenkins-plugin-cli --plugins workflow-aggregator git credentials-binding sonar junit timestamper pipeline-stage-view