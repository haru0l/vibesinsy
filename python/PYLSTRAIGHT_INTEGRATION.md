# pylstraight Integration Guide

## Overview

**pylstraight** provides the STRAIGHT (Speech Transformation and Representation Using Spectral Extrapolation) vocoder algorithm in Python. This enables high-quality **Band Aperiodicity (BAP)** feature extraction for HTS speech synthesis models.

## What is STRAIGHT?

STRAIGHT is a high-quality vocoder that decomposes speech into:
- **Fundamental Frequency (F0)** - Pitch information
- **Spectral Information** - Magnitude spectrum
- **Aperiodic Component** - Voice/voicing level (band aperiodicity)

The aperiodic component (BAP) represents:
- Voicing decisions per frequency band
- Degree of aperiodicity (noise-like components)
- Natural/unnatural speech characteristics

## Why BAP Matters

### Without BAP (MGC + F0 only)
- Synthetic speech sounds somewhat robotic
- Voicing artifacts (e.g., semi-voiced consonants)
- Sometimes noisy or whispered sections
- Shimmer artifacts in quiet voiced regions

### With BAP (MGC + F0 + BAP)
- ✓ More natural speech quality
- ✓ Better representation of voicing/unvoicing
- ✓ Natural-sounding fricatives and affricates
- ✓ Reduced artifacts in challenging regions
- ✓ Better synthesis of emotional/expressive speech

## Installation

### Option 1: From PyPI (Recommended)
```bash
pip install pylstraight
```

### Option 2: From Source
```bash
git clone https://github.com/r9y9/pylstraight.git
cd pylstraight
python setup.py install
```

### Verify Installation
```bash
python3 -c "import pylstraight; print(pylstraight.__version__)"
```

Or use the dependency checker:
```bash
python3 scripts/check_dependencies.py
```

## Feature Extraction with pylstraight

### Primary STRAIGHT-based BAP Extraction

When pylstraight is available, `data_preparation.py` uses STRAIGHT for BAP extraction:

```python
# Load audio
from scipy.io import wavfile
import pylstraight

sr, audio = wavfile.read('audio.wav')
audio = audio.astype(np.float64) / 32768.0

# Extract using STRAIGHT
frame_period = 5.0  # ms (typical 5ms shift for 80 samples at 16kHz)
spectrum = pylstraight.extract(audio, sr, frame_period=frame_period)

# Get aperiodicity spectrum
ap_spectrum = spectrum.ap  # Shape: (num_frames, num_bins)

# Downsample to BAP order (e.g., 5-6 dimensions)
bap = downsample_aperiodicity(ap_spectrum, bap_order=5)
```

### Fallback Spectral Estimation

If pylstraight is not available, BAP is extracted using pysptk:

```python
# Fallback: spectral-based BAP
bap = pysptk.mgcep(frames, order=5, gamma=-1.0, alpha=0.42)
```

This is less accurate but still functional.

## Configuration

### Enable/Disable BAP Extraction

In `data_preparation.py`:

```python
# Enable BAP extraction (uses STRAIGHT if available)
python3 data_preparation.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --usestraight 1  # or any non-zero value

# Disable BAP extraction
python3 data_preparation.py \
  --dataset my_corpus \
  --speaker speaker01
  # --usestraight 0 (default)
```

### BAP Parameters

```bash
python3 data_preparation.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --usestraight 1 \
  --baporder 5  # BAP output dimension - 1
```

**Typical values:**
- `--baporder 5` - 6-dimensional BAP features (4-10 kHz bands)
- `--baporder 3` - 4-dimensional BAP features (lower resolution)
- `--baporder 7` - 8-dimensional BAP features (higher resolution)

## Feature Dimensions

### With BAP (STRAIGHT)

Total CMP (Composite) Dimension Example:
```
MGC:   26D  (order 25 + c0)
LF0:    1D  (log F0)
BAP:    6D  (order 5 + power/const)
────────────
TOTAL:  33D per frame
```

Used in HMM training as:
```
[Frame 0: 33D feature vector]
[Frame 1: 33D feature vector]
...
```

### Without BAP (Spectral or pysptk)

Total CMP Dimension:
```
MGC:   26D  (order 25 + c0)
LF0:    1D  (log F0)
────────────
TOTAL:  27D per frame
```

## Quality Comparison

### Synthesis Quality Ranking

1. **High Quality** - MGC + F0 + BAP (STRAIGHT)
   - Uses pylstraight for accurate aperiodicity estimation
   - Best natural speech quality
   - Handles complex phonemes well

2. **Good Quality** - MGC + F0 + BAP (pysptk spectral)
   - Fallback estimation when pylstraight not available
   - Still good results for most cases
   - Some artifacts in voicing transitions

3. **Acceptable Quality** - MGC + F0 only
   - Without aperiodicity modeling
   - Synthetic-sounding for some speakers
   - Common approach when BAP extraction unavailable

## Complete Workflow

### 1. Install Dependencies

```bash
# Required
pip install pysptk scipy numpy

# Recommended (for superior quality)
pip install pylstraight
```

### 2. Verify Setup

