@echo off
rem Test: --script parameter (success, first error, exit).
setlocal
cd /d "%~dp0.."

call :run --script examples\scripts\stage2_ok.txt
call :run --script examples\scripts\stage2_error.txt
call :run --script examples\scripts\stage2_exit.txt
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
