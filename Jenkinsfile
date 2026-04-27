pipeline {
    agent any 

    environment {
        APP_NAME        = "bmi-app"
        TEST_CONTAINER  = "bmi-app-test"
        PROD_CONTAINER  = "bmi-app-prod"
        TEST_PORT       = "5001"
        PROD_PORT       = "5000"
        HEALTH_URL      = "http://localhost:5001/health"
    }

    stages {

        stage("Build") {
            steps {
                sh '''
                set -e
                docker build -t ${APP_NAME} . 2>&1 | tee build_output.txt
                '''
            }
        }

        stage("Pre-Deploy Health Check") {
            steps {
                sh '''
                set -e

                echo "🧪 Starting test container..."

                docker rm -f ${TEST_CONTAINER} || true

                docker run -d \
                  --name ${TEST_CONTAINER} \
                  --network bmi \
                  ${APP_NAME}

                echo "⏳ Fetching container IP..."

                # Wait until container gets an IP
                for i in $(seq 1 10); do
                    CONTAINER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${TEST_CONTAINER})
                    if [ ! -z "$CONTAINER_IP" ]; then
                        break
                    fi
                    sleep 1
                done

                echo "Container IP: $CONTAINER_IP"

                if [ -z "$CONTAINER_IP" ]; then
                    echo "❌ Failed to get container IP"
                    exit 1
                fi

                HEALTHY=false

                echo "⏳ Waiting for app to become healthy..."

                for i in $(seq 1 15); do
                    echo "Attempt $i..."

                    RESPONSE=$(curl -s --fail http://$CONTAINER_IP:5000/health 2>&1 || true)

                    echo "Raw Response: $RESPONSE"

                    if [ -z "$RESPONSE" ]; then
                        echo "⚠️ Empty response"
                        STATUS="unknown"
                    elif echo "$RESPONSE" | jq . >/dev/null 2>&1; then
                        STATUS=$(echo "$RESPONSE" | jq -r '.status')
                    else
                        echo "❌ Invalid JSON"
                        STATUS="unknown"
                    fi

                    echo "Parsed status: $STATUS"

                    if [ "$STATUS" = "healthy" ]; then
                        echo "✅ Health check passed"
                        HEALTHY=true
                        break
                    fi

                    sleep 2
                done

                if [ "$HEALTHY" != "true" ]; then
                    echo "❌ Health check failed after retries"
                    docker logs ${TEST_CONTAINER} > container_error.log || true
                    docker rm -f ${TEST_CONTAINER} || true
                    exit 1
                fi
                '''
            }
        }

        stage("Deploy (Safe Swap)") {
            steps {
                sh '''
                set -e

                echo "🚀 Deploying to production..."

                docker rm -f ${PROD_CONTAINER} || true

                docker run -d \
                  --name ${PROD_CONTAINER} \
                  --network bmi \
                  -p ${PROD_PORT}:5000 \
                  ${APP_NAME}

                docker rm -f ${TEST_CONTAINER} || true

                echo "✅ Deployment complete"
                '''
            }
        }
    }

    post {
        always {
            emailext(
                to: "udaychopade27@gmail.com, uchopade27@gmail.com",
                subject: "[Jenkins] ${currentBuild.currentResult} - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
Hello Team,

Build Status: ${currentBuild.currentResult}
Job: ${env.JOB_NAME}
Build URL: ${env.BUILD_URL}

Health check and safe deployment executed.

Logs attached.
                """,
                attachmentsPattern: "build_output.txt,container_error.log"
            )
        }

        success {
            echo "✅ Pipeline succeeded. App is live on port ${PROD_PORT}"
        }

        failure {
            echo "❌ Pipeline failed. Check logs."
        }
    }
}