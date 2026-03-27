# Integration Guide: Complete HTS Pipeline

## Overview

This guide shows how to use the complete Python-based HTS speech synthesis system combining data preparation, model building, and synthesis.

## Prerequisites

**Required:**
- Python 3.7+
- pysptk (Python SPTK wrapper) - F0/MGC extraction
- scipy (audio I/O)
- numpy (numerical computing)
- HTS toolkit (for model training)

**Optional (Recommended):**
- pylstraight (STRAIGHT vocoder) - Superior BAP extraction

**Install Python dependencies:**
```bash
# Required packages
pip install pysptk scipy numpy

# Optional (recommended for superior BAP extraction)
pip install pylstraight
```

**Install HTS toolkit:**
```bash
# From source at http://speech.sys.i.is.tohoku.ac.jp/hts/
```

## Architecture

```
┌─────────────────────────────────────┐
│     Raw Audio Files                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  data_preparation.py                │
│  • Extract Features (MGC, F0, BAP)  │
│  • Compose Training Data (CMP)      │
│  • Generate Labels                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Training Data                   │
│  • data/mgc/, lf0/, bap/            │
│  • data/cmp/ (combined)             │
│  • data/labels/ (MLF, mono, full)   │
│  • data/scp/ (train.scp, gen.scp)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Training.py                        │
│  • Build Prototypes                 │
│  • Create HMM Models                │
│  • Estimate Parameters              │
│  • Generate Decision Trees          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Trained Models                  │
│  • models/cmp/, dur/                │
│  • models/tree/                     │
│  • models/weights/                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Synthesis (Training.py synthesis)  │
│  • Generate Features                │
│  • Postfilter                       │
│  • Generate Waveform                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Synthesized Speech              │
│  • wav/gen/                         │
└─────────────────────────────────────┘
```

## Complete Workflow

### Step 1: Prepare Your Data

**Input Requirements:**
- Raw audio files (WAV format, 16 kHz recommended)
- Label files (HTK format with timestamps and phones/fullcontext)
- Configuration parameters

**Directory Structure:**
```
data/
  raw/
    utt001.wav
    utt002.wav
    ...
  labels/
    full/
      utt001.lab
      utt002.lab
      ...
    mono/
      utt001.lab
      utt002.lab
      ...
```

**Run Data Preparation:**
```bash
cd /workspaces/nit070/python

# Use default parameters
python3 scripts/data_preparation.py \
  --dataset my_corpus \
  --speaker speaker01

# Or customize parameters
python3 scripts/data_preparation.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --sampfreq 16000 \
  --mgcorder 25 \
  --baporder 5 \
  --lowerf0 80 \
  --upperf0 400
```

**Verify Data Preparation:**
```bash
# Check generated feature files
ls -la data/mgc/ data/lf0/ data/cmp/

# Verify label files were created
ls data/labels/mono.mlf data/labels/full.mlf

# Check training data scripts
head data/scp/train.scp
head data/scp/gen.scp
```

### Step 2: Configure Training Parameters

Create a configuration file with training parameters:

```bash
# Copy example configuration
cp scripts/example_config.py my_config.py

# Edit for your needs - key parameters:
# - model: {}           # HMM structure
# - train: {}           # Training algorithm
# - parameter: {}       # Feature definitions
# - numsample: {}       # Sample counts
# - etc.
```

**Key Configuration Sections:**

**Model Definition** (for model structure):
```python
'model': {
    'number_of_streams': 2,
    'stream_data_format': ['cmp', 'lf0'],
    'stream_start': [0, 26],      # Where in CMP vector
    'stream_size': [26, 1],        # Stream dimensions
    'stream_win': [2, 2],          # Number of windows
    'stream_vector_size': [26, 1], # With deltas
}
```

**Training Parameters** (for speaker adaptation):
```python
'train': {
    'speaker_f0_floor': [20.0],
    'speaker_f0_ceiling': [600.0],
    'speaker_mcep_adapt': True,
    'speaker_lf0_adapt': True,
}
```

