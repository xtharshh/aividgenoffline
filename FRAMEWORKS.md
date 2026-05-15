# Framework & Technology Definitions

Complete reference guide for all frameworks, libraries, and technologies used in the Offline AI Avatar Video Generator.

---

## 🧠 Deep Learning & AI Frameworks

### PyTorch
**What it is**: Open-source machine learning framework built on Python and C++.

**Purpose**: Core framework for running AI models (talking head, TTS, face detection, etc.)

**In this project**:
- Loads and runs pre-trained neural network models
- Handles GPU acceleration via CUDA
- Manages tensor operations and model inference
- Memory management for video processing pipelines

**Key components**:
- `torch.cuda`: GPU device management
- `torch.nn`: Neural network modules
- Model loading and inference

**Example usage**:
```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
model = load_model().to(device)
output = model(input_tensor)
```

**Dependency chains**: 
- Base for all deep learning in project
- Required by: TTS, Face-Alignment, MediaPipe, InsightFace

---

### TorchVision
**What it is**: PyTorch library for computer vision tasks.

**Purpose**: Pre-trained image models and computer vision utilities.

**In this project**:
- Image preprocessing and normalization
- Model utilities for visual processing
- Tensor transformations for avatar images

**Key components**:
- `torchvision.transforms`: Image preprocessing
- `torchvision.models`: Pre-trained visual models

---

### TorchAudio
**What it is**: PyTorch library for audio and speech processing.

**Purpose**: Audio processing utilities and operations.

**In this project**:
- Audio loading and resampling
- Spectral transformations
- Audio feature extraction
- MFCC (Mel-Frequency Cepstral Coefficients) computation for audio analysis

**Key components**:
- Audio I/O operations
- Resampling and feature extraction
- Audio augmentation utilities

---

## 🎤 Text-to-Speech (TTS) Engines

### Coqui TTS (XTTS-v2)
**What it is**: Open-source, multilingual text-to-speech engine with voice cloning capability.

**Install**: `pip install TTS`

**Purpose**: High-quality speech synthesis with voice cloning.

**In this project**:
- Generates natural-sounding speech from script text
- Supports voice cloning (speaker adaptation from reference audio)
- Multilingual support (13+ languages)
- Used in "balanced" and "quality" modes

**Key features**:
- Zero-shot voice cloning (only needs 3-10s reference audio)
- Emotional control
- Fine control over speaking rate and pitch
- Model size: ~1.8 GB (downloads automatically)

**How it works**:
```
Text → XTTS-v2 Model → Mel-Spectrogram → Vocoder → Speech Audio (WAV)
                ↑ (optional reference audio for cloning)
```

**Supported languages**: EN, ES, FR, DE, IT, PT, PL, TR, RU, NL, CZ, AR, ZH, JA, HU, KO, HI

**Code example**:
```python
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
tts.tts_to_file(text="Hello world", speaker_wav="reference.wav", 
                language="en", file_path="output.wav")
```

---

### Piper TTS
**What it is**: Fast, lightweight, on-device text-to-speech engine.

**Install**: `pip install piper-tts`

**Purpose**: Quick, resource-efficient speech synthesis.

**In this project**:
- Used in "fast" mode for speed-optimized workflows
- Lower quality than XTTS but processes 3-5x faster
- Minimal dependencies
- Works on systems with limited VRAM

**Key features**:
- No voice cloning (fixed voices per language)
- Very fast inference (~0.5-1s per sentence)
- Small model size (~100 MB per language)
- CPU-capable

**Supported languages**: 13+ including EN, ES, FR, DE, JA, ZH

**Code example**:
```python
from piper.voice import PiperVoice
voice = PiperVoice.load("en_US-arctic-medium")
audio = voice.synthesize("Hello world", speaker=0)
```

---

## 🎭 Talking Head & Animation Models

### SadTalker
**What it is**: Advanced facial animation model that creates talking head videos with natural expressions and emotions.

**Repository**: https://github.com/OpenTalker/SadTalker

**Purpose**: Generate expressive talking head animations from still avatar images.

