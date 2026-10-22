@echo off
rem Test: --help, invalid parameters, missing script file.
setlocal
cd /d "%~dp0.."

call :run --help
call :run --unknown
call :run --vfs
call :run --script no\such\script.txt
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
