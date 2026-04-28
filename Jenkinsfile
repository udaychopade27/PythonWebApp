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
        TEST_CONTAINER = "bmi-app-test"
        PROD_CONTAINER = "bmi-app-prod"
        TEST_PORT      = "5001"
        PROD_PORT      = "5000"
        HEALTH_PATH    = "/health"
    }

    stages {

        // ------------------------------------------------------------------
        // 1. SAVE ROLLBACK SNAPSHOT
        //    Tag the current bmi-app image as bmi-app:rollback before
        //    the new build overwrites it. Skipped on very first run.
        // ------------------------------------------------------------------
        stage('Save Rollback Snapshot') {
            steps {
                script {
                    def exists = sh(
                        script: "docker image inspect ${APP_NAME}:latest > /dev/null 2>&1 && echo yes || echo no",
                        returnStdout: true
                    ).trim()

                    if (exists == 'yes') {
                        sh "docker tag ${APP_NAME}:latest ${APP_NAME}:rollback"
                        echo "Rollback snapshot saved as ${APP_NAME}:rollback"
                    } else {
                        echo "No existing image found — rollback snapshot skipped (first build)"
                    }
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
                    docker build -t ${APP_NAME}:latest . 2>&1 | tee build_output.txt
                '''
            }
        }

        // ------------------------------------------------------------------
        // 3. PRE-DEPLOY HEALTH CHECK (test container)
        //    Spin up a throwaway container and verify the app is healthy
        //    before touching the live production container.
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
                            ${APP_NAME}:latest
                    """

                    def healthy = false
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
                        error("Pre-deploy health check failed — aborting deployment, rollback will run in post{}")
                    }
                }
            }
        }

        // ------------------------------------------------------------------
        // 4. DEPLOY (safe swap)
        //    Remove old prod container and start new one.
        // ------------------------------------------------------------------
        stage('Deploy') {
            steps {
                sh '''
                    set -e
                    docker rm -f ${PROD_CONTAINER} || true

                    docker run -d \
                        --name ${PROD_CONTAINER} \
                        --network bmi \
                        -p ${PROD_PORT}:5000 \
                        ${APP_NAME}:latest

                    echo "New container started on port ${PROD_PORT}"
                '''
            }
        }

        // ------------------------------------------------------------------
        // 5. POST-DEPLOY HEALTH CHECK (production container)
        //    Verifies the live container is healthy. Failure triggers rollback.
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
                                echo "Production container is healthy — deployment complete"
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

        // Rollback fires when build, pre-deploy check, deploy, or post-deploy
        // health check fails. Re-starts prod from the rollback snapshot.
        failure {
            script {
                def snapshotExists = sh(
                    script: "docker image inspect ${APP_NAME}:rollback > /dev/null 2>&1 && echo yes || echo no",
                    returnStdout: true
                ).trim()

                if (snapshotExists == 'yes') {
                    echo "== ROLLBACK: restarting ${PROD_CONTAINER} from ${APP_NAME}:rollback =="
                    try {
                        sh "docker rm -f ${PROD_CONTAINER} || true"
                        sh """
                            docker run -d \
                                --name ${PROD_CONTAINER} \
                                --network bmi \
                                -p ${PROD_PORT}:5000 \
                                ${APP_NAME}:rollback
                        """

                        def rbHealthy = false
                        for (int i = 1; i <= 6; i++) {
                            def response = sh(
                                script: "docker exec ${PROD_CONTAINER} curl -s --max-time 3 http://localhost:5000${HEALTH_PATH} || echo ''",
                                returnStdout: true
                            ).trim()
                            def status = response ? sh(script: "echo '${response}' | jq -r '.status' 2>/dev/null || echo unknown", returnStdout: true).trim() : 'unknown'
                            echo "Rollback health check [${i}/6] — status: ${status}"
                            if (status == 'healthy') { rbHealthy = true; break }
                            if (i < 6) sleep(5)
                        }

                        if (rbHealthy) {
                            echo "Rollback successful — previous version is live"
                        } else {
                            echo "CRITICAL: rollback container also unhealthy — manual intervention required"
                        }
                    } catch (err) {
                        echo "CRITICAL: rollback failed — ${err.getMessage()}"
                    }
                } else {
                    echo "No rollback snapshot found — skipped (was this the first build?)"
                }

                // Clean up test container if left behind
                sh "docker rm -f ${TEST_CONTAINER} || true"
            }
        }

        success {
            echo "Deployment succeeded — ${APP_NAME} is live on port ${PROD_PORT}"
        }

        always {
            emailext(
                to: "udaychopade27@gmail.com, uchopade27@gmail.com",
                subject: "[Jenkins] ${currentBuild.currentResult} - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
Hello Team,

Build Status : ${currentBuild.currentResult}
Job          : ${env.JOB_NAME}
Build Number : ${env.BUILD_NUMBER}
Build URL    : ${env.BUILD_URL}

Health check and safe deployment executed.
Logs attached if available.
                """,
                attachmentsPattern: "build_output.txt,container_error.log"
            )
            cleanWs()
        }
    }
}
