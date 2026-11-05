@echo off
rem Test: valid parameters, short forms, any order.
setlocal
cd /d "%~dp0.."

call :run --package org.junit:junit:4.13.2
call :run --package com.google.guava:guava
call :run -p org.slf4j:slf4j-api:2.0.9 -r https://repo.maven.apache.org/maven2 -a
call :run --package=org.junit:junit:4.13.2 --repo=https://repo.maven.apache.org/maven2 --filter=hamcrest
call :run --test-mode --repo examples\repos\simple.txt --package A
call :run -t -a -f E -r examples\repos\simple.txt -p A
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
