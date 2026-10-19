// End-to-end DevSecOps pipeline: Test -> SAST -> Dependency scan -> Build -> Image scan -> DAST -> Push -> GitOps
// Jenkins runs as a container (ubuntu-jenkins-1) with the host Docker socket mounted.
// Every scanner runs as a throw-away container that shares Jenkins' volumes, so nothing
// (python, sonar-scanner, trivy, zap) has to be installed inside Jenkins itself.

pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    timeout(time: 60, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }

  parameters {
    booleanParam(name: 'ENFORCE_GATES', defaultValue: false,
      description: 'true = fail the build on Sonar quality gate / Bandit / Trivy / ZAP findings. Keep false for the first green run.')
  }

  environment {
    // ---- EDIT THESE ----
    APP_DIR           = '.'                        // folder that contains manage.py ('.' if at repo root)
    IMAGE_REPO        = 'vishnumadhu13/complaintbox'    // Docker Hub repo
    GIT_REPO          = 'github.com/VishnuMadhu13/complaintbox.git'
    GIT_BRANCH        = 'main'
    JENKINS_CONTAINER = 'ubuntu-jenkins-1'
    SONAR_HOST_URL    = 'http://3.25.89.189:9000'           // compose service name of SonarQube
    // --------------------
    IMAGE_TAG         = "${BUILD_NUMBER}"
    DAST_NET          = "dast-net-${BUILD_NUMBER}"
    DAST_APP          = "django-dast-${BUILD_NUMBER}"
    DAST_ZAP          = "zap-${BUILD_NUMBER}"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
        sh 'ls -la $APP_DIR'
      }
    }

    stage('Unit Tests') {
      steps {
        sh '''
          docker run --rm --volumes-from ubuntu-jenkins-1 -w /var/jenkins_home/workspace/complaintbox/. \
            -e DJANGO_SECRET_KEY=ci-only-key \
            python:3.9-slim sh -c "apt-get update -qq && \
            apt-get install -y -qq build-essential pkg-config default-libmysqlclient-dev >/dev/null && \
            pip install -q -r requirements.txt && \
            python manage.py test --noinput --settings=complaint_box.settings_ci"
        '''
      }
    }

    // ============ STEP 1: SAST + DEPENDENCY SCAN ============
    stage('SAST') {
      parallel {

        stage('SonarQube') {
          steps {
            withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
              script {
                // share Jenkins' network namespace so the compose DNS name "sonarqube" resolves
                int rc = sh(returnStatus: true, script: '''
                  docker run --rm --network container:$JENKINS_CONTAINER \
                    --volumes-from $JENKINS_CONTAINER -w $WORKSPACE/$APP_DIR \
                    -e SONAR_HOST_URL=$SONAR_HOST_URL -e SONAR_TOKEN=$SONAR_TOKEN \
                    sonarsource/sonar-scanner-cli \
                    -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=300
                ''')
                gate(rc, 'SonarQube quality gate')
              }
            }
          }
        }

        stage('Bandit (Python SAST)') {
          steps {
            script {
              int rc = sh(returnStatus: true, script: '''
                docker run --rm --volumes-from $JENKINS_CONTAINER -w $WORKSPACE/$APP_DIR python:3.12-slim sh -c \
                  "pip install -q bandit && bandit -r . -x ./venv,./.venv,./static,./media,./tests -ll -f json -o bandit-report.json"
              ''')
              gate(rc, 'Bandit')
            }
          }
        }
      }
    }

    stage('Dependency Scan') {
      steps {
        script {
          // pip-audit: known CVEs in requirements.txt
          int rc1 = sh(returnStatus: true, script: '''
            docker run --rm --volumes-from $JENKINS_CONTAINER -w $WORKSPACE/$APP_DIR python:3.12-slim sh -c \
              "pip install -q pip-audit && pip-audit -r requirements.txt -f json -o pip-audit-report.json"
          ''')
          gate(rc1, 'pip-audit')

          // Trivy filesystem scan: dependencies + secrets + misconfig
          int rc2 = sh(returnStatus: true, script: '''
            docker run --rm --volumes-from $JENKINS_CONTAINER -w $WORKSPACE/$APP_DIR \
              aquasec/trivy:latest fs --scanners vuln,secret,misconfig \
              --severity HIGH,CRITICAL --exit-code 1 -f json -o trivy-fs-report.json .
          ''')
          gate(rc2, 'Trivy filesystem scan')
        }
      }
    }

    // ============ STEP 2: BUILD ============
    stage('Docker Build') {
      steps {
        sh '''
          docker build -t $IMAGE_REPO:$IMAGE_TAG -t $IMAGE_REPO:latest $APP_DIR
          docker images $IMAGE_REPO
        '''
      }
    }

    stage('Image Scan (Trivy)') {
      steps {
        script {
          int rc = sh(returnStatus: true, script: '''
            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
              --volumes-from $JENKINS_CONTAINER -w $WORKSPACE \
              aquasec/trivy:latest image --severity HIGH,CRITICAL --exit-code 1 \
              -f json -o trivy-image-report.json $IMAGE_REPO:$IMAGE_TAG
          ''')
          gate(rc, 'Trivy image scan')
        }
      }
    }

    // ============ STEP 1 (cont.): DAST ============
    stage('DAST (OWASP ZAP)') {
      steps {
        script {
          sh '''
            docker network create $DAST_NET
            docker run -d --name $DAST_APP --network $DAST_NET \
              -e DJANGO_SECRET_KEY=dast-only-key -e DJANGO_ALLOWED_HOSTS='*' \
              $IMAGE_REPO:$IMAGE_TAG

            echo "Waiting for app..."
            for i in $(seq 1 30); do
              docker run --rm --network $DAST_NET curlimages/curl -s -o /dev/null http://$DAST_APP:8000/ && break
              sleep 3
            done
          '''
          int rc = sh(returnStatus: true, script: '''
            docker run --name $DAST_ZAP --network $DAST_NET --user root \
              ghcr.io/zaproxy/zaproxy:stable sh -c \
              "mkdir -p /zap/wrk && zap-baseline.py -t http://$DAST_APP:8000 -r zap-report.html -J zap-report.json -I"
          ''')
          sh '''
            docker cp $DAST_ZAP:/zap/wrk/zap-report.html $WORKSPACE/zap-report.html || true
            docker cp $DAST_ZAP:/zap/wrk/zap-report.json $WORKSPACE/zap-report.json || true
          '''
          gate(rc, 'OWASP ZAP baseline')
        }
      }
    }

    // ============ STEP 3: PUSH ============
    stage('Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'docker-cred',
                                          usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          sh '''
            echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
            docker push $IMAGE_REPO:$IMAGE_TAG
            docker push $IMAGE_REPO:latest
            docker logout
          '''
        }
      }
    }

    // ============ STEP 4: GITOPS (ArgoCD picks up this commit) ============
    stage('Update Manifest (GitOps)') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'github-jenkins',
                                          usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
          sh '''
            git config user.email "vishnumadhu04723@gmail.com"
            git config user.name  "VishnuMadhu13"
            git checkout -B $GIT_BRANCH                      # leave detached HEAD
            sed -i "s|image: .*complaintbox.*|image: vishnumadhu13/complaintbox:${IMAGE_TAG}|" k8s/appdeployments.yaml
            git add $APP_DIR/k8s/appdeployments.yaml
            git commit -m "ci: deploy $IMAGE_REPO:$IMAGE_TAG [skip ci]" || echo "nothing to commit"
            git push https://$GIT_USER:$GIT_TOKEN@$GIT_REPO $GIT_BRANCH
          '''
        }
      }
    }
  }

  post {
    always {
      sh '''
        docker rm -f $DAST_APP $DAST_ZAP 2>/dev/null || true
        docker network rm $DAST_NET 2>/dev/null || true
        docker image prune -f || true
      '''
      archiveArtifacts artifacts: "${APP_DIR}/*-report.json, *-report.json, zap-report.html, zap-report.json",
                       allowEmptyArchive: true, fingerprint: true
    }
    success { echo "Pipeline OK -> ArgoCD will sync ${IMAGE_REPO}:${IMAGE_TAG}" }
    failure { echo 'Pipeline failed - check the stage logs and archived reports.' }
  }
}

// Non-zero scanner exit: warn by default, fail only when ENFORCE_GATES=false
def gate(int rc, String name) {
  if (rc != 0) {
    if (params.ENFORCE_GATES) {
      error("${name} failed (exit ${rc})")
    } else {
      echo "WARNING: ${name} reported findings (exit ${rc}) - not enforced this run."
    }
  }
}