#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Validation and Quality Check Tool

Validates that data preparation has completed successfully and all files
have correct dimensions and structure.
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict


class DataValidator:
    """Validate prepared data for HTS training"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate_all(self):
        """Run all validation checks"""
        self.check_directories()
        self.check_feature_files()
        self.check_label_files()
        self.check_list_files()
        self.check_scp_files()
        return self.get_report()
    
    def check_directories(self):
        """Check that required directories exist"""
        required = ['mgc', 'lf0', 'cmp', 'labels/mono', 'labels/full', 'lists', 'scp']
        
        for subdir in required:
            path = self.data_dir / subdir
            if not path.exists():
                self.errors.append(f"Missing directory: {subdir}")
            else:
                self.info.append(f"✓ Found {subdir}/")
    
    def check_feature_files(self):
        """Check feature files exist and have consistent dimensions"""
        feature_types = {
            'mgc': 26,      # MGC order 25 + c0
            'lf0': 1,
            'cmp': 33,      # Example: 26+1+6
        }
        
        for ftype, expected_dim in feature_types.items():
            path = self.data_dir / ftype
            if not path.exists():
                continue
            
            files = sorted(path.glob('*.{}' .format(ftype)))
            if not files:
                self.warnings.append(f"No {ftype} files found in {ftype}/")
                continue
            
            self.info.append(f"\nChecking {ftype} features ({len(files)} files):")
            
            # Check a sample
            for sample_file in files[:min(3, len(files))]:
                try:
                    num_frames = self.get_num_frames(sample_file, expected_dim)
                    self.info.append(f"  {sample_file.name}: {num_frames} frames")
                except Exception as e:
                    self.errors.append(f"Error reading {sample_file}: {e}")
    
    def check_label_files(self):
        """Check label files exist and are valid"""
        label_types = ['mono', 'full']
        
        for ltype in label_types:
            path = self.data_dir / 'labels' / ltype
            if not path.exists():
                self.warnings.append(f"Missing label directory: labels/{ltype}/")
                continue
            
            files = list(path.glob('*.lab'))
            if not files:
                self.warnings.append(f"No {ltype} label files found")
                continue
            
            self.info.append(f"\n{ltype} labels: {len(files)} files")
            
            # Validate first file
            try:
                sample = files[0]
                with open(sample, 'r') as f:
                    lines = f.readlines()
                if not lines:
                    self.errors.append(f"{ltype} label file is empty: {sample}")
                else:
                    self.info.append(f"  {sample.name}: {len(lines)} labels")
            except Exception as e:
                self.errors.append(f"Error reading {ltype} label: {e}")
    
    def check_list_files(self):
        """Check model list files"""
        self.info.append("\nChecking model lists:")
        
        for list_file in ['train.list', 'all.list']:
            path = self.data_dir / 'lists' / list_file
            if not path.exists():
                self.warnings.append(f"Missing list file: {list_file}")
                continue
            
            try:
                with open(path, 'r') as f:
                    lines = [l.strip() for l in f if l.strip()]
                self.info.append(f"  {list_file}: {len(lines)} models")
            except Exception as e:
                self.errors.append(f"Error reading {list_file}: {e}")
        
        # Check MLF files
        for mlf_file in ['mono.mlf', 'full.mlf']:
            path = self.data_dir / 'labels' / mlf_file
            if not path.exists():
                self.warnings.append(f"Missing MLF file: {mlf_file}")
                continue
            
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                # Count utterances (lines starting with ")
                utts = len([l for l in lines if l.startswith('"')])
                self.info.append(f"  {mlf_file}: {utts} utterances")
            except Exception as e:
                self.errors.append(f"Error reading {mlf_file}: {e}")
    
    def check_scp_files(self):
        """Check SCP (script) files"""
        self.info.append("\nChecking SCP files:")
        
        for scp_file in ['train.scp', 'gen.scp']:
            path = self.data_dir / 'scp' / scp_file
            if not path.exists():
                self.warnings.append(f"Missing SCP file: {scp_file}")
                continue
            
            try:
                with open(path, 'r') as f:
                    lines = [l.strip() for l in f if l.strip()]
                self.info.append(f"  {scp_file}: {len(lines)} entries")
            except Exception as e:
                self.errors.append(f"Error reading {scp_file}: {e}")
    
    @staticmethod
    def get_num_frames(filepath, dimension):
        """Calculate number of frames in a binary feature file"""
        import os
        filesize = os.path.getsize(filepath)
        bytes_per_value = 4  # float32
        num_values = filesize // bytes_per_value
        return num_values // dimension if dimension > 0 else 0
    
    def get_report(self):
        """Generate validation report"""
        report = []
        
        if not self.errors and not self.warnings:
            report.append("✓ Data validation PASSED")
        elif self.errors:
            report.append("✗ Data validation FAILED")
        else:
            report.append("⚠ Data validation completed with warnings")
        
        if self.info:
            report.append("\nInfo:")
            report.extend(self.info)
        
        if self.warnings:
            report.append("\nWarnings:")
            for w in self.warnings:
                report.append(f"  ⚠ {w}")
        
        if self.errors:
            report.append("\nErrors:")
            for e in self.errors:
                report.append(f"  ✗ {e}")
        
        return '\n'.join(report)


class FeatureStatistics:
    """Compute statistics on prepared features"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
    
    def compute_stats(self, feature_type='mgc', max_files=None):
        """Compute statistics for a feature type"""
        try:
            import numpy as np
        except ImportError:
            print("NumPy required for statistics. Install with: pip install numpy")
            return None
        
        path = self.data_dir / feature_type
        if not path.exists():
            print(f"Feature directory not found: {feature_type}")
            return None
        
        files = sorted(path.glob(f'*.{feature_type}'))
        if not files:
            print(f"No {feature_type} files found")
            return None
        
        if max_files:
            files = files[:max_files]
        
        all_frames = []
        
        for ffile in files:
            try:
                with open(ffile, 'rb') as f:
                    data = np.frombuffer(f.read(), dtype=np.float32)
                all_frames.extend(data)
            except Exception as e:
                print(f"Error reading {ffile}: {e}")
        
        if not all_frames:
            return None
        
        all_frames = np.array(all_frames)
        
        stats = {
            'count': len(all_frames),
            'mean': float(np.mean(all_frames)),
            'std': float(np.std(all_frames)),
            'min': float(np.min(all_frames)),
            'max': float(np.max(all_frames)),
            'files': len(files),
        }
        
        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Validate and check prepared HTS data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all data
  %(prog)s validate
  
  # Compute MGC statistics
  %(prog)s stats --type mgc
  
  # Compute statistics on limited files
  %(prog)s stats --type cmp --max-files 100
    """
    )
    
    parser.add_argument('--data-dir', default='data', help='Data directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate data preparation')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Compute feature statistics')
    stats_parser.add_argument('--type', default='mgc', help='Feature type')
    stats_parser.add_argument('--max-files', type=int, help='Limit number of files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'validate':
        validator = DataValidator(args.data_dir)
        print(validator.validate_all())
        return 0 if not validator.errors else 1
    
    elif args.command == 'stats':
        stats_tool = FeatureStatistics(args.data_dir)
        stats = stats_tool.compute_stats(args.type, args.max_files)
        
        if stats:
            print(f"\nStatistics for {args.type}:")
            print(f"  Files: {stats['files']}")
            print(f"  Total values: {stats['count']}")
            print(f"  Mean: {stats['mean']:.6f}")
            print(f"  Std: {stats['std']:.6f}")
            print(f"  Min: {stats['min']:.6f}")
            print(f"  Max: {stats['max']:.6f}")
        return 0
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
