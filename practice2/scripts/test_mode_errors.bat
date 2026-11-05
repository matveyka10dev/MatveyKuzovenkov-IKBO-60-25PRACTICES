@echo off
rem Test: errors of --test-mode and --ascii-tree flags.
setlocal
cd /d "%~dp0.."

call :run --package A --repo examples\repos\simple.txt --test-mode=yes
call :run --package A --repo examples\repos\simple.txt --test-mode --test-mode
call :run --package A --repo examples\repos\simple.txt -tt
call :run --package org.junit:junit --ascii-tree=on
call :run --package org.junit:junit --ascii-tree --ascii-tree
call :run --package org.junit:junit -a 1
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
