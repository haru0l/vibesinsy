# HTS Data Preparation - Implementation Guide

## Overview

The `data_preparation.py` script performs acoustic feature extraction for HTS (HMM-based Text-to-Speech) training. This guide explains the corrected implementation and how to use it.

## Fixed API Issues

### 1. F0 (Fundamental Frequency) Extraction

**Corrected Implementation:**
- Uses `pylstraight.extract_f0()` instead of the non-existent `pysptk.dio()` and `pysptk.stonemask()`
- pylstraight provides superior F0 extraction via the STRAIGHT vocoder

**Key Parameters:**
```python
f0 = pylstraight.extract_f0(
    audio,              # Input audio signal (float64)
    sr,                 # Sampling rate
    frame_shift=ms,     # Frame shift in milliseconds
    f0_range=(lower, upper),  # F0 range in Hz
    f0_format="linear"  # Output format (linear frequency, not log)
)
```

**Processing:**
1. Extract linear F0 values
2. Convert to log F0: `lf0 = log(f0)` for voiced frames, `0` for unvoiced
3. Save as binary float32 files

### 2. MGC (Mel-Generalized Cepstrum) Extraction

**Corrected Implementation:**
- Uses `pysptk.mcep()` for frame-by-frame extraction (NOT the non-existent batch `pysptk.mgcep()`)
- Processes each windowed, padded frame individually

**Processing Pipeline:**
```python
# 1. Frame extraction
frames = pysptk.util.frame_by_frame(audio, framelen, frameshift)

# 2. Apply window (Blackman, Hamming, or Hanning)
windowed = frames * window

# 3. Pad to FFT length
padded = np.pad(windowed, ...)

# 4. Extract MCEP for each frame
for i, frame in enumerate(padded):
    mgc[i, :] = pysptk.mcep(
        frame,
        order=mgcorder,
        alpha=freqwarp,      # Frequency warping (typically 0.545)
        eps=1.0e-8,          # Small constant for numerical stability
        etype=0,             # Energy type
        threshold=0.000001,  # Threshold for convergence
        itype=0              # Input type (time domain)
    )
```

**Parameters:**
- `order`: MGC order (e.g., 24, 25, or 34)
- `alpha`: Frequency warping coefficient (typical: 0.545 for 16kHz)
- `eps`: Regularization epsilon
- `etype`: 0 = use linear prediction coefficients
- `itype`: 0 = time domain input

### 3. BAP (Band Aperiodicity) Extraction

**Corrected Implementation:**
- Uses `pylstraight` for superior aperiodicity analysis
- Two-step process: extract F0, then extract aperiodicity spectrum
- Downsamples full spectrum to BAP order dimensions via linear interpolation

**Processing Pipeline:**
```python
# 1. Extract F0 using pylstraight
f0 = pylstraight.extract_f0(audio, sr, frame_shift=ms, ...)

# 2. Extract aperiodicity spectrum
ap_spectrum = pylstraight.extract_ap(
    audio, sr, f0,
    frame_shift=ms,
    ap_format="a"  # Aperiodicity (0=periodic, 1=aperiodic)
)

# 3. Downsample to BAP order dimensions
# Linear interpolation from full spectrum to baporder+1 coefficients
indices = np.linspace(0, num_freqs - 1, baporder + 1)
for i, idx in enumerate(indices):
    # Interpolate at index
    bap[:, i] = interpolate(ap_spectrum[:, idx])
```

## Installation

### Required Dependencies

```bash
# Core dependencies
pip install numpy scipy

# Speech signal processing
pip install pysptk

# Superior vocoder features (optional but recommended)
pip install pylstraight
```

### System Dependencies (Ubuntu/Debian)
```bash
sudo apt-get install libfftpack0 libfftpack-dev
```

## Data Formats

### Output Binary Files

All features are saved as **binary float32 files** (big-endian by default):

#### F0 File (.lf0)
- Shape: `(n_frames,)` 
- Values: log(f0) for voiced frames, 0 for unvoiced
- Size: `n_frames * 4` bytes

