@echo off
rem Test: run the emulator without parameters.
setlocal
cd /d "%~dp0.."

call :run
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