**In this project**:
- Creates realistic facial movements (eyes, eyebrows, jaw, head pose)
- Synchronizes with speech audio
- Captures emotional expressions from audio
- Used in "balanced" and "quality" modes

**Key features**:
- Works from any face image (no special training needed)
- Generates head movements, eye gaze, facial expressions
- Handles occlusions and partial faces
- Model size: ~1.5 GB
- VRAM requirement: 8+ GB

**How it works**:
```
Avatar Image + Audio → SadTalker Model → Facial Parameters → 
Facial Mesh → 3D Rendering → Video Frames
```

**Key models used**:
- Face detection & alignment
- 3D face reconstruction
- Motion predictor (from audio)
- Renderer

---

### Wav2Lip
**What it is**: Real-time lip-sync animation model that generates accurate mouth movements.

**Repository**: https://github.com/Rudrabha/Wav2Lip

**Purpose**: Precise lip-synchronization between audio and avatar mouth.

**In this project**:
- Primary talking head in "fast" mode
- Refinement pass in "balanced"/"quality" modes
- Most accurate lip-sync available
- Works with limited VRAM (4+ GB)

**Key features**:
- Photorealistic lip animations
- Speaker-independent (works with any face)
- Fast inference (~0.1s per frame)
- Trained on faces from all ethnicities

**How it works**:
```
Avatar Image + Audio Mel-Spectrogram → Wav2Lip GAN → Mouth Region → 
Avatar Composition → Video Frames
```

**Model components**:
- Discriminator: Validates realistic lip movement
- Generator: Creates face frames with synchronized mouths
- Face detector: SFD (Single Shot MultiBox Detector)

---

## 🎤 Speech Recognition & Transcription

### Faster-Whisper
**What it is**: Optimized implementation of OpenAI's Whisper speech-to-text model.

**Install**: `pip install faster-whisper`

**Purpose**: Convert speech audio to text with high accuracy.

**In this project**:
- Automatically generates subtitles from synthesized speech
- Transcribes audio for SRT (subtitle) file creation
- Language auto-detection
- More efficient than original Whisper (CTransformers backend)

**Key features**:
- 99%+ accuracy in quiet environments
- Multilingual (99 languages)
- Handles accents, background noise
- 2-4x faster than original Whisper
- Model size: ~140 MB (base model)

**Model sizes**:
- Tiny: 39 MB (fast, less accurate)
- Base: 140 MB (good balance)
- Small: 466 MB (better accuracy)
- Medium: 1.5 GB (high accuracy)
- Large: 3.1 GB (highest accuracy)

