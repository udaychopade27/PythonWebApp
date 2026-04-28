// ============================================================
// LOCAL TEST PIPELINE — BMI App
// Paste this as "Pipeline script" in a Jenkins Pipeline job.
// No GitHub setup needed. Requires Docker + the bmi network:
//   docker network create bmi
// ============================================================

pipeline {
    agent any

    environment {
        APP_NAME       = "bmi-app"
        IMAGE_TAG      = "${BUILD_NUMBER}"
        TEST_CONTAINER = "bmi-app-test-${BUILD_NUMBER}"
        PROD_CONTAINER = "bmi-app-prod-${BUILD_NUMBER}"
        TEST_PORT      = "5001"
        PROD_PORT      = "5000"
        HEALTH_PATH    = "/health"
    }

    stages {

        // ------------------------------------------------------------------
        // 1. CAPTURE ROLLBACK TAG
        // ------------------------------------------------------------------
        stage('Capture Rollback Tag') {
            steps {
                script {
                    def previousTag = sh(
                        script: """docker ps --filter "name=bmi-app-prod" --format "{{.Image}}" | awk -F: '{print \$NF}' | head -1""",
                        returnStdout: true
                    ).trim()

                    env.PREVIOUS_TAG = previousTag ?: 'none'
                    echo "Rollback target: ${env.PREVIOUS_TAG}"
                }
            }
        }

        // ------------------------------------------------------------------
        // 2. BUILD
        // ------------------------------------------------------------------
        stage('Build') {
            steps {
                sh '''
                    set -e
                    docker build -t ${APP_NAME}:${IMAGE_TAG} . 2>&1 | tee build_output.txt
                '''
            }
        }

        // ------------------------------------------------------------------
        // 3. PRE-DEPLOY HEALTH CHECK
        //    Entire loop runs in one shell script — no Groovy/shell split.
        //    Waits for the container to be running before curling.
        // ------------------------------------------------------------------
        stage('Pre-Deploy Health Check') {
            steps {
                sh 'docker rm -f ${TEST_CONTAINER} 2>/dev/null || true'
                sh '''
                    docker run -d \
                        --name ${TEST_CONTAINER} \
                        --network bmi \
                        -p ${TEST_PORT}:5000 \
                        ${APP_NAME}:${IMAGE_TAG}
                '''
                script {
                    def passed = sh(
                        returnStatus: true,
                        script: '''
                            RETRIES=15
                            for i in $(seq 1 $RETRIES); do
                                # Wait until container is in running state
                                STATE=$(docker inspect -f '{{.State.Status}}' ${TEST_CONTAINER} 2>/dev/null || echo 'missing')
                                if [ "$STATE" != "running" ]; then
                                    echo "Attempt $i/$RETRIES — container state: $STATE, waiting..."
                                    sleep 2
                                    continue
                                fi

                                STATUS=$(docker exec ${TEST_CONTAINER} \
                                    curl -s --max-time 3 http://localhost:5000${HEALTH_PATH} 2>/dev/null \
                                    | jq -r '.status' 2>/dev/null || echo 'unknown')

                                echo "Attempt $i/$RETRIES — health status: $STATUS"

                                if [ "$STATUS" = "healthy" ]; then
                                    echo "Pre-deploy health check passed"
                                    exit 0
                                fi
                                sleep 2
                            done
                            echo "Pre-deploy health check failed after $RETRIES attempts"
                            exit 1
                        '''
                    )
                    sh 'docker rm -f ${TEST_CONTAINER} 2>/dev/null || true'
                    if (passed != 0) {
                        error("Pre-deploy health check failed — aborting, rollback will run in post{}")
                    }
                }
            }
        }

        // ------------------------------------------------------------------
        // 4. DEPLOY — stop previous prod container, start new one
        // ------------------------------------------------------------------
        stage('Deploy') {
            steps {
                sh '''
                    set -e
                    echo "== Stopping any running prod container =="
                    docker ps -q --filter "name=bmi-app-prod" | xargs -r docker rm -f || true

                    echo "== Starting ${PROD_CONTAINER} =="
                    docker run -d \
                        --name ${PROD_CONTAINER} \
                        --network bmi \
                        -p ${PROD_PORT}:5000 \
                        ${APP_NAME}:${IMAGE_TAG}

                    echo "Container ${PROD_CONTAINER} started on port ${PROD_PORT}"
                '''
            }
        }

        // ------------------------------------------------------------------
        // 5. POST-DEPLOY HEALTH CHECK
        //    Same single-shell approach as pre-deploy check.
        // ------------------------------------------------------------------
        stage('Post-Deploy Health Check') {
            steps {
                script {
                    def passed = sh(
                        returnStatus: true,
                        script: '''
                            RETRIES=12
                            for i in $(seq 1 $RETRIES); do
                                STATE=$(docker inspect -f '{{.State.Status}}' ${PROD_CONTAINER} 2>/dev/null || echo 'missing')
                                if [ "$STATE" != "running" ]; then
                                    echo "Attempt $i/$RETRIES — container state: $STATE, waiting..."
                                    sleep 3
                                    continue
                                fi

                                STATUS=$(docker exec ${PROD_CONTAINER} \
                                    curl -s --max-time 3 http://localhost:5000${HEALTH_PATH} 2>/dev/null \
                                    | jq -r '.status' 2>/dev/null || echo 'unknown')

                                echo "Attempt $i/$RETRIES — health status: $STATUS"

                                if [ "$STATUS" = "healthy" ]; then
                                    echo "Production container ${PROD_CONTAINER} is healthy"
                                    exit 0
                                fi
                                sleep 3
                            done
                            echo "Post-deploy health check failed after $RETRIES attempts"
                            exit 1
                        '''
                    )
                    if (passed != 0) {
                        error("Post-deploy health check failed — rollback will run in post{}")
                    }
                }
            }
        }
    }

    // ======================================================================
    // POST ACTIONS
    // ======================================================================
    post {

        failure {
            script {
                if (env.PREVIOUS_TAG && env.PREVIOUS_TAG != 'none') {
                    def rollbackContainer = "bmi-app-prod-${env.PREVIOUS_TAG}"
                    def rollbackImage     = "${env.APP_NAME}:${env.PREVIOUS_TAG}"
                    echo "== ROLLBACK: ${rollbackImage} → ${rollbackContainer} =="
                    try {
                        // Stop the failed new container AND the existing rollback container (if already running)
                        sh "docker rm -f ${env.PROD_CONTAINER} 2>/dev/null || true"
                        sh "docker rm -f ${rollbackContainer} 2>/dev/null || true"
                        sh """
                            docker run -d \
                                --name ${rollbackContainer} \
                                --network bmi \
                                -p ${env.PROD_PORT}:5000 \
                                ${rollbackImage}
                        """
                        def rbPassed = sh(
                            returnStatus: true,
                            script: """
                                for i in \$(seq 1 6); do
                                    STATE=\$(docker inspect -f '{{.State.Status}}' ${rollbackContainer} 2>/dev/null || echo 'missing')
                                    STATUS=''
                                    if [ "\$STATE" = "running" ]; then
                                        STATUS=\$(docker exec ${rollbackContainer} \
                                            curl -s --max-time 3 http://localhost:5000${env.HEALTH_PATH} 2>/dev/null \
                                            | jq -r '.status' 2>/dev/null || echo 'unknown')
                                    fi
                                    echo "Rollback check [\$i/6] — state: \$STATE, status: \$STATUS"
                                    if [ "\$STATUS" = "healthy" ]; then exit 0; fi
                                    sleep 5
                                done
                                exit 1
                            """
                        )
                        if (rbPassed == 0) {
                            echo "Rollback successful — ${rollbackImage} is live on port ${env.PROD_PORT}"
                        } else {
                            echo "CRITICAL: rollback container also unhealthy — manual intervention required"
                        }
                    } catch (err) {
                        echo "CRITICAL: rollback failed — ${err.getMessage()}"
                    }
                } else {
                    echo "No previous tag — rollback skipped (first build)"
                }
                sh 'docker rm -f ${TEST_CONTAINER} 2>/dev/null || true'
            }
        }

        success {
            echo "Deployment succeeded — ${APP_NAME}:${BUILD_NUMBER} is live on port ${PROD_PORT}"
        }

        always {
//             emailext(
//                 to: "udaychopade27@gmail.com, uchopade27@gmail.com",
//                 subject: "[Jenkins] ${currentBuild.currentResult} - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
//                 body: """
// Hello Team,

// Build Status  : ${currentBuild.currentResult}
// Job           : ${env.JOB_NAME}
// Build Number  : ${env.BUILD_NUMBER}
// Image Tag     : ${env.APP_NAME}:${env.BUILD_NUMBER}
// Build URL     : ${env.BUILD_URL}

// Health check and safe deployment executed.
// Logs attached if available.
//                 """,
//                 attachmentsPattern: "build_output.txt,container_error.log"
//             )
            deleteDir()
        }
    }
}
