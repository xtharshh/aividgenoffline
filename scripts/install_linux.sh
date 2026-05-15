#!/bin/bash
set -e

echo "============================================================"
echo "  Offline AI Avatar Video Generator - Linux Setup"
echo "============================================================"
echo ""

# Check dependencies
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] Python3 not found. Install: sudo apt install python3.10"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "[ERROR] Git not found. Install: sudo apt install git"; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || { echo "[ERROR] FFmpeg not found. Install: sudo apt install ffmpeg"; exit 1; }

echo "[OK] Python: $(python3 --version)"
echo "[OK] Git: $(git --version)"
echo "[OK] FFmpeg: $(ffmpeg -version 2>&1 | head -1)"

# System deps
echo ""
echo "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-venv python3-pip \
    libgl1-mesa-glx libglib2.0-0 \
    libsm6 libxext6 libxrender-dev \
    cmake build-essential

# Create venv
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# PyTorch with CUDA (change cu118 to cu121 for CUDA 12.1+)
echo ""
echo "Installing PyTorch with CUDA..."
pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu118 \
    --quiet

# Requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Create directories
mkdir -p output temp projects models repos logs

# Download minimal models
echo ""
echo "Downloading minimal model checkpoints (~560 MB)..."
python scripts/download_models.py --minimal

echo ""
echo "============================================================"
echo "  Setup complete!"
echo ""
echo "  Usage:"
echo "    source venv/bin/activate"
echo "    python generate.py --script script.txt --avatar avatar.jpg --output out.mp4"
echo ""
echo "  For full quality (downloads ~2 GB more):"
echo "    python scripts/download_models.py --full"
echo "============================================================"
