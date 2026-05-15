# Installation Troubleshooting Guide

Comprehensive guide for resolving common installation issues on Windows, Linux, and macOS.

---

## Common Installation Errors & Solutions

### ❌ Error: `ERROR: Could not find a version that satisfies the requirement TTS>=0.22.0`

**Cause**: Package name is incorrect in requirements.txt. The package is `coqui-tts`, not `TTS`.

**Status**: ✅ **FIXED** - Updated to `coqui-tts>=0.22.0`

**If you see this error**:
1. Ensure your `requirements.txt` uses `coqui-tts` not `TTS`
2. Delete and recreate venv:
   ```bash
   rmdir venv /s /q
   python -m venv venv
   venv\Scripts\activate
   ```
3. Reinstall:
   ```bash
   pip install -r requirements.txt
   ```

---

### ❌ Error: `NameError: name 'CCompiler' is not defined` (NumPy build error)

**Cause**: NumPy <1.26 uses old `distutils` that conflicts with Python 3.10+ and newer setuptools.

**Status**: ✅ **FIXED** - Updated to `numpy>=1.26.0`

**What's happening**:
- Old NumPy versions tried to build from source
- They used deprecated `distutils` module
- Modern setuptools removed this module
- Result: Build fails with `CCompiler` not defined

**If you see this error**:

1. **Option 1: Clean reinstall** (Recommended)
   ```bash
   # Remove venv completely
   rmdir venv /s /q
   
   # Create fresh venv
   python -m venv venv
   venv\Scripts\activate
   
   # Upgrade pip and setuptools first
   python -m pip install --upgrade pip setuptools wheel
   
   # Install pre-built NumPy (avoids compilation)
   python -m pip install "numpy>=1.26.0"
   
   # Then install all requirements
   pip install -r requirements.txt --no-cache-dir
   ```

2. **Option 2: Skip build entirely**
   ```bash
   pip install -r requirements.txt --only-binary :all: --no-build-isolation
   ```

3. **Option 3: Install build tools** (Windows)
   - Download: https://visualstudio.microsoft.com/downloads/
   - Select: "Desktop development with C++"
   - Reinstall: `pip install -r requirements.txt --no-cache-dir`

---

### ❌ Error: `error: subprocess-exited-with-error` when installing Wav2Lip dependencies

**Cause**: Wav2Lip repo has very old `requirements.txt` with packages incompatible with Python 3.10+.

**Status**: ✅ **PARTIALLY FIXED** - Model downloader now skips on error and continues.

**What's happening**:
- Wav2Lip requires: `numpy<1.20`, `scipy<1.5.0`, `librosa==0.7.2` (extremely outdated)
- These versions don't support Python 3.10+
- Installation fails when trying to resolve dependency chain

**Workaround**:

The updated `download_models.py` now gracefully handles this:

```python
if result.returncode != 0:
    print(f"  ⚠️  Warning: Some dependencies failed to install (this is OK)")
    print(f"      Repo can still be used - some features may be unavailable")
```

The model checkpoints (`.pth` files) will still download and work. You don't need Wav2Lip's Python dependencies if you're using the pre-trained models directly.

**If installation still fails**:
1. Skip the Wav2Lip repo cloning (checkpoints download anyway)
2. Use Wav2Lip runner as-is (it works without full dependency install)
3. Focus on models you do need:
   ```bash
   python scripts/download_models.py --minimal
   ```

---

### ❌ Error: `ModuleNotFoundError: No module named 'coqui_tts'`

**Cause**: TTS package (coqui-tts) not installed or import name mismatch.

**Solution**:
```bash
# Reinstall explicitly
pip uninstall coqui-tts -y
pip install coqui-tts==0.22.0 --no-cache-dir

# Verify
python -c "from TTS.api import TTS; print('OK')"
```

---

### ❌ Error: `ERROR: Could not find a version that satisfies the requirement...` (any package)

**Cause**: Package doesn't exist or network issue.

