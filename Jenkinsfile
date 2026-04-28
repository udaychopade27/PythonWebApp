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
        //    Inspect whichever bmi-app-prod-* container is currently running
        //    and record its image tag (= previous build number) for rollback.
        // ------------------------------------------------------------------
        stage('Capture Rollback Tag') {
            steps {
                script {
                    def previousTag = sh(
                        script: """
                            docker ps --filter "name=bmi-app-prod" --format "{{.Image}}" \
                                | awk -F: '{print \$NF}' | head -1
                        """,
                        returnStdout: true
                    ).trim()

                    env.PREVIOUS_TAG = previousTag ?: 'none'
                    echo "Current prod image tag (rollback target): ${env.PREVIOUS_TAG}"
                }
            }
        }

        // ------------------------------------------------------------------
        // 2. BUILD  — tagged with build number
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
        // 3. PRE-DEPLOY HEALTH CHECK (throwaway test container)
        //    Verifies the new image is healthy before touching production.
        // ------------------------------------------------------------------
        stage('Pre-Deploy Health Check') {
            steps {
                script {
                    sh "docker rm -f ${TEST_CONTAINER} || true"
                    sh """
                        docker run -d \
                            --name ${TEST_CONTAINER} \
                            --network bmi \
                            -p ${TEST_PORT}:5000 \
                            ${APP_NAME}:${IMAGE_TAG}
                    """

                    def healthy    = false
                    def maxRetries = 15

                    for (int i = 1; i <= maxRetries; i++) {
                        def response = sh(
                            script: "docker exec ${TEST_CONTAINER} curl -s --max-time 3 http://localhost:5000${HEALTH_PATH} || echo ''",
                            returnStdout: true
                        ).trim()

                        echo "Pre-deploy health attempt [${i}/${maxRetries}] — response: ${response ?: '(empty)'}"

                        if (response) {
                            def status = sh(
                                script: "echo '${response}' | jq -r '.status' 2>/dev/null || echo unknown",
                                returnStdout: true
                            ).trim()

                            if (status == 'healthy') {
                                healthy = true
                                echo "Pre-deploy health check passed"
                                break
                            }
                        }

                        if (i < maxRetries) sleep(2)
                    }

                    sh "docker rm -f ${TEST_CONTAINER} || true"

                    if (!healthy) {
                        error("Pre-deploy health check failed — aborting, rollback will run in post{}")
                    }
                }
            }
        }

        // ------------------------------------------------------------------
        // 4. DEPLOY
        //    Stop any running bmi-app-prod-* container, start the new one.
        // ------------------------------------------------------------------
        stage('Deploy') {
            steps {
                sh '''
                    set -e

                    echo "== Stopping previous prod container =="
                    docker ps -q --filter "name=bmi-app-prod" | xargs -r docker rm -f || true

                    echo "== Starting bmi-app-prod-${IMAGE_TAG} =="
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
        // 5. POST-DEPLOY HEALTH CHECK (live production container)
        //    Failure here triggers rollback in post{}.
        // ------------------------------------------------------------------
        stage('Post-Deploy Health Check') {
            steps {
                script {
                    def healthy    = false
                    def maxRetries = 12
                    def waitSecs   = 5

                    for (int attempt = 1; attempt <= maxRetries; attempt++) {
                        def response = sh(
                            script: "docker exec ${PROD_CONTAINER} curl -s --max-time 3 http://localhost:5000${HEALTH_PATH} || echo ''",
                            returnStdout: true
                        ).trim()

                        echo "Post-deploy health check [${attempt}/${maxRetries}] — response: ${response ?: '(empty)'}"

                        if (response) {
                            def status = sh(
                                script: "echo '${response}' | jq -r '.status' 2>/dev/null || echo unknown",
                                returnStdout: true
                            ).trim()

                            if (status == 'healthy') {
                                healthy = true
                                echo "Production container ${PROD_CONTAINER} is healthy — deployment complete"
                                break
                            }
                        }

                        if (attempt < maxRetries) sleep(waitSecs)
                    }

                    if (!healthy) {
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

        // Rollback: stop the failed new container, restart from PREVIOUS_TAG image.
        failure {
            script {
                if (env.PREVIOUS_TAG && env.PREVIOUS_TAG != 'none') {
                    def rollbackContainer = "bmi-app-prod-${env.PREVIOUS_TAG}"
                    def rollbackImage     = "${APP_NAME}:${env.PREVIOUS_TAG}"

                    echo "== ROLLBACK: starting ${rollbackContainer} from ${rollbackImage} =="
                    try {
                        // Stop the failed new container
                        sh "docker rm -f ${PROD_CONTAINER} || true"

                        // Restart previous image
                        sh """
                            docker run -d \
                                --name ${rollbackContainer} \
                                --network bmi \
                                -p ${PROD_PORT}:5000 \
                                ${rollbackImage}
                        """

                        def rbHealthy = false
                        for (int i = 1; i <= 6; i++) {
                            def response = sh(
                                script: "docker exec ${rollbackContainer} curl -s --max-time 3 http://localhost:5000${HEALTH_PATH} || echo ''",
                                returnStdout: true
                            ).trim()
                            def status = response
                                ? sh(script: "echo '${response}' | jq -r '.status' 2>/dev/null || echo unknown", returnStdout: true).trim()
                                : 'unknown'
                            echo "Rollback health check [${i}/6] — status: ${status}"
                            if (status == 'healthy') { rbHealthy = true; break }
                            if (i < 6) sleep(5)
                        }

                        if (rbHealthy) {
                            echo "Rollback successful — ${rollbackImage} is live on port ${PROD_PORT}"
                        } else {
                            echo "CRITICAL: rollback container also unhealthy — manual intervention required"
                        }
                    } catch (err) {
                        echo "CRITICAL: rollback failed — ${err.getMessage()}"
                    }
                } else {
                    echo "No previous tag recorded — rollback skipped (first build or capture failed)"
                }

                sh "docker rm -f ${TEST_CONTAINER} || true"
            }
        }

        success {
            echo "Deployment succeeded — ${APP_NAME}:${BUILD_NUMBER} is live on port ${PROD_PORT}"
        }

//         always {
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
//             deleteDir()
//         }
    }
}
