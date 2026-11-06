@echo off
rem Test: dependency graph from the local Maven repository (offline).
setlocal
cd /d "%~dp0.."
set "PORT=8765"
set "REPO_URL=http://127.0.0.1:%PORT%"
start "depviz-repo" /min python -m http.server %PORT% --bind 127.0.0.1 --directory examples\maven-repo
ping -n 3 127.0.0.1 > NUL

call :run --package junit:junit --repo %REPO_URL%
call :run --package org.example:demo-app --repo %REPO_URL%
call :run --package org.example:demo-app --filter google --repo %REPO_URL%
call :run --package org.example:cycle-x:1.0 --repo %REPO_URL%
call :run --package org.example:cycle-x:1.0 --filter cycle-z --repo %REPO_URL%
call :run --package org.example:missing-dep:1.0 --repo %REPO_URL%
taskkill /fi "WINDOWTITLE eq depviz-repo*" /t /f > NUL 2>&1
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
