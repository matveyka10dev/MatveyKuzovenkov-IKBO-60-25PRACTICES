@echo off
rem Test: load order of dependencies in test repositories.
setlocal
cd /d "%~dp0.."

call :run --test-mode --repo examples\repos\simple.txt --package A --load-order
call :run --test-mode --repo examples\repos\cycle.txt --package A --load-order
call :run --test-mode --repo examples\repos\cycles.txt --package A --load-order
call :run --test-mode --repo examples\repos\names.txt --package APP --load-order
call :run --test-mode --repo examples\repos\names.txt --package APP --filter T --load-order
call :run --test-mode --repo examples\repos\missing.txt --package A --load-order
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