```bash
python3 scripts/check_dependencies.py
```

Expected output:
```
✓ Python 3.X.X
✓ numpy
✓ scipy
✓ pysptk
✓ pylstraight    # Optional but present
```

### 3. Extract Features with BAP

```bash
python3 scripts/data_preparation.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --usestraight 1 \
  --baporder 5
```

### 4. Prepare for Training

Generated files:
```
data/
  mgc/          # Mel-cepstral coefficients
  lf0/          # Log F0
  bap/          # Band aperiodicity (STRAIGHT-based)
  cmp/          # Composite features (MGC + LF0 + BAP = 33D)
  labels/       # Phone labels
  lists/        # Model lists
  scp/          # Training scripts
```

### 5. Train Models

```bash
# Update config.pm with feature dimensions
# CMP dimension: mgcorder + 1 + 1 + baporder + 1 = 25+1+1+5+1 = 33

python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --build-models

python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --train \
  --iterations 5
```

### 6. Synthesize

```bash
python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --synthesize
```

## Troubleshooting

### Issue: pylstraight Not Installed

```
pylstraight not available. BAP extraction disabled.
```

**Solution:**
```bash
pip install pylstraight
```

Or proceed without BAP (uses pysptk spectral fallback).

### Issue: STRAIGHT Extraction Fails

```
STRAIGHT extraction fallback to spectral estimate
```

**What happened:**
- pylstraight.extract() returned None or invalid
- System falls back to pysptk-based BAP estimation

**Check:**
- Audio file format (should be WAV or RAW)
- Sample rate (verify with --sampfreq)
- Audio quality (very noisy audio may have issues)

### Issue: Training Fails with BAP

**Error:** Feature dimension mismatch in training

**Solution:** Update configuration to match CMP dimension:
```python
# If using: MGC order 25, BAP order 5
# CMP dimension = 26 + 1 + 6 = 33

'num_streams': 3,
'stream_size': [26, 1, 6],  # MGC, LF0, BAP
'cmp_dim': 33,
```

### Issue: No Improvement in Synthesis Quality

**Possible causes:**
- BAP dimensions too small (try `--baporder 7`)
- Low-quality training data
- Insufficient model training iterations
- Model averaging needed for multiple speakers

**Solutions:**
- Increase BAP order for finer aperiodicity modeling
- Ensure training data is high quality
- Train with more iterations
- Use speaker adaptation if models are speaker-specific

## Advanced Topics

### STRAIGHT Parameter Tuning

STRAIGHT uses several parameters for analysis:

```python
# Frame period (default: 5ms for 16kHz)
frame_period = 5.0

# F0 extraction parameters (typically automatic)
F0_threshold = 0.1  # 0-1 range

# Spectrum analysis parameters
fft_size = 512
```

Most parameters are automatic with pylstraight; default settings work well for typical speech.

### Batch Processing

For large datasets, process in batches:

```bash
# Process multiple speakers in parallel
for speaker in speaker01 speaker02 speaker03; do
  python3 data_preparation.py \
    --dataset my_corpus \
    --speaker $speaker \
    --usestraight 1 &
done
wait
```

### Quality Analysis

Compare synthesis with/without BAP:

```bash
# Train model without BAP
python3 data_preparation.py --dataset test --speaker sp01
# (BAP not enabled by default)

# Train model with BAP
python3 data_preparation.py --dataset test --speaker sp01 --usestraight 1

# Compare synthesized quality subjectively
# Or compute MCD/F0RMSE metrics
```

## References

### Documentation
- [pylstraight GitHub](https://github.com/r9y9/pylstraight)
- [STRAIGHT Project](http://www.fbs.osaka-u.ac.jp/~kawahara/STRAIGHTadv/)
- [Speech Vocoding Overview](https://en.wikipedia.org/wiki/Speech_coding)

### Papers
- Kawahara, H., et al. "STRAIGHT, a new high-quality speech vocoder with a low computational burden", 2001
- Yamamoto, T., et al. "Using continuous F0 trajectory for speaker identification", 2013

## See Also

- [DATA_PREPARATION.md](DATA_PREPARATION.md) - Feature extraction guide
- [PYSPTK_MIGRATION.md](PYSPTK_MIGRATION.md) - pysptk integration
- [INTEGRATION.md](INTEGRATION.md) - Complete HTS pipeline
- [data_preparation.py](scripts/data_preparation.py) - Feature extraction source
- [check_dependencies.py](scripts/check_dependencies.py) - Dependency checker

## Quick Reference

### Installation
```bash
pip install pysptk scipy numpy pylstraight
```

### Extract Features
```bash
python3 scripts/data_preparation.py --dataset X --speaker Y --usestraight 1
```

### Train Models
```bash
python3 scripts/Training.py --config X.py --train --iterations 5
```

### Features Generated
- `data/mgc/` - 26D mel-cepstral (order 25)
- `data/lf0/` - 1D log F0
- `data/bap/` - 6D band aperiodicity (order 5)
- `data/cmp/` - 33D composite (MGC + LF0 + BAP)

---

**Status:** Production-ready | **Version:** 1.0 | **Last Updated:** 2024
