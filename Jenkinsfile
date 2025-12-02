pipeline {
    agent any 
    
    stages {
        stage("Build") {
            steps {
                sh "docker build -t bmi-app ."
            }
        }

        stage("Run") {
            steps {
                sh "docker run -d -p 5000:5000 bmi-app || true"
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
Job Name: ${env.JOB_NAME}
Build Number: ${env.BUILD_NUMBER}
Build URL: ${env.BUILD_URL}

The last 100 lines of the build log have been attached.

Regards,
Jenkins
""",
                attachLog: true,   // <-- THIS ATTACHES FULL LOG
                compressLog: false // optional: compress to .gz
            )
        }

        success {
            echo "Pipeline succeeded."
        }

        failure {
            echo "Pipeline failed."
        }
    }
}
