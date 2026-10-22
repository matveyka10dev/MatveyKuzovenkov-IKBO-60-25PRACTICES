@echo off
rem Test: both parameters in different order.
setlocal
cd /d "%~dp0.."

call :run --vfs examples\vfs\minimal.csv --script examples\scripts\stage2_ok.txt
call :run --script examples\scripts\stage2_ok.txt --vfs examples\vfs\minimal.csv
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
