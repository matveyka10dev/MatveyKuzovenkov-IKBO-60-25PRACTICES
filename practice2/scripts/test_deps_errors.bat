@echo off
rem Test: errors of getting dependencies: missing package, bad POM, network.
setlocal
cd /d "%~dp0.."
set "PORT=8765"
set "REPO_URL=http://127.0.0.1:%PORT%"
start "depviz-repo" /min python -m http.server %PORT% --bind 127.0.0.1 --directory examples\maven-repo
ping -n 3 127.0.0.1 > NUL

call :run --package org.example:ghost:1.0 --repo %REPO_URL%
call :run --package org.example:ghost --repo %REPO_URL%
call :run --package org.example:no-versions --repo %REPO_URL%
call :run --package org.example:broken-xml:1.0 --repo %REPO_URL%
call :run --package org.example:not-a-pom:1.0 --repo %REPO_URL%
call :run --package org.example:orphan:1.0 --repo %REPO_URL%
call :run --package org.example:cycle-a:1.0 --repo %REPO_URL%
call :run --package junit:junit --repo http://127.0.0.1:1
call :run --package junit:junit --repo http://no-such-host.invalid/maven2
taskkill /fi "WINDOWTITLE eq depviz-repo*" /t /f > NUL 2>&1
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
