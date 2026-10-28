@echo off
rem Test: minimal VFS (root directory only).
setlocal
cd /d "%~dp0.."

call :run --vfs examples\vfs\minimal.csv --script examples\scripts\vfs_minimal.txt
rem Without --vfs an empty VFS is used
call :run --script examples\scripts\vfs_minimal.txt
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
