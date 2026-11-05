@echo off
rem Test: errors of --package.
setlocal
cd /d "%~dp0.."

call :run --repo examples\repos\simple.txt
call :run --package
call :run --package ""
call :run --package junit
call :run --package "org.junit:junit 4"
call :run --package org.junit:junit:4.13:extra
call :run --test-mode --repo examples\repos\simple.txt --package a
call :run --test-mode --repo examples\repos\simple.txt --package org.junit:junit
call :run --package A --package B
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