**Solution**:
```bash
# Check PyPI availability
pip index versions <package_name>

# Retry with longer timeout
pip install --default-timeout=1000 -r requirements.txt

# Or reinstall with cache clearing
pip install --no-cache-dir -r requirements.txt --retries 5
```

---

### ❌ Error: `pip: command not found` or `python: command not found`

**Cause**: Python/pip not in PATH or wrong shell.

**Windows Solution**:
```bash
# Use full path to Python
C:\Users\YourUsername\AppData\Local\Programs\Python\Python310\python.exe -m venv venv
```

**Linux/macOS Solution**:
```bash
# Check if Python installed
which python3
python3 --version

# Use python3 explicitly
python3 -m venv venv
source venv/bin/activate
```

---

### ❌ Error: `CUDA out of memory` during installation

**Cause**: This shouldn't happen during pip install, but if it does:

**Solution**:
- Installation is CPU-only, should use minimal VRAM
- If still failing, your GPU drivers may be interfering
- Disable GPU:
  ```bash
  set CUDA_VISIBLE_DEVICES=-1
  pip install -r requirements.txt
  ```

---

### ⚠️ Warning: `Retrying connection...` many times

**Cause**: Slow internet or PyPI servers are slow.

**Solution**:
```bash
# Use different PyPI mirror
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
# OR
pip install -i https://pypi.org/simple/ -r requirements.txt

# Or just wait - may take 10-30 minutes on slow connections
```

---

## Platform-Specific Setup Issues

### Windows

#### Issue: `The term 'python' is not recognized`

**Solution**:
1. Uninstall Python
2. Reinstall with **"Add Python to PATH"** checked
3. Restart terminal/VS Code
4. Verify: `python --version`

#### Issue: `FFmpeg not found` (even after installation)

**Solution** (already in updated installer):
```bash
# Manually add to PATH if needed
set PATH=C:\Program Files\ffmpeg-8.1.1-essentials_build\bin;%PATH%
```

#### Issue: `Long filenames` causing issues

**Solution**:
```bash
# Enable long filenames support
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1
```

---

### Linux / macOS

#### Issue: `Permission denied: './venv/bin/activate'`

**Solution**:
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

#### Issue: `gcc: command not found`

**Solution** (Ubuntu/Debian):
```bash
sudo apt-get install build-essential python3-dev
pip install -r requirements.txt
```

**Solution** (macOS):
```bash
xcode-select --install
pip install -r requirements.txt
```

#### Issue: `pyaudio` or audio-related package fails

**Solution** (Ubuntu/Debian):
```bash
sudo apt-get install portaudio19-dev
pip install -r requirements.txt
```

**Solution** (macOS):
```bash
brew install portaudio
pip install -r requirements.txt
```

---

## Installation Verification

### Check everything installed correctly

```bash
# Activate environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/macOS

# Test each major package
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python -c "from TTS.api import TTS; print('Coqui TTS: OK')"
python -c "from faster_whisper import WhisperModel; print('Faster-Whisper: OK')"
python -c "import librosa; print(f'LibROSA: {librosa.__version__}')"
python -c "import mediapipe; print('MediaPipe: OK')"
python -c "import insightface; print('InsightFace: OK')"

# Test CUDA (if GPU available)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name() if torch.cuda.is_available() else \"N/A\"}')"
```

**Expected output**:
```
PyTorch: 2.1.0+cu118
OpenCV: 4.8.0
Coqui TTS: OK
Faster-Whisper: OK
LibROSA: 0.10.0
MediaPipe: OK
InsightFace: OK
CUDA available: True
GPU: NVIDIA GeForce RTX 3090
```

---

## Advanced Installation Options

### Minimal Installation (Fast Mode only)

Only install packages needed for Wav2Lip + Piper (smaller, faster):

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install opencv-python Pillow librosa soundfile noisereduce ffmpeg-python tqdm loguru
pip install faster-whisper mediapipe
pip install piper-tts
```

### CPU-Only Installation (No CUDA)

If you don't have NVIDIA GPU:

```bash
# Install CPU-only PyTorch (much smaller)
pip install torch torchvision torchaudio