**Parameter Definitions** (must match data preparation):
```python
'parameter': {
    'mgc_order': 25,
    'num_cep': 26,       # Including c0
    'num_lf0': 1,
    'num_bap': 6,        # If using BAP
    'lowerf0': 80,
    'upperf0': 400,
}
```

### Step 3: Build Models

**Initialize Training:**
```bash
cd /workspaces/nit070/python

# Create directory structure
mkdir -p models/cmp models/dur models/tree models/weights

# Build prototype models
python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --build-models
```

This creates:
- Model prototypes in `models/`
- Initial trees in `models/tree/`
- Prototype definitions for each stream

**Expected Output:**
```
Building models...
Creating directory structure
Generating prototype models
Creating decision trees
Creating model lists
Training.py execution completed
```

### Step 4: Train Models

**Run Model Training:**
```bash
python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --train \
  --iterations 5
```

This performs:
1. **Model initialization** - HMM parameter estimation from data
2. **Iterative training** - Baum-Welch re-estimation
3. **Parameter clustering** - Decision tree generation
4. **Adaptation** - Speaker adaptation if enabled

**Monitoring Training:**
```bash
# Check training logs
tail -f models/train.log

# Monitor convergence
grep "iteration" models/train.log | tail -20

# Check generated trees
ls models/tree/
```

### Step 5: Synthesize Speech

**Run Synthesis:**
```bash
python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --synthesize \
  --test-utterances data/scp/gen.scp
```

This generates:
- Acoustic features: `wav/gen/*.mgc`, `wav/gen/*.lf0`
- Waveforms: `wav/gen/*.wav`

**Verify Output:**
```bash
# Check synthesized waveforms
ls -lh wav/gen/*.wav

# Check quality
ffmpeg -i wav/gen/utt001.wav -show_format -show_streams

# Listen to results
aplay wav/gen/utt001.wav
```

### Step 6: Evaluate Results

**Verify Model Quality:**
```bash
# Check model file sizes (indicator of training convergence)
ls -lh models/cmp/
ls -lh models/dur/

# Check decision trees (should have balanced structure)
wc -l models/tree/*.tree

# Compare input/output feature statistics
python3 scripts/data_utils.py feature-stats data/cmp/utt001.cmp 33
python3 scripts/data_utils.py feature-stats wav/gen/utt001.mgc 26
```

**Quality Metrics:**
- **MCD (Mel-Cepstral Distortion)**: Spectral difference between natural and synthetic
- **F0 RMSE**: Pitch accuracy
- **MOS (Mean Opinion Score)**: Perceptual quality (requires listeners)

## Multi-Speaker System

For training a speaker-independent system:

### Data Preparation (All Speakers)
```bash
for speaker in speaker01 speaker02 speaker03; do
  python3 scripts/data_preparation.py \
    --dataset my_corpus \
    --speaker $speaker \
    --features-only &
done
wait

# Compose together
for speaker in speaker01 speaker02 speaker03; do
  python3 scripts/data_preparation.py \
    --dataset my_corpus \
    --speaker $speaker \
    --compose-only &
done
wait
```

### Unified Training
```bash
# Create unified training lists combining all speakers
cat data/speaker01/scp/train.scp \
    data/speaker02/scp/train.scp \
    data/speaker03/scp/train.scp > data/scp/global_train.scp

# Train with combined data
python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --train-file data/scp/global_train.scp \
  --train
```

### Speaker Adaptation
```bash
# After training global models, adapt to specific speaker
python3 scripts/Training.py \
  --config my_config.py \
  --dataset my_corpus \
  --speaker speaker01 \
  --adapt-speaker \
  --global-models models/global/
```

## Configuration File Examples

### Example 1: High-Quality Female Voice

```python
# Female speaker, 25 kHz sampling, high-order MGC

config = {
    'SAMPFREQ': 25000,
    'MODELORDER': 34,      # High-order spectral modeling
    'LOWERF0': 150,        # Female F0 range
    'UPPERF0': 600,
    'NUMSPEAKER': 1,
    'NUMWINDOW': 2,
    'NUMITERA': 5,
    'TRAPEZOID': False,
    'BESTFIRST': True,
    'TREEKIND': 'lin',
    'FASTMATH': True,
    # ... more parameters
}
```

