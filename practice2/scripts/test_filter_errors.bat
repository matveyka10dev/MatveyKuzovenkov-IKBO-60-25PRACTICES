@echo off
rem Test: errors of --filter.
setlocal
cd /d "%~dp0.."

call :run --package org.junit:junit --filter
call :run --package org.junit:junit --filter ""
call :run --package org.junit:junit --filter "ham crest"
call :run --package org.junit:junit --filter junit
call :run --test-mode --repo examples\repos\simple.txt --package ABC --filter B
call :run --package org.junit:junit --filter a --filter b
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
