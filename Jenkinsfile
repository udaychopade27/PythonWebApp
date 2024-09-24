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
}

        

