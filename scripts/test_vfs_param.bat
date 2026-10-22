@echo off
rem Test: --vfs parameter (path to the physical location of the VFS).
setlocal
cd /d "%~dp0.."

call :run --vfs examples\vfs\minimal.csv
call :run "--vfs=examples\vfs\deep.csv"
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
