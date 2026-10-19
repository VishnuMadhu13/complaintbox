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
      description: 'true = fail the build on Sonar quality gate / Bandit / Trivy / pip-audit / ZAP findings. A scanner that crashes (no report produced) always fails the build.')
  }

  environment {
    // ---- EDIT THESE ----
    APP_DIR           = '.'                              // folder that contains manage.py ('.' if at repo root)
    IMAGE_REPO        = 'vishnumadhu13/complaintbox'     // Docker Hub repo
    GIT_REPO          = 'github.com/VishnuMadhu13/complaintbox.git'
    GIT_BRANCH        = 'main'
    JENKINS_CONTAINER = 'ubuntu-jenkins-1'
    SONAR_HOST_URL    = 'http://32.236.227.85:9000'      // SonarQube URL as seen from Jenkins (changes if the EC2 IP changes)
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
        // Old reports in a reused workspace must never make a crashed scan look successful.
        sh 'rm -f $APP_DIR/*-report.json zap-report.html zap-report.json'
        sh 'ls -la $APP_DIR'
      }
    }

    stage('Unit Tests') {
      steps {
        // mysqlclient needs the MySQL client libs to build; tests use SQLite via settings_ci
        sh '''
          docker run --rm --volumes-from $JENKINS_CONTAINER -w $WORKSPACE/$APP_DIR \
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
                // share Jenkins' network namespace so the scanner reaches SonarQube like Jenkins does
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
              gate(rc, 'Bandit', "${env.APP_DIR}/bandit-report.json")
            }
          }
        }
      }
    }

    stage('Dependency Scan') {
      steps {
        script {
          // pip-audit: known CVEs in requirements.txt.
          // It resolves the requirements, so mysqlclient must be buildable -> install the MySQL client libs first.
          int rc1 = sh(returnStatus: true, script: '''
            docker run --rm --volumes-from $JENKINS_CONTAINER -w $WORKSPACE/$APP_DIR python:3.12-slim sh -c \
              "apt-get update -qq && \
               apt-get install -y -qq build-essential pkg-config default-libmysqlclient-dev >/dev/null && \
               pip install -q pip-audit && pip-audit -r requirements.txt -f json -o pip-audit-report.json"
          ''')
          gate(rc1, 'pip-audit', "${env.APP_DIR}/pip-audit-report.json")

          // Trivy filesystem scan: dependencies + secrets + misconfig (vuln DB cached in a named volume)
          int rc2 = sh(returnStatus: true, script: '''
            docker run --rm -v trivy-cache:/root/.cache/ \
              --volumes-from $JENKINS_CONTAINER -w $WORKSPACE/$APP_DIR \
              aquasec/trivy:latest fs --scanners vuln,secret,misconfig \
              --severity HIGH,CRITICAL --exit-code 1 -f json -o trivy-fs-report.json .
          ''')
          gate(rc2, 'Trivy filesystem scan', "${env.APP_DIR}/trivy-fs-report.json")
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
          // --ignore-unfixed: only report vulnerabilities that have a fix available
          int rc = sh(returnStatus: true, script: '''
            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
              -v trivy-cache:/root/.cache/ \
              --volumes-from $JENKINS_CONTAINER -w $WORKSPACE \
              aquasec/trivy:latest image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 \
              -f json -o trivy-image-report.json $IMAGE_REPO:$IMAGE_TAG
          ''')
          gate(rc, 'Trivy image scan', 'trivy-image-report.json')
        }
      }
    }

    // ============ STEP 1 (cont.): DAST ============
    stage('DAST (OWASP ZAP)') {
      steps {
        script {
          // The app image defaults to MySQL; for DAST it runs on SQLite (settings_ci) so it starts without a database.
          // If the app does not come up, print its logs and fail instead of scanning nothing.
          sh '''
            docker network create $DAST_NET
            docker run -d --name $DAST_APP --network $DAST_NET \
              -e DJANGO_SETTINGS_MODULE=complaint_box.settings_ci \
              -e DJANGO_SECRET_KEY=dast-only-key -e DJANGO_ALLOWED_HOSTS='*' \
              $IMAGE_REPO:$IMAGE_TAG

            echo "Waiting for app..."
            UP=0
            for i in $(seq 1 20); do
              if docker run --rm --network $DAST_NET curlimages/curl -s -o /dev/null http://$DAST_APP:8000/; then
                UP=1; break
              fi
              if [ "$(docker inspect -f '{{.State.Running}}' $DAST_APP)" != "true" ]; then
                break
              fi
              sleep 3
            done
            if [ "$UP" != 1 ]; then
              echo "App did not start - container logs:"
              docker logs $DAST_APP || true
              exit 1
            fi
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
          gate(rc, 'OWASP ZAP baseline', 'zap-report.json')
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
            # pick up commits pushed while this build was running, so the push is a fast-forward
            git pull --rebase https://$GIT_USER:$GIT_TOKEN@$GIT_REPO $GIT_BRANCH
            sed -i "s|image: .*complaintbox.*|image: $IMAGE_REPO:$IMAGE_TAG|" $APP_DIR/k8s/deployments.yaml
            git add $APP_DIR/k8s/deployments.yaml
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
        # keep only the 2 newest numeric image tags on the Jenkins host
        docker images $IMAGE_REPO --format '{{.Tag}}' | grep -E '^[0-9]+$' | sort -n | head -n -2 \
          | xargs -r -I{} docker rmi $IMAGE_REPO:{} || true
        docker image prune -f || true
      '''
      archiveArtifacts artifacts: "${APP_DIR}/*-report.json, *-report.json, zap-report.html, zap-report.json",
                       allowEmptyArchive: true, fingerprint: true
    }
    success { echo "Pipeline OK -> ArgoCD will sync ${IMAGE_REPO}:${IMAGE_TAG}" }
    failure { echo 'Pipeline failed - check the stage logs and archived reports.' }
  }
}

// Scanner result handling:
//  - report given and missing  -> the scanner itself failed: ALWAYS fail the build
//  - non-zero exit (findings)  -> fail only when ENFORCE_GATES=true, otherwise warn
def gate(int rc, String name, String report = null) {
  if (report && !fileExists(report)) {
    error("${name} produced no ${report} - the scan itself failed (exit ${rc}). Check the stage log.")
  }
  if (rc != 0) {
    if (params.ENFORCE_GATES) {
      error("${name} failed (exit ${rc})")
    } else {
      echo "WARNING: ${name} reported findings (exit ${rc}) - not enforced this run."
    }
  }
}