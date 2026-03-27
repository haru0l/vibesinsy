# Data Preparation Guide

## Overview

The data preparation tools convert raw audio files into acoustic features suitable for HTS model training using **pysptk** for F0/MGC extraction and **pylstraight** for superior STRAIGHT-based BAP (band aperiodicity) extraction. This guide covers using `data_preparation.py` and `makefile.py` to prepare your speech datasets.

## Components

### data_preparation.py
Main feature extraction and data composition script.

**Features:**
- Extracts acoustic features (MGC, F0, BAP) from raw audio using SPTK
- Composes training data by combining feature streams
- Generates label files and model lists
- Creates SCP (script) files for training

### makefile.py
Provides Make-compatible interface to data_preparation.py.

**Usage:** Makes it easy to run specific preparation stages

### data_utils.py
Utility functions for label and feature file handling.

## Quick Start

### Basic Feature Extraction

```bash
cd /path/to/python

# Extract all features and prepare training data
python3 scripts/data_preparation.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --raw-dir data/raw

# Or use make-style targets
python3 scripts/makefile.py all
```

### Pipeline Stages

```bash
# Stage 1: Extract acoustic features (MGC, F0, BAP)
python3 scripts/data_preparation.py --dataset my_corpus --features-only

# Stage 2: Compose training data
python3 scripts/data_preparation.py --dataset my_corpus --compose-only

# Stage 3: Generate labels and model lists
python3 scripts/data_preparation.py --dataset my_corpus --lists-only

# Or run all stages
python3 scripts/data_preparation.py --dataset my_corpus
```

## Configuration

### Command-Line Parameters

```
Feature Extraction:
  --sampfreq INT          Sampling frequency (Hz) [16000]
  --framelen INT          Frame length (samples) [400]
  --frameshift INT        Frame shift (samples) [80]
  --fftlen INT            FFT length [512]

Feature Parameters:
  --mgcorder INT          MGC order [25]
  --baporder INT          BAP order [5]
  --gamma FLOAT           Mel-cepstral analysis gamma [0.42]
  --lowerf0 FLOAT         Lower F0 threshold (Hz) [80]
  --upperf0 FLOAT         Upper F0 threshold (Hz) [400]
  --lngain BOOL           Use log gain [true]

Data:
  --dataset STR           Dataset name [default]
  --speaker STR           Speaker ID [speaker01]
  --raw-dir PATH          Raw audio directory [data/raw]

Pipeline Control:
  --features-only         Extract features only, skip composition
  --compose-only          Skip feature extraction, compose training data only
  --lists-only            Skip features/compose, generate lists only
```

### AnalysisConfig Defaults

```python
sampfreq: 16000      # Sampling frequency
framelen: 400        # Frame length
frameshift: 80       # Frame shift
fftlen: 512          # FFT length
mgcorder: 25         # MGC order
baporder: 5          # BAP order (0 for without BAP)
gamma: 0.42          # Mel-cepstral analysis constant
lowerf0: 80          # F0 extraction lower bound
upperf0: 400         # F0 extraction upper bound
lngain: True         # Use log gain
```

## File Organization

After running data preparation:

```
data/
  mgc/              # Mel-cepstral coefficients
  lf0/              # Log fundamental frequency
  bap/              # Band aperiodicity (if enabled)
  cmp/              # Composite features (MGC+LF0+BAP)
  labels/
    mono.mlf        # Monophone model list
    full.mlf        # Fullcontext model list
    mono/           # Monophone labels
    full/           # Fullcontext labels
  lists/
    train.list      # Training model list
    all.list        # All model list
  scp/
    train.scp       # Training data script
    gen.scp         # Generation data script
```

## Acoustic Features Explained

### MGC (Mel-Generalized Cepstral coefficients)
- Spectral features for speech modeling
- Order typically 25 (dimension 26 with c0)
- Extracted using SPTK `mgcep`

### LF0 (Log Fundamental Frequency)
- Pitch information for prosody
- Single dimension (or 3 with delta/acceleration)
- Extracted using SPTK `pitch`
- Voiced/unvoiced classification included

### BAP (Band Aperiodicity)
- Aperiodic components of speech
- Order typically 5 (dimension 6 with power)
- Extracted using SPTK `mcep` then `lpc2lsp`
- Optional, useful for more natural synthesis

### CMP (Composite)
- Concatenated feature vector
- Order: MGC + LF0 + BAP
- Example: [26D MGC] [1D LF0] [6D BAP] = 33D total
- Used directly for HMM training

## Extraction Process

### 1. Feature Extraction (using pysptk & pylstraight)

**Audio Loading:**
- Supports WAV and raw audio formats
- Automatically detects sampling rate from WAV files
- Converts audio to float32 for processing

**MGC Extraction:**
```python
# Using pysptk.mgcep for mel-cepstral analysis
- Frame audio with configurable length and shift
- Apply window function (Hamming/Hanning/Blackman)
- Zero-pad to FFT length
- Extract MGC coefficients with frequency warping
```

**F0/LF0 Extraction:**
```python
# Using pysptk.dio + stonemask for F0 estimation
dio()      # Initial F0 estimation using DIO algorithm
stonemask() # Refine F0 trajectory using StoneMask
Log conversion for LF0 (0 for unvoiced frames)
```

**BAP Extraction (STRAIGHT-based):**
```python
# Primary: pylstraight STRAIGHT vocoder analysis
# Provides superior aperiodicity/voicing estimation
spectrum = pylstraight.extract(audio, sr, frame_period)
ap_spectrum = spectrum.ap  # Aperiodicity spectrum
# Downsample to BAP order dimensions

# Fallback: pysptk spectral estimation (if pylstraight not available)
# Uses mel-cepstrum with gamma parameter
```

