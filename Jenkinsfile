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
                echo "run the image"
                sh "docker run -d -p 5000:5000 bmi-app"
            }
        }
    }

    post {
        always {
            script {
                def buildStatus = currentBuild.currentResult   // FIXED
                def subject = "[Jenkins] ${buildStatus} - Frontend Deployment: ${env.JOB_NAME} [${env.BUILD_NUMBER}]"
                
                def body = """
Build Status: ${buildStatus}
Job: ${env.JOB_NAME}
Build URL: ${env.BUILD_URL}
"""

                // Add logs only on failure
                if (buildStatus == "FAILURE") {
                    try {
                        def logContent = currentBuild.rawBuild.getLog(100).join('\n')  // FIXED
                        body += """
--- Last 100 Lines of Error Log ---
${logContent}
-----------------------------------
"""
                    } catch (err) {
                        body += "\nFailed to fetch logs: ${err}\n"
                    }
                }

                def recipients = "udaychopade27@gmail.com, uchopade27@gmail.com"

                mail(to: recipients, subject: subject, body: body)
            }
        }

        success {
            echo "✅ Frontend CI/CD pipeline completed successfully."
        }
        failure {
            echo "❌ Pipeline failed. Check email for logs."
        }
    }
}