**Code example**:
```python
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cuda")
segments, info = model.transcribe("audio.wav")
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

---

## 👁️ Face Detection & Analysis

### MediaPipe
**What it is**: Google's framework for building multimodal ML pipelines.

**Install**: `pip install mediapipe`

**Purpose**: Detect and track facial landmarks (eyes, nose, mouth, etc.)

**In this project**:
- Facial landmark detection for avatar alignment
- Face bounding box detection
- Head pose estimation
- Eye & gaze tracking
- Used to ensure avatar is properly centered

**Key modules**:
- `MediaPipe Face Detection`: Fast face detection
- `MediaPipe Face Mesh`: 468 facial landmarks
- `MediaPipe Pose`: Body pose (not used here but available)

**Performance**:
- ~100 FPS on GPU
- Works on CPU (slower but possible)
- Lightweight models (~5 MB)

---

### Face-Alignment
**What it is**: Library for detecting and aligning facial landmarks.

**Install**: `pip install face-alignment`

**Purpose**: Precise facial feature localization and face alignment.

**In this project**:
- Detects 2D/3D facial landmarks
- Aligns faces for consistent processing
- Face angle/rotation correction
- Enables proper face reconstruction

**Key features**:
- 468-point facial mesh (3D)
- Works with PyTorch/TensorFlow backends
- Handles profile/angled faces
- Model size: ~60 MB

---

### InsightFace
**What it is**: Open-source face recognition and analysis framework.

**Install**: `pip install insightface`

**Purpose**: Advanced face detection, recognition, and manipulation.

**In this project**:
- Face detection with high accuracy
- Face alignment for preprocessing
- Face quality assessment
- Enables robust avatar face detection

**Key features**:
- Multiple detection backends (RetinaFace, CenterFace)
- High accuracy on diverse face types
- Fast inference
- Handles faces at various angles and scales

**Code example**:
```python
import insightface
app = insightface.app.FaceAnalysis()
app.prepare(ctx_id=0, det_size=(640, 640))
faces = app.get(image)
```

---

## 🎨 Image Processing

### OpenCV (cv2)
**What it is**: Industry-standard computer vision library.

**Install**: `pip install opencv-python`

**Purpose**: Image and video processing operations.

**In this project**:
- Video reading and writing
- Image resizing and transformations
- Color space conversions (RGB, HSV, YUV)
- Image filtering and enhancement
- Face detection and ROI extraction
- Video frame composition

**Key modules used**:
- `cv2.VideoCapture`: Read video frames
- `cv2.VideoWriter`: Write output videos
- `cv2.resize`: Image scaling
- `cv2.cvtColor`: Color conversion
- `cv2.rectangle`, `cv2.putText`: Drawing operations
- `cv2.bilateralFilter`: Noise reduction

**Code example**:
```python
import cv2
video = cv2.VideoCapture("input.mp4")
while True:
    ret, frame = video.read()
    if not ret: break
    # Process frame
    frame = cv2.resize(frame, (1920, 1080))