### 2. Data Composition

Features are concatenated into single CMP files:

```
[Frame 0 MGC (26D)][LF0][BAP (6D)]
[Frame 1 MGC (26D)][LF0][BAP (6D)]
...
```

Result: Time-series feature matrix suitable for HMM training

### 3. Label Generation

MLF (Master Label Format) files group frames by phone/model:

```
#!MLF!#
"label001.lab"
0 100000 aa 1
100000 200000 bb 2
200000 300000 cc 3
.
"label002.lab"
0 100000 dd 1
...
```

## Integration with Training.py

Complete speech synthesis pipeline:

```bash
# 1. Prepare data
python3 scripts/data_preparation.py --dataset my_corpus --speaker spk01

# 2. Load configuration
python3 scripts/Training.py --config config.pm \
  --dataset my_corpus \
  --speaker spk01 \
  --build-models

# 3. Train models
python3 scripts/Training.py --config config.pm \
  --dataset my_corpus \
  --speaker spk01 \
  --train

# 4. Synthesize
python3 scripts/Training.py --config config.pm \
  --dataset my_corpus \
  --speaker spk01 \
  --synthesize
```

## Common Tasks

### Extract Features for Multiple Speakers

```bash
for speaker in spk01 spk02 spk03; do
  python3 scripts/data_preparation.py \
    --dataset my_corpus \
    --speaker $speaker
done
```

### Use Different Parameters

```bash
# Higher quality features
python3 scripts/data_preparation.py \
  --dataset my_corpus \
  --mgcorder 39 \
  --baporder 5 \
  --frameshift 50

# Lower frequency (e.g., for infant speech)
python3 scripts/data_preparation.py \
  --dataset my_corpus \
  --lowerf0 150 \
  --upperf0 300
```

### Clean Generated Features

```bash
# Remove all generated features
python3 scripts/makefile.py clean

# Remove specific features
python3 scripts/makefile.py clean_mgc
python3 scripts/makefile.py clean_lf0
python3 scripts/makefile.py clean_cmp
```

### Verify Feature Generation

```bash
# Check feature files exist and have correct dimensions
python3 scripts/data_utils.py feature-stats data/mgc/utt001.mgc 26
python3 scripts/data_utils.py feature-stats data/lf0/utt001.lf0 1
python3 scripts/data_utils.py feature-stats data/cmp/utt001.cmp 33
```

### Inspect Labels

```bash
# View label file content
python3 scripts/data_utils.py read-label data/labels/full/utt001.lab

# Extract monophone from fullcontext label
python3 scripts/data_utils.py extract-mono "aa+bb-cc+dd"
```

## Troubleshooting

### Missing Python Packages

**Error:** `ModuleNotFoundError: No module named 'pysptk'`

**Solution:** Install required packages
```bash
pip install pysptk scipy numpy
```

### Missing pylstraight (Optional)

**Error:** `pylstraight not available. BAP extraction disabled`

**Solution:** Install pylstraight for STRAIGHT-based BAP extraction
```bash
pip install pylstraight
```

If not installed, BAP extraction falls back to pysptk spectral estimation (less accurate but functional).

### Audio Dimension Mismatch

**Error:** `Number of values doesn't match expected dimension`

**Solution:** Check parameters match feature extraction settings
- MGC order determines feature dimension
- Ensure same order used for extraction and training

### Label File Format Issues

**Error:** `Error parsing label file`

**Resolution:** Verify label format:
```
start_time end_time label
100000 200000 aa
```
- Times in HTK format (100ns units)
- White-space separated
- One label per line

### Low F0 Extraction Quality

**Issue:** Many unvoiced frames or extraction failures

**Solutions:**
- Adjust F0 thresholds: `--lowerf0 60 --upperf0 500`
- Check audio quality and sampling frequency
- Verify `--sampfreq` matches actual audio sample rate

## Performance Tips

1. **Parallel Processing**: Process multiple speakers in parallel
   ```bash
   for speaker in spk01 spk02 spk03; do
     python3 scripts/data_preparation.py --speaker $speaker &
   done
   wait
   ```

2. **Skip Unnecessary Stages**: Use `--features-only` or `--compose-only`
   - Saves time if only certain stages need reprocessing

3. **Feature Parameters**: Balance quality vs. training time
   - Higher order MGC = better quality but slower training
   - Common choices: 25 or 39 for MGC order

## Output Verification

After successful preparation:

```bash
# 1. Check directories created
ls -la data/{mgc,lf0,bap,cmp,labels,lists,scp}/

# 2. Verify feature files
ls data/mgc/ | wc -l  # Should match number of audio files

# 3. Check model lists
head data/lists/train.list
head data/lists/all.list

# 4. Verify SCP files
head data/scp/train.scp
head data/scp/gen.scp

# 5. Check label files
head data/labels/mono.mlf
```

## Advanced Configuration

For complex setups, create a Python configuration file:

```python
# my_config.py
class AnalysisConfig:
    sampfreq = 16000
    framelen = 400
    frameshift = 80
    mgcorder = 25
    baporder = 5
    gamma = 0.42
    lowerf0 = 80
    upperf0 = 400
    lngain = True
    dataset = 'my_corpus'
    speaker = 'speaker01'
    raw_dir = 'data/raw'
```

Then pass to data_preparation.py for programmatic use:

```python
from data_preparation import DataPreparation
from my_config import AnalysisConfig

config = AnalysisConfig()
prep = DataPreparation(config)
prep.run_all()
```

## See Also

- [README_PYTHON.md](README_PYTHON.md) - Main documentation
- [Training.py](Training.py) - HTS model training
- [SPTK Documentation](http://sp-nitech.github.io/sptk/latest/) - Feature extraction details
