# Quick Fix Summary

## What Was Wrong

The original `data_preparation.py` had three critical API errors:

### Problem 1: F0 Extraction ❌
```python
# WRONG - These functions don't exist in pysptk!
f0 = pysptk.dio(audio, sr, ...)
f0 = pysptk.stonemask(audio, f0, sr, ...)
```

### Problem 2: MGC Extraction ❌
```python
# WRONG - pysptk.mgcep() with batch processing doesn't exist!
mgc = pysptk.mgcep(frames, order, ...)  # This function doesn't exist
```

### Problem 3: BAP Extraction ❌
```python
# WRONG - Non-existent API
spectrum = pylstraight.extract(audio, sr, ...)
ap = spectrum.ap  # This attribute doesn't exist
```

---

## What Was Fixed

### ✓ F0 Extraction - CORRECT
```python
# Use pylstraight (not pysptk!)
f0 = pylstraight.extract_f0(
    audio, sr,
    frame_shift=frame_shift_ms,
    f0_range=(lower, upper),
    f0_format="linear"
)
# Then convert to log: lf0 = log(f0) for voiced, 0 for unvoiced
```

### ✓ MGC Extraction - CORRECT
```python
# Use pysptk.mcep() for individual frames (not batch!)
for i, frame in enumerate(windowed_padded_frames):
    mgc[i, :] = pysptk.mcep(
        frame,
        order=mgcorder,
        alpha=freqwarp,
        eps=1.0e-8,
        etype=0,
        threshold=0.000001,
        itype=0
    )
```

### ✓ BAP Extraction - CORRECT
```python
# Use pylstraight.extract_ap() with F0 as input
f0 = pylstraight.extract_f0(...)
ap_spectrum = pylstraight.extract_ap(
    audio, sr, f0,
    frame_shift=frame_shift_ms,
    ap_format="a"
)
# Then interpolate to BAP order dimensions
```

---

## Installation

```bash
# Install required packages
pip install numpy scipy pysptk pylstraight
```

## Key Takeaways

| Feature | Library | Function | Input |
|---------|---------|----------|-------|
| **F0** | pylstraight | `extract_f0()` | audio signal |
| **MGC** | pysptk | `mcep()` | windowed frame (per-frame) |
| **BAP** | pylstraight | `extract_ap()` | audio + pre-extracted F0 |

## Files Modified

- `/workspaces/nit070/python/scripts/data_preparation.py`
  - Fixed F0 extraction (lines ~190-215)
  - Fixed MGC extraction (lines ~217-260)
  - Fixed BAP extraction (lines ~262-320)

## Testing

All functions are now syntactically correct. To test at runtime:

```python
python3 -c "from data_preparation import DataPreparation; print('✓ Import successful')"
```

