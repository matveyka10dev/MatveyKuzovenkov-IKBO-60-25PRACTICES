@echo off
rem Test: dependency graph in test repositories: diamond, cycles, depth, missing packages.
setlocal
cd /d "%~dp0.."

call :run --test-mode --repo examples\repos\simple.txt --package A
call :run --test-mode --repo examples\repos\cycle.txt --package A
call :run --test-mode --repo examples\repos\cycle.txt --package C
call :run --test-mode --repo examples\repos\self_cycle.txt --package A
call :run --test-mode --repo examples\repos\cycles.txt --package A
call :run --test-mode --repo examples\repos\cycles.txt --package D
call :run --test-mode --repo examples\repos\deep.txt --package A
call :run --test-mode --repo examples\repos\names.txt --package APP
call :run --test-mode --repo examples\repos\missing.txt --package A
call :run --test-mode --repo examples\repos\simple.txt --package Q
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
