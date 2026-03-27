# pysptk Migration Guide

## Overview

The `data_preparation.py` script has been refactored to use **pysptk** (Python SPTK wrapper) instead of external command-line SPTK tools. This provides a fully integrated Python pipeline for acoustic feature extraction.

## Key Changes

### Before: External SPTK Tools
```bash
# Shell pipeline using command-line tools
x2x +sf audio.raw | \
frame -l 400 -p 80 | \
window -l 400 -L 512 | \
mgcep -a 0.42 -m 25 -l 512 -e 1.0E-08 > mgc.bin

pitch -a 0.97 -f 80 -u 400 -s 16000 -p 80 audio.raw > f0.bin

# Composition with Perl scripts and merge
perl scripts/window.pl ...
merge +f -s 0 -l 1 -L 26 ...
```

### After: Integrated pysptk
```python
# Direct Python processing
from pysptk import dio, stonemask, mgcep
from scipy.io import wavfile

# F0 extraction
sr, audio = wavfile.read('audio.wav')
f0 = dio(audio, sr, frame_period=5)  # ms per frame
f0 = stonemask(audio, f0, sr, frame_period=5)

# MGC extraction
mgc = mgcep(frames, mgcorder=25, alpha=0.42)

# Feature composition (numpy)
cmp = np.concatenate([mgc, lf0[:, None]], axis=1)
```

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Dependencies** | SPTK binaries + Python | pysptk + scipy (Python packages) |
| **Installation** | Complex (compile SPTK) | Simple (`pip install pysptk scipy`) |
| **Integration** | Shell pipelines + Python | Pure Python pipeline |
| **Performance** | Good | Good (comparable) |
| **Portability** | Platform-dependent | Cross-platform |
| **Maintenance** | External tools versioning | Python package versioning |

## Required Dependencies

```bash
pip install pysptk scipy numpy
```

### Dependency Details

| Package | Purpose | Version |
|---------|---------|---------|
| **pysptk** | SPTK wrapper for F0, MGC, etc. | >=0.1.24 |
| **scipy** | Audio I/O (wavfile) | >=1.0 |
| **numpy** | Array operations | >=1.15 |

## Function Mapping

### F0 Extraction

**Before (SPTK command):**
```bash
pitch -H 400 -L 80 -p 80 -s 16.0 -o 2 audio.raw > lf0.bin
```

**After (pysptk):**
```python
import pysptk

# Load audio
sr, audio = wavfile.read('audio.wav')
audio = audio.astype(np.float64) / 32768.0

# Extract F0
frame_period = frameshift * 1000.0 / sampfreq  # Convert to ms
f0 = pysptk.dio(audio, sr, frame_period=frame_period, 
                 f0floor=80, f0ceil=400)
f0 = pysptk.stonemask(audio, f0, sr, frame_period=frame_period)

# Convert to Log F0
lf0 = np.zeros_like(f0)
lf0[f0 > 0] = np.log(f0[f0 > 0])  # Log for voiced, 0 for unvoiced
lf0.astype(np.float32).tofile('lf0.bin')
```

### MGC Extraction

**Before (SPTK commands):**
```bash
x2x +sf audio.raw | frame -l 400 -p 80 | window -l 400 -L 512 | \
mgcep -a 0.42 -m 25 -l 512 -e 1.0E-08 > mgc.bin
```

**After (pysptk):**
```python
import pysptk

# Frame extraction
frames = pysptk.util.frame_by_frame(audio, frame_len=400, hop_len=80)

# Apply window
window = np.hanning(400)
frames = frames * window

# Pad to FFT length
frames = np.pad(frames, ((0, 0), (0, 512-400)), mode='constant')

# MGC extraction
mgc = pysptk.mgcep(frames, order=25, alpha=0.42, gamma=0.0, 
                    eps=1.0e-8, etype=0, itype=0)
mgc.astype(np.float32).tofile('mgc.bin')
```

### Feature Composition

**Before (Perl scripts + SPTK merge):**
```bash
perl scripts/window.pl 26 mgc.bin win/mgc.win1 ... > mgc_windowed.bin
perl scripts/window.pl 1 lf0.bin win/lf0.win1 ... > lf0_windowed.bin
merge +f -s 0 -l 1 -L 26 mgc_windowed.bin < lf0_windowed.bin > cmp.bin
perl scripts/addhtkheader.pl 16000 80 108 9 cmp.bin > output.cmp
```