# Then install rest
pip install -r requirements.txt
```

**Note**: CPU processing is 5-20x slower than GPU.

### Development Installation

For contributing/debugging:

```bash
pip install -e .  # Install in editable mode (if setup.py exists)
pip install -r requirements.txt
pip install pytest pylint black  # Dev tools
```

---

## Getting Help

### Collect diagnostics for troubleshooting

```bash
# Create diagnostics file
python -c "
import sys
import torch
import cv2

print('=== SYSTEM ===')
print(f'Python: {sys.version}')
print(f'Platform: {sys.platform}')

print('\n=== GPU ===')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name()}')
    print(f'CUDA version: {torch.version.cuda}')
    print(f'cuDNN version: {torch.backends.cudnn.version()}')

print('\n=== PACKAGES ===')
import pkg_resources
for package in ['torch', 'torchvision', 'opencv-python', 'librosa', 'soundfile']:
    try:
        version = pkg_resources.get_distribution(package).version
        print(f'{package}: {version}')
    except:
        print(f'{package}: NOT INSTALLED')
" > diagnostics.txt

# Share this file when asking for help
cat diagnostics.txt
```

### Common Log Locations

- Installation log: Check terminal output (save with `script.log` on PowerShell)
- Runtime logs: `logs/pipeline.log`
- Model cache: `models/` directory
- Temporary files: `temp/` directory

---

## Clean Installation (Nuclear Option)

If everything is broken, start fresh:

```bash
# Windows
rmdir venv /s /q
rmdir temp /s /q
del /s /q models\*
git clean -fd  # Remove untracked files

# Linux/macOS
rm -rf venv
rm -rf temp
rm -rf models/*
git clean -fd

# Fresh start
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
scripts\install_windows.bat  # or ./scripts/install_linux.sh
```

---

## Performance Tips

### Reduce Installation Time

```bash
# Use faster index
pip install -i https://pypi.org/simple/ -r requirements.txt

# Parallel downloads (pip 20.3+)
pip install -r requirements.txt --use-deprecated=legacy-resolver

# Skip unused packages
pip install torch torchvision torchaudio opencv-python librosa --no-deps
```

### Reduce Disk Space

```bash
# Clear pip cache after installation
pip cache purge

# Remove test data
find . -name "tests" -type d -exec rm -rf {} +

# Remove model caches
rm -rf ~/.cache/huggingface
```

---

## Compatibility Matrix

| Component | Python 3.9 | Python 3.10 | Python 3.11 | Status |
|-----------|-----------|-----------|-----------|--------|
| PyTorch | ✅ | ✅ | ✅ | Recommended 3.10+ |
| Coqui TTS | ⚠️ | ✅ | ✅ | Use 0.22.0+ |
| MediaPipe | ✅ | ✅ | ✅ | Latest OK |
| NumPy | ⚠️ <1.26 | ✅ ≥1.26 | ✅ | Use ≥1.26 on 3.10+ |
| LibROSA | ✅ | ✅ | ✅ | ≥0.10.0 OK |
| OpenCV | ✅ | ✅ | ✅ | Latest OK |
| FFmpeg | ✅ | ✅ | ✅ | Binary, version independent |

---

## Reporting Issues

When reporting installation issues, include:

1. **OS**: Windows 10/11, Ubuntu 20.04, macOS 12, etc.
2. **Python version**: `python --version`
3. **GPU**: `nvidia-smi` (if applicable)
4. **Full error message**: Copy entire traceback
5. **What you tried**: Steps you took before error occurred
6. **Diagnostics file**: Output from diagnostics script above
7. **Installation log**: Full pip install output

Example:
```
OS: Windows 11
Python: 3.10.8
GPU: RTX 3090 (CUDA 12.1)
Error: [Full traceback here]
Diagnostics: [Output from diagnostics.txt]
```

---

**Last Updated**: May 10, 2026  
**Status**: Actively maintained  
**Support**: Check GitHub issues for similar problems