### Example 2: Real-Time Synthesis

```python
# Lower resolution for faster synthesis

config = {
    'SAMPFREQ': 16000,
    'MODELORDER': 12,      # Low-order for speed
    'LOWERF0': 80,
    'UPPERF0': 400,
    'NUMSAMPLE': 1000,     # Fewer samples for training
    # ... more parameters
}
```

### Example 3: Multi-Language

```python
# Support multiple phoneme sets

config = {
    'SAMPFREQ': 16000,
    'PHONEMESET': 'multi',  # Support multiple languages
    'NUMSPEAKER': 5,        # Multiple speakers
    'GLOBALVARIANCE': True, # For better naturalness
    # ... more parameters
}
```

## Troubleshooting Integration

### Problem: Data Preparation Works but Training Fails

**Symptoms:**
- Data preparation completes successfully
- Training script crashes on model building

**Diagnosis:**
```bash
# Check data consistency
python3 scripts/data_utils.py feature-stats data/cmp/utt001.cmp 33

# Verify config matches data
grep MGCORDER my_config.py
grep BAPORDER my_config.py
```

**Solutions:**
- Ensure MGC order matches config vs. data preparation
- Verify CMP file dimensions in config
- Check that all utterances have matching dimensions

### Problem: Poor Synthesis Quality

**Symptoms:**
- Synthesis runs but output sounds robotic/unnatural
- Too much shimmer/distortion

**Causes & Fixes:**

| Problem | Cause | Solution |
|---------|-------|----------|
| Robotic sound | Under-fitted models | Increase training iterations |
| Shimmer/clicking | Poor MGC modeling | Increase MGC order |
| Muffled audio | Postfilter too strong | Reduce postfilter coefficient |
| Pitch artifacts | Poor F0 extraction | Adjust F0 thresholds |
| Unnatural rhythm | Poor duration modeling | Check duration model training |

### Problem: Out of Memory During Training

**Symptoms:**
- Training starts then crashes with OOM error

**Solutions:**
```bash
# Reduce dataset size
head -n 100 data/scp/train.scp > data/scp/train_subset.scp

# Run with subset
python3 scripts/Training.py \
  --config my_config.py \
  --train-file data/scp/train_subset.scp \
  --train

# Or reduce model complexity
# In config: reduce MODELORDER, NUMSAMPLE
```

### Problem: Slow Training Performance

**Optimizations:**

```bash
# 1. Use parallel processing
export OMP_NUM_THREADS=4

# 2. Reduce dataset for development
head -n 100 data/scp/train.scp > dev.scp

# 3. Profile to identify bottlenecks
time python3 scripts/Training.py --config my_config.py --train

# 4. Use lightweight config for development
# Lower MGC order, fewer iterations, smaller dataset
```

## Pipeline Extensions

### Add Speaker Adaptation

After training base model:

```bash
# Adapt to new speaker
python3 scripts/Training.py \
  --config my_config.py \
  --speaker new_speaker \
  --adapt \
  --base-models models/base/ \
  --adapt-data data/scp/speaker_adapt.scp
```

### Add Global Variance

For more natural synthesis:

```bash
# Modify config to enable GV
config['GLOBALVARIANCE'] = True
config['GVWEIGHT'] = 0.7

# Retrain with GV
python3 scripts/Training.py \
  --config my_config.py \
  --train \
  --global-variance
```

### Add Duration Models

For better rhythm:

```bash
# Train separate duration models
python3 scripts/Training.py \
  --config my_config.py \
  --train-duration-models

# Use in synthesis
python3 scripts/Training.py \
  --config my_config.py \
  --synthesize \
  --duration-models models/dur/
```

## See Also

- [README_PYTHON.md](README_PYTHON.md) - Python system overview
- [DATA_PREPARATION.md](DATA_PREPARATION.md) - Feature extraction details
- [QUICKSTART.md](QUICKSTART.md) - 5-minute quick start
- [CONVERSION_SUMMARY.md](CONVERSION_SUMMARY.md) - What was converted and why
- [Training.py](scripts/Training.py) - Training script documentation
