@echo off
rem Test: error handling, each script stops at its first error.
setlocal
cd /d "%~dp0.."

for %%f in (examples\scripts\errors\*.txt) do call :run --vfs examples\vfs\deep.csv --script "%%f"
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
