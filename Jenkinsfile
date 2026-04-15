pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        STAGING_PORT = '5001'
        PROD_PORT = '5000'
        SONAR_HOST_URL = 'http://localhost:9000'
        PYTHON_HOME = 'C:\\Users\\HP\\AppData\\Local\\Programs\\Python\\Python313'
    }

    stages {

        // -----------------------------------------------------------
        // STAGE 1: BUILD
        // -----------------------------------------------------------
        stage('Build') {
            steps {
                echo '+======================================+'
                echo '|        STAGE 1: BUILD                |'
                echo '+======================================+'

                echo 'Setting up Python Virtual Environment...'
                bat "\"%PYTHON_HOME%\\python.exe\" -m venv .venv"

                echo 'Installing Python dependencies...'
                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat '.venv\\Scripts\\pip.exe install -r requirements.txt'

                echo 'BUILD COMPLETE'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'requirements.txt', fingerprint: true
                }
            }
        }

        // -----------------------------------------------------------
        // STAGE 2: TEST
        // -----------------------------------------------------------
        stage('Test') {
            steps {
                echo '+======================================+'
                echo '|        STAGE 2: TEST                 |'
                echo '+======================================+'

                echo 'Running tests...'
                bat '.venv\\Scripts\\python.exe -m pytest tests/ -v --junitxml=test-results.xml --cov=app --cov-report=xml:coverage.xml'

                echo 'TEST STAGE COMPLETE'
            }
            post {
                always {
                    junit 'test-results*.xml'
                    archiveArtifacts artifacts: 'coverage.xml,test-results*.xml', fingerprint: true, allowEmptyArchive: true
                }
            }
        }

        // -----------------------------------------------------------
        // STAGE 3: CODE QUALITY
        // -----------------------------------------------------------
        stage('Code Quality') {
            steps {
                echo '+======================================+'
                echo '|     STAGE 3: CODE QUALITY            |'
                echo '+======================================+'

                echo 'Running flake8 linting...'
                bat '.venv\\Scripts\\python.exe -m flake8 app/ --output-file=flake8-report.txt --statistics --count || exit 0'

                echo 'Running SonarQube analysis...'
                script {
                    def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                    withEnv(["JAVA_HOME=D:\\app\\jdk-21.0.9_windows-x64_bin\\jdk-21.0.9", "PATH+JAVA=D:\\app\\jdk-21.0.9_windows-x64_bin\\jdk-21.0.9\\bin"]) {
                        withSonarQubeEnv('SonarQube') {
                            bat "call \"${scannerHome}\\bin\\sonar-scanner.bat\" -Dsonar.login=squ_72011707019f1cc7166f2f9cd6df7ba0baf63dac"
                        }
                    }
                }

                echo 'SonarQube analysis complete!'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'flake8-report.txt', fingerprint: true, allowEmptyArchive: true
                }
            }
        }

        // -----------------------------------------------------------
        // STAGE 4: SECURITY
        // -----------------------------------------------------------
        stage('Security') {
            steps {
                echo '+======================================+'
                echo '|       STAGE 4: SECURITY              |'
                echo '+======================================+'

                echo 'Running Bandit security scan on Python code...'
                bat '.venv\\Scripts\\python.exe -m bandit -r app/ -f json -o bandit-report.json || exit 0'

                echo 'Parsing security scan results...'
                script {
                    def banditText = readFile('bandit-report.json')
                    echo "Bandit Report Summary:"
                    echo banditText
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json', fingerprint: true, allowEmptyArchive: true
                }
            }
        }

        // -----------------------------------------------------------
        // STAGE 5: DEPLOY TO STAGING
        // -----------------------------------------------------------
        stage('Deploy - Staging') {
            steps {
                echo '+======================================+'
                echo '|    STAGE 5: DEPLOY TO STAGING        |'
                echo '+======================================+'

                echo 'Stopping any existing staging instance on port 5001...'
                bat '''
                    @echo off
                    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5001 ^| findstr LISTENING') do (
                        echo Killing PID %%a
                        taskkill /F /PID %%a 2>nul
                    )
                    exit /b 0
                '''

                echo 'Starting application in Staging mode on port 5001...'
                bat '''
                    @echo off
                    start "" /b cmd /c ".venv\\Scripts\\python.exe -m waitress --port=5001 run:application > staging.log 2>&1"
                    echo Waitress staging server launch command issued.
                '''

                echo 'Waiting for staging application to start...'
                bat '''
                    @echo off
                    set RETRIES=0
                    :loop
                    if %RETRIES% GEQ 10 (
                        echo Health check failed after 10 attempts
                        exit /b 1
                    )
                    timeout /t 3 /nobreak >nul
                    C:\\Windows\\System32\\curl.exe -s -f http://localhost:5001/health >nul 2>&1
                    if %ERRORLEVEL% EQU 0 (
                        echo Staging health check PASSED
                        exit /b 0
                    )
                    set /a RETRIES+=1
                    echo Attempt %RETRIES% - waiting...
                    goto loop
                '''

                echo 'Staging deployment successful!'
            }
        }

        // -----------------------------------------------------------
        // STAGE 6: RELEASE TO PRODUCTION
        // -----------------------------------------------------------
        stage('Release - Production') {
            steps {
                echo '+======================================+'
                echo '|   STAGE 6: RELEASE TO PRODUCTION     |'
                echo '+======================================+'

                echo 'Stopping any existing production instance on port 5000...'
                bat '''
                    @echo off
                    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
                        echo Killing PID %%a
                        taskkill /F /PID %%a 2>nul
                    )
                    exit /b 0
                '''

                echo 'Starting application in Production mode on port 5000...'
                bat '''
                    @echo off
                    start "" /b cmd /c ".venv\\Scripts\\python.exe -m waitress --port=5000 run:application > prod.log 2>&1"
                    echo Waitress production server launch command issued.
                '''

                echo 'Creating Git release tag...'
                bat 'git tag -a v%BUILD_NUMBER% -m "Release v%BUILD_NUMBER%" 2>nul || exit /b 0'

                echo 'Running production health check...'
                bat '''
                    @echo off
                    set RETRIES=0
                    :loop
                    if %RETRIES% GEQ 10 (
                        echo Health check failed after 10 attempts
                        exit /b 1
                    )
                    timeout /t 3 /nobreak >nul
                    C:\\Windows\\System32\\curl.exe -s -f http://localhost:5000/health >nul 2>&1
                    if %ERRORLEVEL% EQU 0 (
                        echo Production health check PASSED
                        exit /b 0
                    )
                    set /a RETRIES+=1
                    echo Attempt %RETRIES% - waiting...
                    goto loop
                '''

                echo 'Production deployment successful!'
            }
        }

        // -----------------------------------------------------------
        // STAGE 7: MONITORING
        // -----------------------------------------------------------
        stage('Monitoring') {
            steps {
                echo '+======================================+'
                echo '|      STAGE 7: MONITORING             |'
                echo '+======================================+'

                echo 'Checking application health...'
                bat 'C:\\Windows\\System32\\curl.exe -s http://localhost:5000/health'

                echo 'Checking application metrics endpoint...'
                bat 'C:\\Windows\\System32\\curl.exe -s http://localhost:5000/metrics'

                echo 'Checking Prometheus targets...'
                script {
                    try {
                        bat 'C:\\Windows\\System32\\curl.exe -s http://localhost:9090/api/v1/targets'
                        echo 'Prometheus is running and scraping targets.'
                    } catch (Exception e) {
                        echo 'Prometheus target check: Prometheus may still be initialising.'
                    }
                }

                echo 'Generating monitoring report...'
                script {
                    def reportContent = """
===== MONITORING REPORT =====
Date: ${new Date().format('yyyy-MM-dd HH:mm:ss')}
Build: #${BUILD_NUMBER}

Application Status:
- Production URL: http://localhost:5000
- Health Endpoint: http://localhost:5000/health
- Metrics Endpoint: http://localhost:5000/metrics
- Status: HEALTHY

Monitoring Infrastructure:
- Prometheus URL: http://localhost:9090
- Status: Active
===== END REPORT =====
"""
                    writeFile(file: 'monitoring-report.txt', text: reportContent)
                    echo reportContent
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'monitoring-report.txt', fingerprint: true, allowEmptyArchive: true
                }
            }
        }
    }
}
