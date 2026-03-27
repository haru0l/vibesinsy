#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTS Data Preparation and Feature Extraction

This script performs acoustic feature extraction and data preparation for HTS training.
Equivalent to the Makefile.in data preparation workflow.

Uses:
- pysptk for F0 and MGC extraction
- scipy for audio I/O
- pylstraight for superior BAP (band aperiodicity) extraction via STRAIGHT vocoder
"""

import os
import sys
import subprocess
import argparse
import numpy as np
from pathlib import Path
from dataclasses import dataclass
import struct
import warnings

# Try to import pysptk
try:
    import pysptk
    HAS_PYSPTK = True
except ImportError:
    HAS_PYSPTK = False
    warnings.warn("pysptk not found. Install with: pip install pysptk")

# Try to import scipy for audio I/O
try:
    from scipy.io import wavfile
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    warnings.warn("scipy not found. Install with: pip install scipy")

# Try to import pylstraight for STRAIGHT-based features (BAP)
try:
    import pylstraight
    HAS_PYLSTRAIGHT = True
except ImportError:
    HAS_PYLSTRAIGHT = False
    warnings.warn("pylstraight not found. BAP extraction disabled. Install with: pip install pylstraight")


@dataclass
class AnalysisConfig:
    """Configuration for acoustic analysis"""
    # Audio parameters
    sampfreq: int = 16000      # Sampling frequency (Hz)
    framelen: int = 400         # Frame length (samples) = sampfreq * 0.025
    frameshift: int = 80        # Frame shift (samples) = sampfreq * 0.005
    fftlen: int = 512           # FFT length
    
    # MGC parameters
    mgcorder: int = 25          # MGC order
    freqwarp: float = 0.58      # Frequency warping factor
    gamma: int = 0              # Gamma (0=MGC, non-zero=LSP)
    lngain: int = 0             # Log gain flag
    
    # BAP parameters
    baporder: int = 5           # BAP order
    
    # F0 extraction
    lowerf0: int = 40           # Lower F0 limit (Hz)
    upperf0: int = 400          # Upper F0 limit (Hz)
    
    # Window parameters
    windowtype: int = 2         # 0=Blackman, 1=Hamming, 2=Hanning
    normalize: int = 2          # 0=none, 1=by power, 2=by magnitude
    
    # Vocoder settings
    usestraight: int = 0        # Use STRAIGHT vocoder
    
    # Directories
    rawdir: str = "raw"
    mgcdir: str = "mgc"
    lf0dir: str = "lf0"
    bapdir: str = "bap"
    cmpdir: str = "cmp"
    labeldir: str = "labels"
    listdir: str = "lists"
    scpdir: str = "scp"
    
    # Dataset info
    dataset: str = "dataset"
    speaker: str = "speaker"


class DataPreparation:
    """Handle data preparation and feature extraction using pysptk"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available"""
        if not HAS_PYSPTK:
            raise ImportError(
                "pysptk is required for MGC extraction. "
                "Install with: pip install pysptk"
            )
        if not HAS_SCIPY:
            raise ImportError(
                "scipy is required for audio I/O. "
                "Install with: pip install scipy"
            )
        if not HAS_PYLSTRAIGHT and self.config.usestraight:
            print("Warning: pylstraight not available. BAP extraction will be skipped.")
            print("Install with: pip install pylstraight")
    
    def create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config.mgcdir,
            self.config.lf0dir,
            self.config.bapdir,
            self.config.cmpdir,
            os.path.join(self.config.labeldir, 'mono'),
            os.path.join(self.config.labeldir, 'full'),
            os.path.join(self.config.labeldir, 'gen'),
            self.config.listdir,
            self.config.scpdir,
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
    
    def extract_features(self):
        """Extract acoustic features from raw audio files using pysptk"""
        print("Extracting acoustic features using pysptk...")
        
        raw_files = sorted(Path(self.config.rawdir).glob(f"{self.config.dataset}_{self.config.speaker}_*.raw"))
        wav_files = sorted(Path(self.config.rawdir).glob(f"{self.config.dataset}_{self.config.speaker}_*.wav"))
        
        # Support both RAW and WAV formats
        all_files = list(wav_files) + list(raw_files)
        
        if not all_files:
            print(f"Warning: No audio files found in {self.config.rawdir}")
            return
        
        for audio_file in all_files:
            base = audio_file.stem
            print(f"\nProcessing {base}...")
            
            # Load audio
            try:
                if audio_file.suffix.lower() == '.wav':
                    sr, audio = wavfile.read(audio_file)
                    # Ensure 16-bit conversion if needed
                    if audio.dtype != np.int16:
                        audio = np.int16(audio / np.max(np.abs(audio)) * 32767)
                else:
                    # Raw format - assume 16-bit PCM
                    with open(audio_file, 'rb') as f:
                        audio = np.frombuffer(f.read(), dtype=np.int16)
                    sr = self.config.sampfreq
                
                # Convert to float
                audio = audio.astype(np.float64) / 32768.0
                
            except Exception as e:
                print(f"  ✗ Failed to load audio: {e}")
                continue
            
            # Extract features
            # Always extract F0 and MGC (required)
            self._extract_f0(audio, sr, base)
            self._extract_mgc(audio, sr, base)
            
            # Extract BAP only if enabled and pylstraight is available
            if self.config.usestraight and HAS_PYLSTRAIGHT:
                self._extract_bap(audio, sr, base)
    
    def _extract_f0(self, audio: np.ndarray, sr: int, base: str):
        """Extract log F0 using pylstraight"""
        lf0_file = Path(self.config.lf0dir) / f"{base}.lf0"
        
        try:
            # Frame shift in milliseconds for pylstraight
            frame_shift_ms = self.config.frameshift * 1000.0 / sr
            
            # Use pylstraight's extract_f0 for F0 extraction (linear format)
            f0 = pylstraight.extract_f0(
                audio,
                sr,
                frame_shift=frame_shift_ms,
                f0_range=(self.config.lowerf0, self.config.upperf0),
                f0_format="linear",
            )
            
            # Convert to log F0 (unvoiced=0, voiced=log(f0))
            lf0 = np.zeros_like(f0)
            voiced = f0 > 0
            lf0[voiced] = np.log(f0[voiced])
            
            # Save as binary
            lf0.astype(np.float32).tofile(lf0_file)
            print(f"  ✓ Extracted F0 to {lf0_file} ({len(lf0)} frames)")
            
        except Exception as e:
            print(f"  ✗ Failed to extract F0: {e}")
            print(f"    Ensure pylstraight is installed: pip install pylstraight")
    
    def _extract_mgc(self, audio: np.ndarray, sr: int, base: str):
        """Extract mel-cepstral coefficients using pysptk"""
        mgc_file = Path(self.config.mgcdir) / f"{base}.mgc"
        
        try:
            # Frame extraction
            frames = pysptk.util.frame_by_frame(
                audio,
                self.config.framelen,
                self.config.frameshift,
            )
            
            # Apply window
            if self.config.windowtype == 0:  # Blackman
                window = np.blackman(self.config.framelen)
            elif self.config.windowtype == 1:  # Hamming
                window = np.hamming(self.config.framelen)
            else:  # Hanning
                window = np.hanning(self.config.framelen)
            
            windowed = frames * window
            
            # Pad to FFT length
            if self.config.fftlen > self.config.framelen:
                windowed = np.pad(
                    windowed,
                    ((0, 0), (0, self.config.fftlen - self.config.framelen)),
                    mode='constant'
                )
            
            # MGC extraction - extract MCEP for each frame
            num_frames = windowed.shape[0]
            mgc = np.zeros((num_frames, self.config.mgcorder + 1), dtype=np.float64)
            
            for i, frame in enumerate(windowed):
                # Use pysptk.mcep for spectral envelope extraction
                mgc[i, :] = pysptk.mcep(
                    frame,
                    order=self.config.mgcorder,
                    alpha=self.config.freqwarp,
                    eps=1.0e-8,
                    etype=0,
                    threshold=0.000001,
                    itype=0,
                )
            
            # Save as binary
            mgc.astype(np.float32).tofile(mgc_file)
            print(f"  ✓ Extracted MGC to {mgc_file} ({mgc.shape[0]} frames x {mgc.shape[1]} dims)")
            
        except Exception as e:
            print(f"  ✗ Failed to extract MGC: {e}")
            print(f"    Ensure pysptk is installed: pip install pysptk")
    
    def _extract_bap(self, audio: np.ndarray, sr: int, base: str):
        """Extract band aperiodicity using pylstraight STRAIGHT vocoder"""
        bap_file = Path(self.config.bapdir) / f"{base}.bap"
        
        if not HAS_PYLSTRAIGHT:
            print(f"  ⊘ pylstraight not available. Install with: pip install pylstraight")
            return
        
        try:
            # Frame shift in milliseconds for pylstraight
            frame_shift_ms = self.config.frameshift * 1000.0 / sr
            
            # First extract F0 using pylstraight
            f0 = pylstraight.extract_f0(
                audio,
                sr,
                frame_shift=frame_shift_ms,
                f0_range=(self.config.lowerf0, self.config.upperf0),
                f0_format="linear",
            )
            
            # Then extract aperiodicity using pylstraight.extract_ap
            # Returns shape (nframe, nfreq) with aperiodicity spectrum
            ap_spectrum = pylstraight.extract_ap(
                audio,
                sr,
                f0,
                frame_shift=frame_shift_ms,
                ap_format="a",  # aperiodicity (0=fully periodic, 1=fully aperiodic)
            )
            
            # Downsample aperiodicity spectrum to BAP order dimensions
            num_frames, num_freqs = ap_spectrum.shape
            bap = np.zeros((num_frames, self.config.baporder + 1), dtype=np.float64)
            
            # Linear interpolation to BAP order dimensions
            indices = np.linspace(0, num_freqs - 1, self.config.baporder + 1)
            for i, idx in enumerate(indices):
                idx_low = int(np.floor(idx))
                idx_high = int(np.ceil(idx))
                if idx_low == idx_high:
                    bap[:, i] = ap_spectrum[:, idx_low]
                else:
                    # Linear interpolation
                    weight = idx - idx_low
                    bap[:, i] = (1 - weight) * ap_spectrum[:, idx_low] + weight * ap_spectrum[:, idx_high]
            
            # Save as binary
            bap.astype(np.float32).tofile(bap_file)
            print(f"  ✓ Extracted BAP using STRAIGHT to {bap_file} ({bap.shape[0]} frames x {bap.shape[1]} dims)")
            
        except Exception as e:
            print(f"  ✗ Failed to extract BAP: {e}")
            print(f"    Install pylstraight: pip install pylstraight")
    
    def compose_training_data(self):
        """Compose training data from extracted features"""
        print("\nComposing training data...")
        
        raw_files = sorted(Path(self.config.rawdir).glob(f"{self.config.dataset}_{self.config.speaker}_*.raw"))
        
        for raw_file in raw_files:
            base = raw_file.stem
            mgc_file = Path(self.config.mgcdir) / f"{base}.mgc"
            lf0_file = Path(self.config.lf0dir) / f"{base}.lf0"
            cmp_file = Path(self.config.cmpdir) / f"{base}.cmp"
            
            # Check if required files exist
            if not (mgc_file.exists() and lf0_file.exists()):
                print(f"  ⊘ Skipping {base} (missing MGC or F0)")
                continue
            
            print(f"  Composing {base}...")
            
            if self.config.usestraight:
                self._compose_with_bap(base, mgc_file, lf0_file, cmp_file)
            else:
                self._compose_mgc_lf0(base, mgc_file, lf0_file, cmp_file)
    
    def _compose_mgc_lf0(self, base: str, mgc_file: Path, lf0_file: Path, cmp_file: Path):
        """Compose MGC and LF0 into training data"""
        try:
            # Load feature files
            with open(mgc_file, 'rb') as f:
                mgc_data = np.frombuffer(f.read(), dtype=np.float32)
            
            with open(lf0_file, 'rb') as f:
                lf0_data = np.frombuffer(f.read(), dtype=np.float32)
            
            # Calculate dimensions
            mgc_dim = self.config.mgcorder + 1
            lf0_dim = 1
            
            # Reshape to frames
            num_frames_mgc = len(mgc_data) // mgc_dim
            num_frames_lf0 = len(lf0_data) // lf0_dim
            
            if num_frames_mgc != num_frames_lf0:
                print(f"    ✗ Frame mismatch: MGC {num_frames_mgc} != LF0 {num_frames_lf0}")
                return
            
            mgc = mgc_data[:num_frames_mgc * mgc_dim].reshape(num_frames_mgc, mgc_dim)
            lf0 = lf0_data[:num_frames_lf0 * lf0_dim].reshape(num_frames_lf0, lf0_dim)
            
            # Concatenate: [MGC | LF0]
            cmp = np.concatenate([mgc, lf0], axis=1)
            
            # Add HTK header
            self._write_htk_file(cmp_file, cmp, self.config.frameshift)
            print(f"    ✓ Composed {cmp_file} ({cmp.shape[0]} frames x {cmp.shape[1]} dims)")
            
        except Exception as e:
            print(f"    ✗ Failed to compose {cmp_file}: {e}")
    
    def _compose_with_bap(self, base: str, mgc_file: Path, lf0_file: Path, cmp_file: Path):
        """Compose MGC, LF0, and BAP into training data"""
        try:
            # Load feature files
            with open(mgc_file, 'rb') as f:
                mgc_data = np.frombuffer(f.read(), dtype=np.float32)
            
            with open(lf0_file, 'rb') as f:
                lf0_data = np.frombuffer(f.read(), dtype=np.float32)
            
            bap_file = Path(self.config.bapdir) / f"{base}.bap"
            if not bap_file.exists():
                print(f"    ✗ Missing BAP file: {bap_file}")
                return
            
            with open(bap_file, 'rb') as f:
                bap_data = np.frombuffer(f.read(), dtype=np.float32)
            
            # Calculate dimensions
            mgc_dim = self.config.mgcorder + 1
            lf0_dim = 1
            bap_dim = self.config.baporder + 1
            
            # Reshape to frames
            num_frames_mgc = len(mgc_data) // mgc_dim
            num_frames_lf0 = len(lf0_data) // lf0_dim
            num_frames_bap = len(bap_data) // bap_dim
            
            num_frames = min(num_frames_mgc, num_frames_lf0, num_frames_bap)
            
            mgc = mgc_data[:num_frames * mgc_dim].reshape(num_frames, mgc_dim)
            lf0 = lf0_data[:num_frames * lf0_dim].reshape(num_frames, lf0_dim)
            bap = bap_data[:num_frames * bap_dim].reshape(num_frames, bap_dim)
            
            # Concatenate: [MGC | LF0 | BAP]
            cmp = np.concatenate([mgc, lf0, bap], axis=1)
            
            # Add HTK header
            self._write_htk_file(cmp_file, cmp, self.config.frameshift)
            print(f"    ✓ Composed {cmp_file} ({cmp.shape[0]} frames x {cmp.shape[1]} dims)")
            
        except Exception as e:
            print(f"    ✗ Failed to compose {cmp_file}: {e}")
    
    def _write_htk_file(self, filepath: Path, data: np.ndarray, frameshift: int):
        """Write HTK format file with header"""
        try:
            num_frames, num_dims = data.shape
            bytes_per_frame = num_dims * 4  # float32
            
            # HTK header format:
            # nSamples (4 bytes) | samplePeriod (4 bytes) | sampSize (2 bytes) | parmKind (2 bytes)
            header = struct.pack('>I', num_frames)  # nSamples
            header += struct.pack('>I', frameshift * 10000 // self.config.sampfreq)  # samplePeriod in 100ns
            header += struct.pack('>H', bytes_per_frame)  # sampSize
            header += struct.pack('>H', 9)  # parmKind (USER)
            
            with open(filepath, 'wb') as f:
                f.write(header)
                data.astype(np.float32).tofile(f)
        
        except Exception as e:
            print(f"    ✗ Error writing HTK file {filepath}: {e}")
    
    def generate_label_files(self):
        """Generate MLF (Master Label File)"""
        print("\nGenerating label files...")
        
        mono_mlf = Path(self.config.labeldir) / "mono.mlf"
        full_mlf = Path(self.config.labeldir) / "full.mlf"
        
        pwd = str(Path.cwd())
        
        # Generate mono MLF
        with open(mono_mlf, 'w') as f:
            f.write("#!MLF!#\n")
            f.write(f'"*/{self.config.dataset}_{self.config.speaker}_*.lab" -> ')
            f.write(f'"{pwd}/data/labels/mono"\n')
        print(f"  ✓ Generated {mono_mlf}")
        
        # Generate full MLF
        with open(full_mlf, 'w') as f:
            f.write("#!MLF!#\n")
            f.write(f'"*/{self.config.dataset}_{self.config.speaker}_*.lab" -> ')
            f.write(f'"{pwd}/data/labels/full"\n')
        print(f"  ✓ Generated {full_mlf}")
    
    def generate_model_lists(self):
        """Generate model list files"""
        print("\nGenerating model lists...")
        
        mono_list = set()
        full_list = set()
        
        # Collect from label files
        for lab_file in Path(self.config.labeldir, 'full').glob(f"{self.config.dataset}_{self.config.speaker}_*.lab"):
            if lab_file.stat().st_size > 0:
                with open(lab_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            # Extract label (last field)
                            label = line.split()[-1]
                            full_list.add(label)
                            
                            # Extract monophone
                            mono = label.split('-')[1].split('+')[0]
                            mono_list.add(mono)
        
        # Add unseen models from gen labels
        for lab_file in Path(self.config.labeldir, 'gen').glob("*.lab"):
            if lab_file.stat().st_size > 0:
                with open(lab_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            label = line.split()[-1]
                            full_list.add(label)
        
        # Write lists
        lists_dir = Path(self.config.listdir)
        lists_dir.mkdir(parents=True, exist_ok=True)
        
        # Full list
        with open(lists_dir / "full.list", 'w') as f:
            for model in sorted(full_list):
                f.write(f"{model}\n")
        print(f"  ✓ Generated {lists_dir / 'full.list'}")
        
        # Full list with unseen
        with open(lists_dir / "full_all.list", 'w') as f:
            for model in sorted(full_list):
                f.write(f"{model}\n")
        print(f"  ✓ Generated {lists_dir / 'full_all.list'}")
        
        # Monophone list
        with open(lists_dir / "mono.list", 'w') as f:
            for model in sorted(mono_list):
                f.write(f"{model}\n")
        print(f"  ✓ Generated {lists_dir / 'mono.list'}")
    
    def generate_train_scp(self):
        """Generate training data script file"""
        print("\nGenerating training SCP file...")
        
        scp_dir = Path(self.config.scpdir)
        scp_dir.mkdir(parents=True, exist_ok=True)
        
        pwd = str(Path.cwd())
        
        with open(scp_dir / "train.scp", 'w') as f:
            for cmp_file in sorted(Path(self.config.cmpdir).glob(f"{self.config.dataset}_{self.config.speaker}_*.cmp")):
                # Check if corresponding label files exist
                base = cmp_file.stem
                mono_lab = Path(self.config.labeldir, 'mono', f"{base}.lab")
                full_lab = Path(self.config.labeldir, 'full', f"{base}.lab")
                
                if cmp_file.stat().st_size > 0 and mono_lab.exists() and full_lab.exists():
                    f.write(f"{pwd}/{cmp_file}\n")
        
        print(f"  ✓ Generated {scp_dir / 'train.scp'}")
    
    def generate_gen_scp(self):
        """Generate generation label script file"""
        print("\nGenerating generation SCP file...")
        
        scp_dir = Path(self.config.scpdir)
        scp_dir.mkdir(parents=True, exist_ok=True)
        
        pwd = str(Path.cwd())
        
        with open(scp_dir / "gen.scp", 'w') as f:
            for lab_file in sorted(Path(self.config.labeldir, 'gen').glob("*.lab")):
                f.write(f"{pwd}/{lab_file}\n")
        
        print(f"  ✓ Generated {scp_dir / 'gen.scp'}")
    
    def run_all(self):
        """Run complete data preparation pipeline"""
        self.create_directories()
        self.extract_features()
        self.compose_training_data()
        self.generate_label_files()
        self.generate_model_lists()
        self.generate_train_scp()
        self.generate_gen_scp()
        print("\n✓ Data preparation complete!")


def main():
    parser = argparse.ArgumentParser(
        description="HTS Data Preparation and Feature Extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline with default settings
  %(prog)s

  # Extract features only
  %(prog)s --features-only

  # Compose training data only
  %(prog)s --compose-only

  # Custom configuration
  %(prog)s --sampfreq 16000 --mgcorder 25 --dataset mydata --speaker myspeaker
        """
    )
    
    parser.add_argument('--sampfreq', type=int, default=16000, help='Sampling frequency (Hz)')
    parser.add_argument('--framelen', type=int, default=400, help='Frame length (samples)')
    parser.add_argument('--frameshift', type=int, default=80, help='Frame shift (samples)')
    parser.add_argument('--fftlen', type=int, default=512, help='FFT length')
    parser.add_argument('--mgcorder', type=int, default=25, help='MGC order')
    parser.add_argument('--baporder', type=int, default=5, help='BAP order')
    parser.add_argument('--freqwarp', type=float, default=0.58, help='Frequency warping factor')
    parser.add_argument('--gamma', type=int, default=0, help='Gamma (0=MGC, non-zero=LSP)')
    parser.add_argument('--lowerf0', type=int, default=40, help='Lower F0 limit (Hz)')
    parser.add_argument('--upperf0', type=int, default=400, help='Upper F0 limit (Hz)')
    parser.add_argument('--dataset', default='dataset', help='Dataset name')
    parser.add_argument('--speaker', default='speaker', help='Speaker name')
    parser.add_argument('--raw-dir', default='raw', help='Raw audio directory')
    parser.add_argument('--features-only', action='store_true', help='Extract features only')
    parser.add_argument('--compose-only', action='store_true', help='Compose data only')
    parser.add_argument('--lists-only', action='store_true', help='Generate lists only')
    
    args = parser.parse_args()
    
    # Create configuration
    config = AnalysisConfig(
        sampfreq=args.sampfreq,
        framelen=args.framelen,
        frameshift=args.frameshift,
        fftlen=args.fftlen,
        mgcorder=args.mgcorder,
        baporder=args.baporder,
        freqwarp=args.freqwarp,
        gamma=args.gamma,
        lowerf0=args.lowerf0,
        upperf0=args.upperf0,
        dataset=args.dataset,
        speaker=args.speaker,
        rawdir=args.raw_dir,
    )
    
    # Run preparation
    prep = DataPreparation(config)
    
    if args.features_only:
        prep.create_directories()
        prep.extract_features()
    elif args.compose_only:
        prep.compose_training_data()
    elif args.lists_only:
        prep.generate_label_files()
        prep.generate_model_lists()
        prep.generate_train_scp()
        prep.generate_gen_scp()
    else:
        prep.run_all()


if __name__ == '__main__':
    main()
