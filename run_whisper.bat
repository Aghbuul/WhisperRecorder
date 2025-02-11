@echo off
powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c cd /d %~dp0 && call venv\Scripts\activate && python whisper_recorder.py'" 