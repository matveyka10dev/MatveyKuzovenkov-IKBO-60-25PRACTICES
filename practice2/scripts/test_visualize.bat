@echo off
rem Test: visualization of three packages: Graphviz, image and ASCII tree.
setlocal
cd /d "%~dp0.."

call :run --test-mode --repo examples\repos\simple.txt --package A
call :run --test-mode --repo examples\repos\cycles.txt --package A
call :run --test-mode --repo examples\repos\names.txt --package APP
call :run --test-mode --repo examples\repos\simple.txt --package A --ascii-tree
call :run --test-mode --repo examples\repos\cycles.txt --package A --ascii-tree
call :run --test-mode --repo examples\repos\names.txt --package APP --ascii-tree
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
