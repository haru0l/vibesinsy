#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTS Data Makefile - Python replacement for Makefile.in

This script provides Make-like targets for data preparation using Python.
Usage: python3 makefile.py [target]

Targets:
  all        - Complete pipeline (analysis + labels)
  analysis   - Feature extraction (features + cmp)
  labels     - Label generation (mlf + list + scp)
  features   - Extract acoustic features
  cmp        - Compose training data files
  mlf        - Generate MLF files
  list       - Generate model list files
  scp        - Generate SCP script files
  clean      - Remove generated files
  clean-mgc  - Remove MGC files
  clean-lf0  - Remove LF0 files
  clean-bap  - Remove BAP files
  clean-cmp  - Remove CMP files
  clean-mlf  - Remove MLF files
  clean-list - Remove list files
  clean-scp  - Remove SCP files
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


class MakefileWrapper:
    """Python replacement for Makefile targets"""
    
    def __init__(self, configfile=None):
        self.config = self._load_config(configfile)
        self.data_prep_script = 'data_preparation.py'
    
    def _load_config(self, configfile):
        """Load configuration from file"""
        config = {
            'SPEAKER': 'speaker',
            'DATASET': 'dataset',
            'SAMPFREQ': 16000,
            'FRAMELEN': 400,
            'FRAMESHIFT': 80,
            'FFTLEN': 512,
            'MGCORDER': 25,
            'BAPORDER': 5,
            'FREQWARP': 0.58,
            'GAMMA': 0,
            'LOWERF0': 40,
            'UPPERF0': 400,
            'LNGAIN': 0,
            'USESTRAIGHT': 0,
            'NMGCWIN': 3,
            'NLF0WIN': 3,
            'NBAPWIN': 3,
            'WINDOWTYPE': 2,
            'NORMALIZE': 2,
        }
        
        if configfile and os.path.exists(configfile):
            with open(configfile, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if value.isdigit():
                            config[key] = int(value)
                        else:
                            config[key] = value
        
        return config
    
    def run_target(self, target):
        """Run a make target"""
        if hasattr(self, f'target_{target}'):
            getattr(self, f'target_{target}')()
        else:
            print(f"Error: Unknown target '{target}'")
            self.show_help()
            sys.exit(1)
    
    def target_all(self):
        """Build all targets"""
        self.target_analysis()
        self.target_labels()
    
    def target_analysis(self):
        """Extract features and compose data"""
        self.target_features()
        self.target_cmp()
    
    def target_labels(self):
        """Generate label-related files"""
        self.target_mlf()
        self.target_list()
        self.target_scp()
    
    def target_features(self):
        """Extract acoustic features"""
        cmd = self._build_command(['--features-only'])
        self._run_command(cmd)
    
    def target_cmp(self):
        """Compose training data files"""
        cmd = self._build_command(['--compose-only'])
        self._run_command(cmd)
    
    def target_mlf(self):
        """Generate MLF files"""
        cmd = self._build_command(['--lists-only'])
        self._run_command(cmd)
    
    def target_list(self):
        """Generate model list files"""
        cmd = self._build_command(['--lists-only'])
        self._run_command(cmd)
    
    def target_scp(self):
        """Generate SCP script files"""
        cmd = self._build_command(['--lists-only'])
        self._run_command(cmd)
    
    def _build_command(self, extra_args=None):
        """Build data_preparation.py command"""
        cmd = [
            'python3', self.data_prep_script,
            '--sampfreq', str(self.config['SAMPFREQ']),
            '--framelen', str(self.config['FRAMELEN']),
            '--frameshift', str(self.config['FRAMESHIFT']),
            '--fftlen', str(self.config['FFTLEN']),
            '--mgcorder', str(self.config['MGCORDER']),
            '--baporder', str(self.config['BAPORDER']),
            '--freqwarp', str(self.config['FREQWARP']),
            '--gamma', str(self.config['GAMMA']),
            '--lowerf0', str(self.config['LOWERF0']),
            '--upperf0', str(self.config['UPPERF0']),
            '--dataset', self.config['DATASET'],
            '--speaker', self.config['SPEAKER'],
        ]
        if extra_args:
            cmd.extend(extra_args)
        return cmd
    
    def _run_command(self, cmd):
        """Execute a command"""
        import subprocess
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Error: Command failed with code {result.returncode}")
            sys.exit(1)
    
    def target_clean(self):
        """Remove all generated files"""
        self.target_clean_mgc()
        self.target_clean_lf0()
        self.target_clean_bap()
        self.target_clean_cmp()
        self.target_clean_mlf()
        self.target_clean_list()
        self.target_clean_scp()
    
    def target_clean_mgc(self):
        """Remove MGC files"""
        self._remove_dir('mgc')
    
    def target_clean_lf0(self):
        """Remove LF0 files"""
        self._remove_dir('lf0')
    
    def target_clean_bap(self):
        """Remove BAP files"""
        self._remove_dir('bap')
    
    def target_clean_cmp(self):
        """Remove CMP files"""
        self._remove_dir('cmp')
    
    def target_clean_mlf(self):
        """Remove MLF files"""
        mlf_dir = Path('labels')
        for mlf in mlf_dir.glob('*.mlf'):
            mlf.unlink()
            print(f"Removed: {mlf}")
    
    def target_clean_list(self):
        """Remove list files"""
        self._remove_dir('lists')
    
    def target_clean_scp(self):
        """Remove SCP files"""
        self._remove_dir('scp')
    
    def _remove_dir(self, dirname):
        """Remove a directory and its contents"""
        path = Path(dirname)
        if path.exists():
            shutil.rmtree(path)
            print(f"Removed: {dirname}/")
    
    def show_help(self):
        """Show usage information"""
        print(__doc__)


def main():
    parser = argparse.ArgumentParser(
        description='HTS Data Makefile - Python replacement for Makefile.in',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('target', nargs='?', default='all',
                       help='Target to build (default: all)')
    parser.add_argument('-c', '--config', help='Configuration file')
    parser.add_argument('--help-targets', action='store_true', 
                       help='Show available targets')
    
    args = parser.parse_args()
    
    makefile = MakefileWrapper(args.config)
    
    if args.help_targets:
        makefile.show_help()
    else:
        makefile.run_target(args.target)


if __name__ == '__main__':
    main()
