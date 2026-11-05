@echo off
rem Test: errors of --repo.
setlocal
cd /d "%~dp0.."

call :run --package org.junit:junit --repo
call :run --package org.junit:junit --repo ""
call :run --package org.junit:junit --repo ftp://repo.example.com/maven2
call :run --package org.junit:junit --repo https:///maven2
call :run --package org.junit:junit --repo "https://repo.example.com/my repo"
call :run --package org.junit:junit --repo examples\repos\simple.txt
call :run --package A --test-mode
call :run --package A --test-mode --repo https://repo1.maven.org/maven2
call :run --package A --test-mode --repo no\such\file.txt
call :run --package A --test-mode --repo examples\repos
call :run --package A --repo http://a.org --repo http://b.org
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
