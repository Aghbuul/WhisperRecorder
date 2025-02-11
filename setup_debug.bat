@echo off
setlocal EnableDelayedExpansion

echo [DEBUG] Starting setup script...
echo [DEBUG] Current directory: %CD%

:: Check if running in PowerShell
set "PS_CHECK="
for /f "tokens=*" %%a in ('echo %PSModulePath%') do set PS_CHECK=%%a
if defined PS_CHECK (
    echo [DEBUG] Running in PowerShell environment
) else (
    echo [DEBUG] Running in CMD environment
)

:: Force use of CMD
set "CMDCMDLINE=cmd.exe"

echo [DEBUG] Checking for Python...
python --version 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

:: Get Python path with error checking
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    echo [DEBUG] Found Python at: %%i
    set "PYTHON_PATH=%%i"
)

if not defined PYTHON_PATH (
    echo [ERROR] Failed to get Python path
    pause
    exit /b 1
)

echo [DEBUG] Testing Python execution...
"%PYTHON_PATH%" --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to execute Python
    pause
    exit /b 1
)

echo [DEBUG] Current directory path: %~dp0
set "TARGET_DIR=%~dp0"
echo [DEBUG] Target directory: %TARGET_DIR%

echo [DEBUG] Checking if files exist...
if exist "%TARGET_DIR%whisper_recorder.py" (
    echo [DEBUG] Found whisper_recorder.py
) else (
    echo [ERROR] whisper_recorder.py not found in %TARGET_DIR%
    pause
    exit /b 1
)

if exist "%TARGET_DIR%whisper_cpp_wrapper.py" (
    echo [DEBUG] Found whisper_cpp_wrapper.py
) else (
    echo [ERROR] whisper_cpp_wrapper.py not found in %TARGET_DIR%
    pause
    exit /b 1
)

echo [DEBUG] Creating recordings directory...
if not exist "%TARGET_DIR%recordings" (
    mkdir "%TARGET_DIR%recordings"
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create recordings directory
        pause
        exit /b 1
    )
    echo [DEBUG] Created recordings directory
) else (
    echo [DEBUG] Recordings directory already exists
)

echo [DEBUG] Attempting to update whisper_recorder.py...
"%PYTHON_PATH%" -c "
try:
    print('[DEBUG] Reading whisper_recorder.py...')
    with open('whisper_recorder.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'[DEBUG] File content length: {len(content)}')
    
    old_path = r'E:\Cursor\Whisper'
    new_path = r'%TARGET_DIR%'.rstrip('\\').replace('\\', '/')
    print(f'[DEBUG] Replacing {old_path} with {new_path}')
    
    content = content.replace(old_path, new_path)
    
    print('[DEBUG] Writing updated content...')
    with open('whisper_recorder.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('[DEBUG] Update complete')
except Exception as e:
    print(f'[ERROR] Failed: {str(e)}')
    exit(1)
"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to update whisper_recorder.py
    pause
    exit /b 1
)

echo [DEBUG] Attempting to update whisper_cpp_wrapper.py...
"%PYTHON_PATH%" -c "
try:
    print('[DEBUG] Reading whisper_cpp_wrapper.py...')
    with open('whisper_cpp_wrapper.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'[DEBUG] File content length: {len(content)}')
    
    old_path = r'E:\Cursor\Whisper'
    new_path = r'%TARGET_DIR%'.rstrip('\\').replace('\\', '/')
    print(f'[DEBUG] Replacing {old_path} with {new_path}')
    
    content = content.replace(old_path, new_path)
    
    print('[DEBUG] Writing updated content...')
    with open('whisper_cpp_wrapper.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('[DEBUG] Update complete')
except Exception as e:
    print(f'[ERROR] Failed: {str(e)}')
    exit(1)
"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to update whisper_cpp_wrapper.py
    pause
    exit /b 1
)

echo [DEBUG] Setup completed successfully
echo [DEBUG] Final directory structure:
dir /s /b "%TARGET_DIR%"

echo.
echo [SUCCESS] Setup completed! You can now run Whisper Recorder using run_whisper.bat
echo.
pause 