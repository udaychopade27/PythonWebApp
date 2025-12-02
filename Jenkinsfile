pipeline {
    agent any 
    
    stages {
        stage("Build") {
            steps {
                echo "Building the image"
                sh "docker build -t bmi-app ."
            }
        }

        stage("Run") {
            steps {
                echo "Running the image"
                sh "docker run -d -p 5000:5000 bmi-app"
            }
        }
    }

    post {
        always {
            script {

                def buildStatus = currentBuild.currentResult
                def subject = "[Jenkins] ${buildStatus} - Deployment: ${env.JOB_NAME} [${env.BUILD_NUMBER}]"

                def body = """
                    Build Status: ${buildStatus}
                    Job: ${env.JOB_NAME}
                    Build URL: ${env.BUILD_URL}
                    """

                if (buildStatus == "FAILURE") {
                    try {
                        def run = Jenkins.getInstance()
                            .getItemByFullName(env.JOB_NAME)
                            .getBuildByNumber(env.BUILD_NUMBER.toInteger())

                        def logContent = run.getLog(100).join("\n")

                        body += """
                               --- Last 100 Lines of Log ---
                               ${logContent}
                               -----------------------------------
                        """
                    } catch (err) {
                        body += "Failed to fetch error logs: ${err}\n"
                    }
                }

                def recipients = "udaychopade27@gmail.com, uchopade27@gmail.com"

                mail(to: recipients, subject: subject, body: body)
            }
        }

        success {
            echo "✅ Pipeline completed successfully."
        }

        failure {
            echo "❌ Pipeline failed."
        }
    }
}
