@echo off
rem Test: invalid test repository files.
setlocal
cd /d "%~dp0.."

call :run --test-mode --repo examples\repos\broken\bad_name.txt --package A
call :run --test-mode --repo examples\repos\broken\no_colon.txt --package A
call :run --test-mode --repo examples\repos\broken\duplicate_package.txt --package A
call :run --test-mode --repo examples\repos\broken\duplicate_dependency.txt --package A
call :run --test-mode --repo examples\repos\broken\empty.txt --package A
call :run --test-mode --repo examples\repos\broken\not_utf8.txt --package A
exit /b 0

:run
rem Print the command, run the tool, show the exit code.
echo ^> run.bat %*
call run.bat %*
echo [exit code: %errorlevel%]
echo.
exit /b
