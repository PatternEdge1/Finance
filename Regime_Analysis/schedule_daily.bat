@echo off
REM ============================================================================
REM Daily Regime Dashboard - Windows Task Scheduler Runner
REM ============================================================================
REM 
REM This batch file is designed to be run by Windows Task Scheduler
REM to automate daily video generation after market close.
REM
REM SETUP INSTRUCTIONS:
REM 1. Open Task Scheduler (taskschd.msc)
REM 2. Create New Task (not Basic Task)
REM 3. General tab:
REM    - Name: "Daily Regime Dashboard"
REM    - Run whether user is logged on or not (requires password)
REM 4. Triggers tab:
REM    - New trigger: Daily at 7:00 PM (after market close)
REM    - Enable: Yes
REM 5. Actions tab:
REM    - Action: Start a program
REM    - Program: Full path to this .bat file
REM    - Start in: Directory containing this file
REM 6. Conditions tab:
REM    - Uncheck "Start only if on AC power" (if on laptop)
REM 7. Settings tab:
REM    - Allow task to be run on demand: Yes
REM    - Stop task if runs longer than: 1 hour
REM
REM ============================================================================

REM Change to the script directory
cd /d "%~dp0"

echo ============================================================================
echo Daily Regime Dashboard Video Generator
echo Starting: %date% %time%
echo ============================================================================

REM ============================================================================
REM ENVIRONMENT ACTIVATION (uncomment and configure as needed)
REM ============================================================================

REM If using Anaconda/Miniconda:
REM call C:\Users\YourUsername\Anaconda3\Scripts\activate.bat
REM call conda activate your_env_name

REM If using Python venv:
REM call venv\Scripts\activate.bat

REM If using standard Python installation (ensure Python is in PATH):
REM No activation needed

REM ============================================================================
REM RUN VIDEO GENERATION
REM ============================================================================

echo.
echo Running video generation...
py -3 daily_regime_video.py SPY QQQ IWM DIA XLF XLK XLE XLV

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Video generation failed with code %ERRORLEVEL%
    echo Check the log file for details.
    exit /b %ERRORLEVEL%
)

echo.
echo Video generation completed successfully!

REM ============================================================================
REM OPTIONAL: AUTO-UPLOAD TO YOUTUBE (uncomment to enable)
REM ============================================================================

REM echo.
REM echo Running YouTube upload...
REM py -3 auto_upload.py
REM 
REM if %ERRORLEVEL% NEQ 0 (
REM     echo.
REM     echo WARNING: YouTube upload failed with code %ERRORLEVEL%
REM     echo Video was generated successfully but not uploaded.
REM     exit /b 0
REM )
REM 
REM echo YouTube upload completed successfully!

REM ============================================================================
REM COMPLETION
REM ============================================================================

echo.
echo ============================================================================
echo Daily Regime Dashboard - Complete
echo Finished: %date% %time%
echo ============================================================================

exit /b 0