#### MGC File (.mgc)
- Shape: `(n_frames, mgcorder + 1)`
- Size: `n_frames * (mgcorder + 1) * 4` bytes
- Includes c0 (log energy) and cepstral coefficients

#### BAP File (.bap) - Optional
- Shape: `(n_frames, baporder + 1)`
- Size: `n_frames * (baporder + 1) * 4` bytes

#### Composite File (.cmp)
- Concatenated features: `[MGC | LF0 | BAP]` (optional)
- Size: `n_frames * (mgcorder + baporder + 3) * 4` bytes

### HTK Format with Header

When using `_write_htk_file()`, files include HTK header:
```
HTK Header (12 bytes):
  - nSamples (4 bytes, big-endian int32)
  - samplePeriod (4 bytes, big-endian int32, in 100ns units)
  - sampSize (2 bytes, big-endian int16)
  - parmKind (2 bytes, big-endian int16, 9 = USER)
+ Data (float32 samples)
```

## Configuration Parameters

Key configuration from `Config.pm.in`:

```python
# Sampling and frame settings
sampfreq = 16000        # Sampling frequency (Hz)
framelen = 1024         # Frame length (samples)
frameshift = 80         # Frame shift (samples)
fftlen = 2048          # FFT length (samples)

# Feature dimensions
mgcorder = 24          # MGC order (24=25 dims with c0)
baporder = 1           # BAP order
lowerf0 = 50           # Lower F0 bound (Hz)
upperf0 = 400          # Upper F0 bound (Hz)

# Spectral parameters
freqwarp = 0.545       # Frequency warping (α)
gamma = 0              # MGC gamma parameter
windowtype = 2         # 0=Blackman, 1=Hamming, 2=Hanning

# Features to extract
usestraight = 1        # Use STRAIGHT vocoder for BAP
```

## Usage

### Basic Feature Extraction

```python
from data_preparation import DataPreparation, Config

# Initialize configuration
config = Config(
    dataset="nitech_jp_song070",
    speaker="f001",
    sampfreq=16000,
    framelen=1024,
    frameshift=80,
    fftlen=2048,
    mgcorder=24,
    # ... other params
)

# Create processor
processor = DataPreparation(config)

# Create directories
processor.create_directories()

# Extract features
processor.extract_features()

# Compose training data
processor.compose_training_data()

# Generate labels and lists
processor.generate_label_files()
processor.generate_model_lists()
```

### Command Line Usage

```bash
python3 data_preparation.py \
    --dataset nitech_jp_song070 \
    --speaker f001 \
    --sampfreq 16000 \
    --mgcorder 24
```

## Troubleshooting

### Error: "pysptk.mcep() not available"
- Make sure pysptk is installed: `pip install pysptk`
- Verify installation: `python -c "import pysptk; print(pysptk.mcep)"`

### Error: "pylstraight not available"
- Optional for BAP extraction; F0 and MGC will still work
- Install if needed: `pip install pylstraight`

### Dimension Mismatch Between Features
- Ensure all frames are processed with same parameters
- Check that audio file is valid and non-corrupt
- Verify frame length divisibility: `len(audio) % frameshift`

### Poor Feature Quality
- Adjust F0 range (`lowerf0`, `upperf0`) for your data
- Try different frequency warping (`freqwarp`): 0.545 for 16kHz, 0.580 for 22.05kHz
- Check window type (Hanning is typical default)

## References

### Papers
- Tokuda, K., Masuko, T., Yamada, T., et al. (2002). "Speech synthesis based on hidden Markov models." Proceedings of IEEE.
- Kawahara, H., Masuda-Katsuse, I., & de Cheveigné, A. (1999). "Restructuring speech representations using a pitch-adaptive time-frequency envelope extractor." Speech Communication.

### Data Files Generated
- mgc/: Mel-generalized cepstral coefficients
- lf0/: Log fundamental frequency
- bap/: Band aperiodicity (if using STRAIGHT)
- cmp/: Composite features
- labels/: Label files (mono, full, gen)
- lists/: Model and file lists

