@echo off
rem Test: direct dependencies of real packages from Maven Central (online).
setlocal
cd /d "%~dp0.."

call :run --package junit:junit:4.13.2
call :run --package com.google.guava:guava:33.0.0-jre
call :run --package org.apache.commons:commons-lang3:3.14.0
call :run --package org.slf4j:slf4j-api
call :run --package org.springframework:spring-core:6.1.4 --repo https://repo.maven.apache.org/maven2
call :run --package org.example:no-such-package:1.0
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
