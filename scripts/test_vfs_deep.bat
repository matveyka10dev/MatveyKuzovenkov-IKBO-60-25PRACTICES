@echo off
rem Test: VFS with at least 3 levels of files and directories.
setlocal
cd /d "%~dp0.."

call :run --vfs examples\vfs\deep.csv --script examples\scripts\vfs_deep.txt
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
