@echo off
rem Test: filtering packages by substring in test repositories.
setlocal
cd /d "%~dp0.."

call :run --test-mode --repo examples\repos\simple.txt --package A --filter C
call :run --test-mode --repo examples\repos\cycle.txt --package A --filter B
call :run --test-mode --repo examples\repos\cycles.txt --package A --filter E
call :run --test-mode --repo examples\repos\names.txt --package APP --filter LO
call :run --test-mode --repo examples\repos\names.txt --package APP --filter T
call :run --test-mode --repo examples\repos\names.txt --package APP --filter O
call :run --test-mode --repo examples\repos\names.txt --package WEB --filter ON
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
