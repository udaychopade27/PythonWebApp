pipeline {
    agent any 
    
    stages{
        stage("Build"){
            steps {
                echo "Building the image"
                sh "docker build -t bmi-app ."
            }
        }

        stage("Run"){
            steps {
                echo "run the image"
                sh "docker run -d -p 5000:5000  bmi-app "
            }
        }
    }
    post {
  // Always run these actions, regardless of build status
  always {
    // Collect the email body based on success or failure
    script {
      def buildStatus = currentBuild.result
      def subject = "[Jenkins] ${buildStatus} - Frontend Deployment: ${env.JOB_NAME} [${env.BUILD_NUMBER}]"
      def body = "Build Status: ${buildStatus}\n" +
                 "Job: ${env.JOB_NAME}\n" +
                 "Build URL: ${env.BUILD_URL}\n"
                 
      // Add error details on failure
      if (buildStatus == 'FAILURE') {
          // Get the last 100 lines of the build log
          def logContent = currentBuild.rawBuild.log.take(100).join('\n')
          
          body += "\n--- Last 100 Lines of Error Log ---\n" +
                  "${logContent}\n" +
                  "-----------------------------------\n"
      }
      
      // Define the list of email recipients (replace with your actual group emails)
      def recipients = "udaychopade27@gmail.com, uchopade27@gmail.com"
      
      // Send the email
      mail(to: recipients, subject: subject, body: body)
    }
  }

  success {
    echo "✅ Frontend CI/CD pipeline completed successfully (build on Jenkins, deployed to EC2)."
  }
  failure {
    echo "❌ Frontend CI/CD pipeline failed. Existing site on EC2 remains serving last successful version."
  }
}
}

        