```

---

### Pillow (PIL)
**What it is**: Python Imaging Library for image processing.

**Install**: `pip install Pillow`

**Purpose**: Image file I/O and manipulation.

**In this project**:
- Load avatar images (JPG, PNG)
- Image resizing and cropping
- Format conversions
- Image quality adjustments
- Thumbnail generation

**Key modules used**:
- `PIL.Image`: Load, save, manipulate images
- `PIL.ImageOps`: Image operations
- `PIL.ImageDraw`: Drawing on images

**Code example**:
```python
from PIL import Image
img = Image.open("avatar.jpg")
img = img.resize((512, 512))
img.save("avatar_resized.jpg")
```

---

## 🔊 Audio Processing

### Librosa
**What it is**: Python library for audio analysis and music information retrieval.

**Install**: `pip install librosa`

**Purpose**: Audio loading, feature extraction, and analysis.

**In this project**:
- Load and parse audio files
- Compute spectrograms (time-frequency representation)
- Extract audio features (MFCCs, Chroma, Tempogram)
- Audio duration calculation
- Resampling to standard rates
- Energy and loudness analysis

**Key features**:
- Handles multiple audio formats
- Mel-spectrogram generation (input for many ML models)
- Time-stretching and pitch-shifting
- Beat tracking and onset detection

**Code example**:
```python
import librosa
y, sr = librosa.load("audio.wav")  # Load audio at sampling rate
S = librosa.feature.melspectrogram(y=y, sr=sr)  # Mel-spectrogram
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # MFCCs
```

---

### SoundFile
**What it is**: Library for reading/writing audio files (WAV, FLAC, OGG).

**Install**: `pip install soundfile`

**Purpose**: Lossless audio I/O operations.

**In this project**:
- Read voice reference samples (WAV)
- Write synthesized audio outputs
- Preserve audio quality (no compression)
- Handle various sample rates and bit depths

**Code example**:
```python
import soundfile as sf
data, samplerate = sf.read("audio.wav")
sf.write("output.wav", data, samplerate)
```

---

### Noisereduce
**What it is**: Library for noise reduction in audio signals.

**Install**: `pip install noisereduce`

**Purpose**: Clean up audio by reducing background noise.

**In this project**:
- Reduce background noise from synthesized speech
- Improve audio quality for lip-sync models
- Normalize audio levels
- Enhance clarity for subtitle generation

**How it works**:
```
Audio Input → Noise Profile Analysis → Spectral Subtraction → Clean Audio
```

**Code example**:
```python
import noisereduce as nr
import librosa
y, sr = librosa.load("noisy.wav")
reduced = nr.reduce_noise(y=y, sr=sr)
```

---

## 🎥 Video Processing

### FFmpeg
**What it is**: Comprehensive multimedia framework and command-line tool.

**Install**: Download binary from https://www.gyan.dev/ffmpeg/builds/

**Purpose**: Video encoding, decoding, and format conversion.

**In this project**:
- Combine audio and video streams
- Encode final video output
- Handle audio-video synchronization
- Apply filters and effects
- Support multiple codec formats (H.264, H.265, VP9)
- Video composition (overlays, scaling)

**Key components**:
- `ffmpeg`: Main binary for video encoding
- `ffprobe`: Analyze media files
- Used via Python wrapper (`ffmpeg-python`)

**Common operations**:
- Merge video + audio: `ffmpeg -i video.mp4 -i audio.wav -c:v copy output.mp4`
- Encode with codec: `ffmpeg -i input.mp4 -vcodec libx264 output.mp4`
- Create PiP overlay: `ffmpeg -i main.mp4 -i overlay.mp4 [complex filter] output.mp4`

---

### ffmpeg-python
**What it is**: Python wrapper for FFmpeg command-line tool.

**Install**: `pip install ffmpeg-python`

**Purpose**: Programmatic video manipulation from Python.

**In this project**:
- Final video assembly (audio + video merging)
- Video format conversion
- Resolution scaling
- Frame extraction
- Video metadata handling

**Code example**:
```python
import ffmpeg
(
    ffmpeg
    .input("video.mp4")
    .input("audio.wav")
    .output("final.mp4", vcodec="libx264", acodec="aac")
    .run()
)
```

---

## 🔢 Numerical & Scientific Computing

### NumPy
**What it is**: Fundamental package for numerical computing in Python.

**Install**: `pip install numpy` (usually pre-installed)

**Purpose**: Array/matrix operations and numerical computations.

**In this project**:
- Tensor/array manipulations
- Audio signal processing (arrays of samples)
- Mathematical operations on images/audio
- Batch processing
- Shape transformations

**Key operations**:
```python
import numpy as np
audio = np.array([...])  # Audio samples
frame = np.zeros((1080, 1920, 3))  # Black frame
concatenated = np.concatenate([arr1, arr2])  # Merge arrays
```

---

### SciPy
**What it is**: Scientific computing library building on NumPy.

**Install**: `pip install scipy`

**Purpose**: Advanced mathematical and scientific computations.

**In this project**:
- Signal processing (filters, convolution)
- Image processing (interpolation, morphological operations)
- Audio resampling
- Statistical operations
- Optimization for parameter tuning

**Key modules used**:
- `scipy.signal`: Audio filtering
- `scipy.interpolate`: Smooth animation curves
- `scipy.ndimage`: Image filtering

---

## 🤖 Model Management

### HuggingFace Hub
**What it is**: Repository and Python library for sharing ML models.

**Install**: `pip install huggingface-hub`

**Purpose**: Download and cache pre-trained models.

**In this project**:
- Download model checkpoints from HuggingFace Model Hub
- Automatic caching (avoid re-downloading)
- Version management
- Access control for models

**Code example**:
```python
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(
    repo_id="username/model-name",
    filename="model.pth",
    cache_dir="models/"
)
```

---

### SafeTensors
**What it is**: Safe and efficient format for storing tensors.

**Install**: `pip install safetensors`

**Purpose**: Load pre-trained model weights safely and efficiently.

**In this project**:
- Load model checkpoints in SafeTensors format
- Faster loading than pickle format
- Safe deserialization (prevents code execution attacks)
- Better memory efficiency

**Code example**:
```python
from safetensors.torch import load_file
state_dict = load_file("model.safetensors")
model.load_state_dict(state_dict)
```

---

## 📊 Progress & Logging

### tqdm
**What it is**: Progress bar library for loops and iterables.

**Install**: `pip install tqdm`

**Purpose**: Visual progress indication during processing.

**In this project**:
- Progress bars for:
  - Model downloads
  - Frame processing
  - Video encoding
  - Audio analysis
- Estimated time remaining
- Processing speed display

**Code example**:
```python
from tqdm import tqdm
for i in tqdm(range(1000)):
    process(i)
    # Output: 50%|█████ | 500/1000 [00:30<00:30, 15.00 it/s]
