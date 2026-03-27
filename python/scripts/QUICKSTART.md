# Quick Start Guide - Python HTS Training

This guide will help you get started with the Python version of the HTS Training script in 5 minutes.

## Prerequisites

- Python 3.7 or higher
- HTS toolkit installed
- SPTK (Speech Processing Toolkit) installed
- Basic knowledge of HTS training

## Step 1: Verify Installation

Check that Python is installed:
```bash
python3 --version  # Should be 3.7 or higher
```

Check HTS tools are available:
```bash
HCompV -version
HErest -version
```

## Step 2: Copy Python Scripts

Copy the Python scripts to your HTS project:
```bash
cp Training.py /path/to/project/scripts/
cp config_loader.py /path/to/project/scripts/
cp hts_utils.py /path/to/project/scripts/
cp example_config.py /path/to/project/scripts/
```

Make Training.py executable:
```bash
chmod +x /path/to/project/scripts/Training.py
```

## Step 3: Create Configuration

### Option A: Use Your Existing Config.pm

If you already have a Perl `Config.pm`, the Python version can load it directly:

```bash
cd /path/to/project/scripts
python3 Training.py Config.pm
```

### Option B: Convert to Python Configuration

Create a Python-based configuration file:

```bash
cp example_config.py config.py
# Edit config.py to match your project
python3 Training.py config.py
```

### Option C: Create Minimal Configuration

Create a file `my_config.py`:

```python
# Minimal Configuration
prjdir = '/path/to/project'
qnum = '001'
ver = '001'
nState = 5
sr = 16000
fs = 80
fw = 0.58

SET = ['cmp', 'dur']
cmp = ['mgc', 'lf0', 'bap']
dur = ['dur']

ordr = {'mgc': 25, 'lf0': 1, 'bap': 5, 'dur': 1}
nwin = {'mgc': 3, 'lf0': 3, 'bap': 3}

# Enable first stage
MKEMV = 1
```

## Step 4: Run Training

Navigate to scripts directory:
```bash
cd /path/to/project/scripts
```

Run the training script:
```bash
# Using Python directly
python3 Training.py my_config.py

# Or using shebang (if executable)
./Training.py my_config.py
```

## Step 5: Monitor Progress

The script will output progress messages with timestamps:
```
==================================================
Start preparing environments at Thu Mar 21 10:30:45 2024
==================================================

Creating directories...
Generating configuration files...
...
```

## Configuration Quick Reference

### Essential Parameters

```python
# Project settings
prjdir = '/path/to/project'  # Project directory
qnum = '001'                 # Question set number
ver = '001'                  # Version number
nState = 5                   # Number of HMM states

# Feature parameters
sr = 16000                   # Sampling rate (Hz)
fs = 80                      # Frame shift (samples)
fw = 0.58                    # Frequency warping

# Model structure
cmp = ['mgc', 'lf0', 'bap']  # Acoustic feature types
dur = ['dur']                # Duration feature types

# Orders
ordr = {
    'mgc': 25,  # Mel-cepstral order
    'lf0': 1,   # Log F0
    'bap': 5,   # Band aperiodicity
    'dur': 1,   # Duration
}
```

### Training Stages

Enable specific training stages:

```python
# Environment setup
MKEMV = 1      # Create directories and configs

# Training stages
HCMPV = 1      # Compute variance floors
IN_RE = 1      # Initialization and re-estimation
MMMMF = 1      # Make monophone MMF
ERST0 = 1      # Re-estimation (monophone)
MN2FL = 1      # Mono-to-fullcontext conversion
ERST1 = 1      # Re-estimation (fullcontext)
CXCL1 = 1      # Tree-based clustering
ERST2 = 1      # Re-estimation (clustered)

# Advanced stages
MCDGV = 1      # Global variance training
WGEN = 1       # Waveform generation
```

### Common Adjustments

```python
# For faster training (fewer iterations)
nIte = 5       # Number of re-estimation iterations

# For smaller models
nState = 3     # Fewer states
mocc = {'mgc': 50}  # Higher minimum occurrence

# For better quality
nIte = 15      # More iterations
maxGViter = 300    # More GV iterations
maxEMiter = 30     # More EM iterations
```

## Troubleshooting

### Command Not Found

Error: `HCompV: command not found`

Solution: Add HTS bin directory to PATH:
```bash
export PATH=$PATH:/path/to/hts/bin
```

### Python Module Not Found

Error: `ModuleNotFoundError: No module named 'config_loader'`

Solution: Make sure all Python scripts are in the same directory:
```bash
ls -la /path/to/project/scripts/Training.py
ls -la /path/to/project/scripts/config_loader.py
```

### Configuration Load Error

Error: `Configuration file ... not found`

Solution: Use absolute paths in configuration:
```python
prjdir = '/absolute/path/to/project'  # Not relative paths
```

### Permission Denied

Error: `Permission denied: './Training.py'`

Solution: Make script executable:
```bash
chmod +x Training.py
```

## Next Steps

1. **Read Full Documentation**: See `README_PYTHON.md`
2. **Explore Utilities**: Check `hts_utils.py` for helper functions
3. **Advanced Configuration**: Copy and modify `example_config.py`
4. **Understand Workflow**: Review `CONVERSION_SUMMARY.md`

## Common Tasks

### Resume Training from Checkpoint

Edit configuration to skip completed stages:

```python
MKEMV = 0    # Already done
HCMPV = 0    # Already done
IN_RE = 0    # Already done
MMMMF = 0    # Already done
ERST0 = 0    # Already done
MN2FL = 1    # Resume from here
ERST1 = 1
```

### Adjust Model Quality

For better synthesis quality:

```python
nIte = 20          # More training iterations
maxGViter = 500    # More GV training
gvWeight = 1.2     # Stronger GV
maxdev = 9.0       # Higher std dev
```

For faster training:

```python
nIte = 3           # Fewer iterations
maxGViter = 50     # Less GV training
MCDGV = 0          # Skip GV
WGEN = 0           # Skip waveform generation
```

### Change Feature Types

```python
cmp = ['mgc', 'lf0']  # Remove 'bap'

ordr = {
    'mgc': 25,
    'lf0': 1,
    'dur': 1,
}

strb = {'mgc': 0, 'lf0': 25}
stre = {'mgc': 24, 'lf0': 25}
```

## Performance Tips

1. **Use SSD Storage**: Faster I/O reduces training time
2. **Parallel Processing**: Run multiple configurations simultaneously
3. **Monitor Resources**: Use `top` or `htop` to watch CPU/memory
4. **Check Disk Space**: Ensure enough space for models and statistics

## File Organization

After training completes:

```
project/
├── configs/          # HTS configuration files
├── models/           # Trained models and statistics
├── trees/            # Decision trees
├── voices/           # Converted voice files
├── gen/              # Generated parameters
├── gv/               # Global variance models
├── data/             # Training data
│   ├── labels/       # Label files
│   ├── questions/    # Question files
│   └── raw/          # Raw feature files
└── scripts/          # Python scripts
```

## Getting Help

For more information:

- **Installation Issues**: Check `README_PYTHON.md` → Troubleshooting
- **Configuration Help**: See `example_config.py` inline comments
- **Function Reference**: Review docstrings in source code
- **HTS Documentation**: http://hts.sp.nitech.ac.jp/

## Summary

You now have:
✅ Python HTS training script
✅ Configuration system
✅ Utility functions
✅ Example configurations
✅ Complete documentation

Start training your models with:
```bash
python3 Training.py my_config.py
```

Enjoy Python-based HTS training! 🚀
