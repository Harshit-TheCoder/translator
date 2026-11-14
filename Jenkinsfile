pipeline {
  // Run on the Jenkins machine itself (it has python, redis, docker).
  agent any

  options {
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
  }

  environment {
    IMAGE = 'ghcr.io/Harshit-TheCoder/translator'
    // Full git commit id of the build, used as the image tag.
    TAG   = "${env.GIT_COMMIT}"
  }

  stages {
    stage('Test') {
      steps {
        // One sh block, because each sh starts a fresh shell.
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install --quiet -r requirements.txt -r requirements-dev.txt
          python -m pytest -q --cov=app --cov-report=xml --junitxml=junit.xml
        '''
      }
    }

    stage('Golden-set eval') {
      steps {
        sh '''
          . .venv/bin/activate
          # Start Redis only if one is not already answering.
          redis-cli ping || redis-server --daemonize yes
          bash ci/run_eval.sh
        '''
      }
    }

    stage('SonarQube analysis') {
      steps {
        // "sonarqube" = server name set in Manage Jenkins > System.
        withSonarQubeEnv('sonarqube') {
          // "sonar-scanner" = tool name set in Manage Jenkins > Tools.
          sh "${tool 'sonar-scanner'}/bin/sonar-scanner"
        }
      }
    }

    stage('Quality gate') {
      steps {
        // Waits for SonarQube's verdict (needs the webhook, see setup).
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Build image') {
      steps {
        sh 'docker build -t $IMAGE:$TAG .'
      }
    }

    stage('Trivy scan') {
      steps {
        // Trivy runs as a container and reads the image through the socket.
        sh '''
          docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v trivy-cache:/root/.cache/ \
            aquasec/trivy:0.58.1 image \
            --exit-code 1 --severity CRITICAL --ignore-unfixed \
            $IMAGE:$TAG
        '''
      }
    }

    stage('Push to ghcr.io') {
      // Only on main. Works for both plain and multibranch jobs.
      when { expression { return env.BRANCH_NAME == 'main' || env.GIT_BRANCH == 'origin/main' } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'ghcr-creds',
                                          usernameVariable: 'GH_USER',
                                          passwordVariable: 'GH_TOKEN')]) {
          // Single quotes: the secret is read by the shell, never printed by Groovy.
          sh '''
            echo "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin
            docker push $IMAGE:$TAG
          '''
        }
      }
    }

    stage('GitOps: update config repo') {
      when { expression { return env.BRANCH_NAME == 'main' || env.GIT_BRANCH == 'origin/main' } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'config-repo-creds',
                                          usernameVariable: 'CFG_USER',
                                          passwordVariable: 'CFG_TOKEN')]) {
          sh '''
            rm -rf config
            git clone https://$CFG_USER:$CFG_TOKEN@github.com/Harshit-TheCoder/translator-config.git config
            cd config
            sed -i "s|^  tag:.*|  tag: '$TAG'|" env/dev/values.yaml
            git config user.name "ci-bot"
            git config user.email "ci-bot@users.noreply.github.com"
            git add env/dev/values.yaml
            git commit -m "chore: translator image $TAG" || echo "nothing to commit"
            git push
            cd .. && rm -rf config
          '''
        }
      }
    }
  }

  post {
    always {
      // Show test results in the Jenkins UI, then stop Redis.
      junit allowEmptyResults: true, testResults: 'junit.xml'
      sh 'redis-cli shutdown nosave || true'
    }
  }
}