```

---

### Loguru
**What it is**: Modern logging library for Python.

**Install**: `pip install loguru`

**Purpose**: Structured, colored logging with file output.

**In this project**:
- Detailed logging of pipeline stages
- Debug information for troubleshooting
- File rotation for long-running processes
- Color-coded log levels (INFO, WARNING, ERROR)
- Log file storage in `logs/pipeline.log`

**Code example**:
```python
from loguru import logger
logger.info("Starting pipeline")
logger.warning("Low VRAM detected")
logger.error("Model load failed")
```

---

## 🌐 HTTP & Requests

### Requests
**What it is**: HTTP library for Python.

**Install**: `pip install requests`

**Purpose**: Download files and make HTTP requests.

**In this project**:
- Download model checkpoints from remote servers
- Check internet connectivity
- Fetch model metadata
- Resume interrupted downloads

**Code example**:
```python
import requests
response = requests.get("https://example.com/model.pth", stream=True)
with open("model.pth", "wb") as f:
    for chunk in response.iter_content():
        f.write(chunk)
```

---

## 🗄️ Database & State Management

### SQLite3
**What it is**: Lightweight, file-based SQL database (built into Python).

**Purpose**: Store pipeline state for resume capability.

**In this project**:
- Track completed processing stages
- Store intermediate results
- Enable checkpoint recovery
- Store project metadata

**Database location**: `projects/{project_name}.db`

**Stored data**:
- Stage completion status (TTS done, lip-sync done, etc.)
- Timestamp of each stage
- Output file paths
- Configuration snapshots

**Code example**:
```python
import sqlite3
conn = sqlite3.connect("project.db")
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO stages (name, status) VALUES (?, ?)",
    ("tts", "completed")
)
conn.commit()
```

---

## 🛠️ Development & System Utilities

### Git
**What it is**: Version control system for source code management.

**Purpose**: Clone external repositories (Wav2Lip, SadTalker).

**In this project**:
- Clone SadTalker repo: `git clone https://github.com/OpenTalker/SadTalker repos/SadTalker`
- Clone Wav2Lip repo: `git clone https://github.com/Rudrabha/Wav2Lip repos/Wav2Lip`
- Access to latest model versions

---

## 📋 Summary Table

| Category | Framework | Purpose | Key Use |
|----------|-----------|---------|---------|
| **Deep Learning** | PyTorch | AI model inference & training | Core ML operations |
| | TorchVision | Computer vision | Image models |
| | TorchAudio | Audio processing | Spectral features |
| **TTS** | Coqui XTTS-v2 | High-quality speech synthesis | Balanced/Quality modes |
| | Piper TTS | Fast speech synthesis | Fast mode |
| **Animation** | SadTalker | Expressive talking head | Balanced/Quality modes |
| | Wav2Lip | Lip-sync animation | Fast mode, refinement |
| **Speech-to-Text** | Faster-Whisper | Audio transcription | Subtitle generation |
| **Face Detection** | MediaPipe | Facial landmark detection | Face alignment |
| | Face-Alignment | Precise landmark localization | 3D face mesh |
| | InsightFace | Advanced face detection | Robust detection |
| **Image Processing** | OpenCV | Video/image operations | Frame processing |
| | Pillow | Image file I/O | Avatar loading |
| **Audio Processing** | Librosa | Audio analysis | Spectrogram extraction |
| | SoundFile | Audio file I/O | WAV read/write |
| | Noisereduce | Audio noise reduction | Quality enhancement |
| **Video Processing** | FFmpeg | Video encoding/muxing | Final assembly |
| | ffmpeg-python | FFmpeg Python wrapper | Programmatic encoding |
| **Numerical** | NumPy | Array operations | Data manipulation |
| | SciPy | Scientific computing | Signal processing |
| **Model Management** | HuggingFace Hub | Model repository | Model downloading |
| | SafeTensors | Secure tensor format | Safe model loading |
| **Utilities** | tqdm | Progress bars | Visual feedback |
| | Loguru | Advanced logging | Debugging/logging |
| | Requests | HTTP requests | File downloading |
| | SQLite3 | Database | State persistence |

