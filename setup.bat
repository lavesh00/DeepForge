@echo off
setlocal enabledelayedexpansion

if "%1"=="start" goto START_SERVER
if "%1"=="test" goto TEST
if "%1"=="clean" goto CLEAN

REM ========================================
REM DEEPFORGE COMPLETE SETUP
REM ========================================

echo ========================================
echo   DeepForge Complete Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ and add it to PATH
    pause
    exit /b 1
)

echo [1/7] Python check...
python --version

REM Create virtual environment
echo.
echo [2/7] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [3/7] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo [4/7] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARNING] Pip upgrade failed, continuing...
)

REM Install project dependencies
echo.
echo [5/7] Installing project dependencies...
pip install -e . --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install project dependencies
    pause
    exit /b 1
)

REM Install ML dependencies
echo.
echo [6/7] Installing ML dependencies (transformers, torch, huggingface-hub)...
pip install transformers torch huggingface-hub --quiet
if errorlevel 1 (
    echo [WARNING] ML dependencies failed, DeepSeek model may not work
)

REM Create all required directories
echo.
echo [7/7] Creating directories...
if not exist "%USERPROFILE%\.deepforge" mkdir "%USERPROFILE%\.deepforge"
if not exist "%USERPROFILE%\.deepforge\state" mkdir "%USERPROFILE%\.deepforge\state"
if not exist "%USERPROFILE%\.deepforge\state\missions" mkdir "%USERPROFILE%\.deepforge\state\missions"
if not exist "%USERPROFILE%\.deepforge\logs" mkdir "%USERPROFILE%\.deepforge\logs"
if not exist "%USERPROFILE%\.deepforge\models" mkdir "%USERPROFILE%\.deepforge\models"
if not exist "%USERPROFILE%\deepforge_workspaces" mkdir "%USERPROFILE%\deepforge_workspaces"

REM Verify installation
echo.
echo Verifying installation...
python -m interface.cli.deepforge --help >nul 2>&1
if errorlevel 1 (
    echo [WARNING] CLI verification failed
) else (
    echo [OK] Installation verified successfully
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start the server, run:
echo   setup.bat start
echo.
echo Or test the installation:
echo   setup.bat test
echo.
goto END

:START_SERVER
echo ========================================
echo   Starting DeepForge Server
echo ========================================
echo.
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Running setup first...
    echo.
    call "%~f0"
    if errorlevel 1 (
        echo [ERROR] Setup failed. Cannot start server.
        pause
        exit /b 1
    )
    echo.
    echo Setup complete. Starting server...
    echo.
)
call venv\Scripts\activate.bat
echo Starting server on http://localhost:8080
echo Press Ctrl+C to stop
echo.
python -m interface.api.server
goto END

:TEST
echo ========================================
echo   Testing DeepForge Installation
echo ========================================
echo.
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python scripts\verify_all.py
goto END

:CLEAN
echo ========================================
echo   Cleaning DeepForge Installation
echo ========================================
echo.
echo This will remove:
echo   - Virtual environment (venv)
echo   - Python cache files (__pycache__)
echo   - Build artifacts
echo.
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    goto END
)
if exist "venv" rmdir /s /q "venv"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f"
if exist "deepforge.egg-info" rmdir /s /q "deepforge.egg-info"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo Clean complete.
goto END

:END
endlocal
