@echo off
rem Test: all commands of stages 1-3 on a deeply nested VFS.
setlocal
cd /d "%~dp0.."

call :run --vfs examples\vfs\deep.csv --script examples\scripts\stage3_all.txt
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
