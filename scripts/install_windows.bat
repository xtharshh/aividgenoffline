@echo off
setlocal
echo ============================================================
echo   Offline AI Avatar Video Generator - Windows Setup
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10 from https://python.org
    pause & exit /b 1
)
for /f %%i in ('python -c "import sys; print(sys.version_info.major)"') do set PY_MAJOR=%%i
for /f %%i in ('python -c "import sys; print(sys.version_info.minor)"') do set PY_MINOR=%%i
if %PY_MAJOR% NEQ 3 (
    echo [ERROR] Unsupported Python version. Use Python 3.10 or 3.11.
    pause & exit /b 1
)
if %PY_MINOR% LSS 10 (
    echo [ERROR] Python %PY_MAJOR%.%PY_MINOR% is too old. Use Python 3.10 or 3.11.
    pause & exit /b 1
)
if %PY_MINOR% GTR 11 (
    echo [ERROR] Python %PY_MAJOR%.%PY_MINOR% is not supported by coqui-tts.
    echo         Install Python 3.11 and rerun this script.
    pause & exit /b 1
)
echo [OK] Python found

:: Check Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found. Install from https://git-scm.com
    pause & exit /b 1
)
echo [OK] Git found

:: Check FFmpeg
if exist "C:\Program Files\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe" (
    set "PATH=C:\Program Files\ffmpeg-8.1.1-essentials_build\bin;%PATH%"
    echo [OK] FFmpeg found
) else if exist "C:\ffmpeg\bin\ffmpeg.exe" (
    set "PATH=C:\ffmpeg\bin;%PATH%"
    echo [OK] FFmpeg found
) else (
    ffmpeg -version >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] FFmpeg not found.
        echo Install FFmpeg:
        echo   1. Download from https://www.gyan.dev/ffmpeg/builds/
        echo   2. Extract and add bin/ folder to your PATH
        echo   3. Restart this script
        pause & exit /b 1
    )
    echo [OK] FFmpeg found
)

:: Create venv
echo.
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

:: Upgrade pip and install build tools
echo Upgrading pip and installing build tools...
python -m pip install --upgrade pip setuptools wheel --disable-pip-version-check

:: Install build dependencies for Windows compilation
echo Installing build dependencies...
python -m pip install --upgrade numpy --disable-pip-version-check

:: Install PyTorch with CUDA 11.8 (adjust cu118 to cu121 for CUDA 12.1)
echo.
echo Installing PyTorch with CUDA support...
echo This may take 5-15 minutes depending on your internet speed...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir --disable-pip-version-check

:: Install requirements
echo.
echo Installing Python dependencies...
echo This may take 3-8 minutes...

pip install -r requirements.txt --no-cache-dir --disable-pip-version-check --retries 5
:: Create directories
mkdir output 2>nul
mkdir temp 2>nul
mkdir projects 2>nul
mkdir models 2>nul
mkdir repos 2>nul
mkdir logs 2>nul

:: Download minimal models
echo.
echo Downloading model checkpoints (minimal set, ~560 MB)...
python scripts\download_models.py --minimal

echo.
echo ============================================================
echo   Setup complete!
echo.
echo   Usage:
echo     venv\Scripts\activate
echo     python generate.py --script script.txt --avatar avatar.jpg --output out.mp4
echo.
echo   For full quality (downloads ~2 GB more):
echo     python scripts\download_models.py --full
echo ============================================================
pause
