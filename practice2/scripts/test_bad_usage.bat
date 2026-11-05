@echo off
rem Test: help, unknown options, extra arguments.
setlocal
cd /d "%~dp0.."

call :run --help
call :run 
call :run --package org.junit:junit --unknown
call :run --package org.junit:junit extra
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
