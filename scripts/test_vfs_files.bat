@echo off
rem Test: VFS with several files (text, multiline text, base64).
setlocal
cd /d "%~dp0.."

call :run --vfs examples\vfs\files.csv --script examples\scripts\vfs_files.txt
rem The same kind of VFS saved by Excel: BOM, CRLF, semicolons
call :run --vfs examples\vfs\excel.csv --script examples\scripts\vfs_excel.txt
exit /b 0

:run
rem Print the command, run the emulator with empty input, show exit code.
echo ^> run.bat %*
call run.bat %* < NUL
echo [exit code: %errorlevel%]
echo.
exit /b