---

## 🔄 Framework Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT FILES                                │
│         (Script, Avatar Image, Voice Sample)                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 1: TEXT PROCESSING                           │
│  Pillow (load avatar) → input validation                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 2: TTS SYNTHESIS                             │
│  Coqui XTTS-v2 OR Piper → Audio Generation                     │
│  LibROSA (spectral analysis) → Audio features                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│          STAGE 3: AUDIO POST-PROCESSING                         │
│  Noisereduce → Clean audio                                      │
│  SoundFile → Save WAV                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│           STAGE 4: SUBTITLE GENERATION                          │
│  Faster-Whisper → Transcribe audio → Generate SRT              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 5: FACE DETECTION & ALIGNMENT                     │
│  MediaPipe → Face landmark detection                            │
│  InsightFace/Face-Alignment → Facial mesh extraction            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│        STAGE 6: TALKING HEAD ANIMATION                          │
│  SadTalker OR Wav2Lip → Generate video frames                   │
│  (PyTorch running on CUDA GPU)                                   │
│  LibROSA → Extract audio features for animation                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 7: VIDEO COMPOSITION                              │
│  OpenCV → Frame composition, overlays                           │
│  FFmpeg-python → Audio/video muxing                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│            STAGE 8: FINAL ENCODING                              │
│  FFmpeg → H.264 encoding, optimization                          │
│  Requests/HuggingFace → Upload if needed                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT FILES                                 │
│         (MP4 Video + SRT Subtitles)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Framework Dependencies & Compatibility

**Dependency hierarchy**:

```
PyTorch (GPU-accelerated compute)
├── TorchVision (image models)
├── TorchAudio (audio models)
├── Coqui TTS (text-to-speech)
├── Face-Alignment (facial landmarks)
├── MediaPipe (face detection)
├── InsightFace (face analysis)
└── SadTalker (talking head animation)

LibROSA (audio analysis)
├── NumPy (array ops)
├── SciPy (signal processing)
└── Librosa → Wav2Lip (lip-sync model)

FFmpeg (video encoding)
└── ffmpeg-python (Python wrapper)
    └── OpenCV (frame composition)

Model Ecosystem
├── HuggingFace Hub (model downloads)
├── SafeTensors (model loading)
└── Requests (HTTP downloads)

Utilities
├── SQLite3 (state persistence)
├── Loguru (logging)
├── tqdm (progress indication)
└── Pillow (image I/O)
```

---

## ⚙️ Version Compatibility

| Framework | Minimum Version | Recommended | Notes |
|-----------|-----------------|-------------|-------|
| PyTorch | 2.0 | 2.1+ | CUDA 11.8+ for GPU |
| TorchVision | 0.15 | 0.16+ | Paired with PyTorch |
| TorchAudio | 2.0 | 2.1+ | Paired with PyTorch |
| TTS (Coqui) | 0.20 | 0.22+ | Model auto-downloads |
| Piper TTS | 1.0 | 1.2+ | Lightweight alternative |
| Faster-Whisper | 0.10 | 1.0+ | CTransformers backend |
| OpenCV | 4.5 | 4.8+ | Video codec support |
| Pillow | 9.0 | 10.0+ | Format support |
| LibROSA | 0.9 | 0.10+ | Audio features |
| FFmpeg | 4.2 | 5.1+ | Codec availability |
| NumPy | 1.20 | 1.24+ | Array operations |
| SciPy | 1.7 | 1.11+ | Signal processing |

---

**Last Updated**: May 10, 2026  
**Framework Count**: 24+ technologies integrated  
**Status**: Comprehensive reference document
