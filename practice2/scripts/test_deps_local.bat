@echo off
rem Test: direct dependencies from the local Maven repository (offline).
setlocal
cd /d "%~dp0.."
set "PORT=8765"
set "REPO_URL=http://127.0.0.1:%PORT%"
start "depviz-repo" /min python -m http.server %PORT% --bind 127.0.0.1 --directory examples\maven-repo
ping -n 3 127.0.0.1 > NUL

call :run --package junit:junit:4.13.2 --repo %REPO_URL%
call :run --package junit:junit --repo %REPO_URL%
call :run --package org.example:demo-app --repo %REPO_URL%
call :run --package org.example:demo-app:1.0.0 --repo %REPO_URL%
call :run --package org.hamcrest:hamcrest-library:1.3 --repo %REPO_URL%
call :run --package org.example:no-deps:1.0 --repo %REPO_URL%
taskkill /fi "WINDOWTITLE eq depviz-repo*" /t /f > NUL 2>&1
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
