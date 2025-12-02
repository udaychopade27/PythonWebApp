pipeline {
    agent any 
    
    stages {

        stage("Build") {
            steps {
                sh """
                docker build -t bmi-app . 2>&1 | tee build_output.log
                """
            }
        }

        stage("Run") {
            steps {
                sh """
                docker run -d -p 5000:5000 bmi-app 2>&1 | tee -a build_output.log || true
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

Build log has been attached.
                """,
                attachmentsPattern: "build_output.log"
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
