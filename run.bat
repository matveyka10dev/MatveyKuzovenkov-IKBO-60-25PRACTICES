@echo off
rem Run the emulator: run.bat [emulator options]
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m shell_emu %*
