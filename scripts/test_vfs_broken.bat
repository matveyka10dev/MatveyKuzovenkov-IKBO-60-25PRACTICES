@echo off
rem Test: invalid CSV files and a missing VFS file.
setlocal
cd /d "%~dp0.."

for %%f in (examples\vfs\broken\*.csv) do call :run --vfs "%%f"
call :run --vfs examples\vfs\no_such_file.csv
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