**After (Pure Python):**
```python
# Load components
mgc = np.frombuffer(open('mgc.bin', 'rb').read(), dtype=np.float32)
lf0 = np.frombuffer(open('lf0.bin', 'rb').read(), dtype=np.float32)

# Reshape
mgc_frames = mgc.reshape(-1, 26)  # mgcorder+1
lf0_frames = lf0.reshape(-1, 1)

# Concatenate
cmp = np.concatenate([mgc_frames, lf0_frames], axis=1)

# Add HTK header and save
_write_htk_file('output.cmp', cmp, frameshift=80)
```

## Audio Format Support

### Input Formats
- **WAV files**: Automatically detected via scipy.io.wavfile
- **RAW files**: Assumed to be 16-bit PCM at configured sample rate
- **Auto-detection**: Checks file extension (.wav vs .raw)

### Example
```python
# WAV file
sr, audio = wavfile.read('audio.wav')

# RAW file
with open('audio.raw', 'rb') as f:
    audio = np.frombuffer(f.read(), dtype=np.int16)
sr = 16000  # or config.sampfreq
```

## Configuration Parameters

### Mapping to pysptk Functions

**Sampling Rate (`sampfreq`)**
- Used in frame_period calculation
- pysptk expects sample rate in Hz

**Frame Length (`framelen`)**
- pysptk: `frame_len` parameter in `frame_by_frame()`
- Typically 400 samples for 16 kHz (25 ms frames)

**Frame Shift (`frameshift`)**
- pysptk: `hop_len` parameter in `frame_by_frame()`
- Typically 80 samples for 16 kHz (5 ms shift)

**MGC Order (`mgcorder`)**
- pysptk: `order` parameter in `mgcep()`
- Common values: 25, 39, 50
- Output dimension = order + 1 (includes c0)

**Frequency Warping (`freqwarp`)**
- pysptk: `alpha` parameter in `mgcep()`
- Mel-cepstral analysis constant
- Common value: 0.42 (for 16 kHz audio)

**F0 Range (`lowerf0`, `upperf0`)**
- pysptk: `f0floor`, `f0ceil` parameters
- Typical: 80-400 Hz for adult speech

## Migration Checklist

- [x] Replace x2x, frame, window with pysptk framing
- [x] Replace pitch with pysptk.dio + stonemask
- [x] Replace mgcep with pysptk.mgcep
- [x] Replace merge with numpy concatenation
- [x] Add HTK header writing (was in Perl scripts)
- [x] Add scipy audio I/O for WAV files
- [x] Update error handling for pysptk exceptions
- [x] Update documentation
- [x] Test with sample data

## Troubleshooting

### Issue: Import Error for pysptk
```
ModuleNotFoundError: No module named 'pysptk'
```
**Solution:**
```bash
pip install pysptk
```

### Issue: Audio File Not Found
```
FileNotFoundError: [Errno 2] No such file or directory: 'audio.wav'
```
**Solution:** Ensure audio files are in `data/raw/` directory and named with pattern `{dataset}_{speaker}_*.wav`

### Issue: Feature Dimension Mismatch
```
Frame mismatch: MGC 1000 != LF0 999
```
**Cause:** Different number of frames extracted due to parameter mismatch
**Solution:** Verify identical parameters used for all features:
- framelen, frameshift, sampfreq must be consistent
- Check MGC order matches between extraction and composition

### Issue: Poor Quality Features
```
Extracted features look distorted or silent
```
**Solutions:**
- Check audio amplitude (should be float32 in [-1, 1] range)
- Verify frame parameters match audio sample rate
- Try adjusting window type (Hamming vs Hanning)
- Increase FFT length for better spectral resolution

## Performance Notes

- **pysptk speed**: Comparable to native SPTK tools
- **Memory usage**: Features loaded entirely in RAM (typical 1-4 GB)
- **For large datasets**: Consider batch processing by speaker

## Version Compatibility

- **pysptk**: >= 0.1.24
- **scipy**: >= 1.0
- **numpy**: >= 1.15
- **Python**: >= 3.7

## References

- [pysptk Documentation](http://r9y9.github.io/pysptk/)
- [SPTK Reference](http://sp-nitech.github.io/sptk/latest/)
- [Acoustic Feature Extraction](https://en.wikipedia.org/wiki/Mel-frequency_cepstral_coefficient)

## See Also

- [DATA_PREPARATION.md](DATA_PREPARATION.md) - Feature extraction guide
- [data_preparation.py](scripts/data_preparation.py) - Implementation
- [INTEGRATION.md](INTEGRATION.md) - Complete pipeline guide
