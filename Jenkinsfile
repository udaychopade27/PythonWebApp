pipeline {
    agent any 

    environment {
        APP_NAME = "bmi-app"
        TEST_CONTAINER = "bmi-app-test"
        PROD_CONTAINER = "bmi-app-prod"
        TEST_PORT = "5001"
        PROD_PORT = "5000"
        HEALTH_URL = "http://localhost:5001/health"
    }

    stages {

        stage("Build") {
            steps {
                sh """
                docker build -t ${APP_NAME} . 2>&1 | tee build_output.txt
                """
            }
        }

        stage("Pre-Deploy Health Check") {
            steps {
                sh """
                echo "🧪 Starting test container..."

                docker rm -f ${TEST_CONTAINER} || true

                docker run -d \
                  --name ${TEST_CONTAINER} \
                  -p ${TEST_PORT}:5000 \
                  ${APP_NAME}

                sleep 10

                HEALTHY=false

                for i in {1..5}; do
                    if curl -sSf ${HEALTH_URL} > /dev/null 2>&1; then
                        HEALTHY=true
                        break
                    fi
                    sleep 3
                done

                if [ "\$HEALTHY" = true ]; then
                    echo "✅ Health check passed"
                else
                    echo "❌ Health check failed"
                    docker logs ${TEST_CONTAINER} > container_error.log
                    docker rm -f ${TEST_CONTAINER}
                    exit 1
                fi
                """
            }
        }

        stage("Deploy (Safe Swap)") {
            steps {
                sh """
                echo "🚀 Deploying to production..."

                docker rm -f ${PROD_CONTAINER} || true

                docker run -d \
                  --name ${PROD_CONTAINER} \
                  -p ${PROD_PORT}:5000 \
                  ${APP_NAME}

                docker rm -f ${TEST_CONTAINER} || true

                echo "✅ Deployment complete"
                """
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