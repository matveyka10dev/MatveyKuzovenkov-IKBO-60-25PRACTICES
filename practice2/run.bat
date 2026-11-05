@echo off
rem Run the tool: run.bat [options]
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m depviz %*
