#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Processing Utilities for HTS

Utilities for handling label files, feature files, and data composition.
"""

import argparse
from pathlib import Path
import struct


class LabelFileHandler:
    """Handle HTK label files (both monophone and fullcontext)"""
    
    @staticmethod
    def read_label(filepath):
        """
        Read a label file and return list of frames
        
        Format: [start_time] [end_time] [label]
        Times are in 100ns units (HTK format)
        """
        frames = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    
                    start = int(parts[0])
                    end = int(parts[1])
                    label = ' '.join(parts[2:])
                    
                    frames.append({
                        'start': start,
                        'end': end,
                        'label': label,
                        'duration': end - start
                    })
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        
        return frames
    
    @staticmethod
    def write_label(filepath, frames):
        """Write label file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for frame in frames:
                    f.write(f"{frame['start']} {frame['end']} {frame['label']}\n")
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
    
    @staticmethod
    def extract_monophone(fullcontext_label):
        """Extract monophone from fullcontext label"""
        # Format: *-phone+*
        try:
            return fullcontext_label.split('-')[1].split('+')[0]
        except:
            return fullcontext_label
    
    @staticmethod
    def convert_time(htk_time, frameshift, sampfreq):
        """Convert HTK time (100ns units) to frame index"""
        # HTK time in 100ns units, frameshift in samples, sampfreq in Hz
        return int(htk_time / (frameshift * (10000000 / sampfreq)))


class FeatureFileHandler:
    """Handle binary feature files"""
    
    @staticmethod
    def read_feature(filepath, dtype='f', dimension=None):
        """
        Read binary feature file
        
        Args:
            filepath: Path to feature file
            dtype: Data type ('f' for float, 'd' for double)
            dimension: Feature dimension (if known)
        
        Returns:
            NumPy array of shape (num_frames, dimension)
        """
        try:
            import numpy as np
            with open(filepath, 'rb') as f:
                data = f.read()
            
            if dtype == 'f':
                values = np.frombuffer(data, dtype=np.float32)
            else:
                values = np.frombuffer(data, dtype=np.float64)
            
            if dimension:
                values = values.reshape(-1, dimension)
            
            return values
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None
    
    @staticmethod
    def write_feature(filepath, data, dtype='f'):
        """
        Write binary feature file
        
        Args:
            filepath: Path to output file
            data: NumPy array
            dtype: Data type ('f' for float, 'd' for double)
        """
        try:
            import numpy as np
            with open(filepath, 'wb') as f:
                if dtype == 'f':
                    data.astype(np.float32).tofile(f)
                else:
                    data.astype(np.float64).tofile(f)
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
    
    @staticmethod
    def get_num_frames(filepath, dimension, dtype='f'):
        """Get number of frames in a feature file"""
        try:
            import os
            filesize = os.path.getsize(filepath)
            if dtype == 'f':
                bytes_per_value = 4
            else:
                bytes_per_value = 8
            
            num_values = filesize // bytes_per_value
            num_frames = num_values // dimension
            return num_frames
        except:
            return 0


class CompositFileHandler:
    """Handle composite feature files (CMP format)"""
    
    @staticmethod
    def read_htk_header(filepath):
        """
        Read HTK feature file header
        
        Returns: (nSamples, samplePeriod, sampSize, parmKind)
        """
        try:
            with open(filepath, 'rb') as f:
                header = f.read(12)
            
            nSamples = struct.unpack('>I', header[0:4])[0]
            samplePeriod = struct.unpack('>I', header[4:8])[0]
            sampSize = struct.unpack('>H', header[8:10])[0]
            parmKind = struct.unpack('>H', header[10:12])[0]
            
            return nSamples, samplePeriod, sampSize, parmKind
        except Exception as e:
            print(f"Error reading header from {filepath}: {e}")
            return None
    
    @staticmethod
    def write_htk_header(filepath, nSamples, samplePeriod, sampSize, parmKind=9):
        """Write HTK feature file header"""
        try:
            header = b''
            header += struct.pack('>I', nSamples)
            header += struct.pack('>I', samplePeriod)
            header += struct.pack('>H', sampSize)
            header += struct.pack('>H', parmKind)
            
            with open(filepath, 'wb') as f:
                f.write(header)
        except Exception as e:
            print(f"Error writing header to {filepath}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Data processing utilities for HTS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read label file
  %(prog)s read-label labels/full/utt001.lab
  
  # Convert fullcontext labels to monophone
  %(prog)s extract-mono labels/full/utt001.lab
  
  # Get feature file statistics
  %(prog)s feature-stats mgc/utt001.mgc 25
    """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Read label
    read_label_parser = subparsers.add_parser('read-label', help='Read label file')
    read_label_parser.add_argument('filepath', help='Label file path')
    
    # Extract monophone
    extract_mono_parser = subparsers.add_parser('extract-mono', help='Extract monophone from label')
    extract_mono_parser.add_argument('label', help='Fullcontext label')
    
    # Feature stats
    feature_stats_parser = subparsers.add_parser('feature-stats', help='Get feature file stats')
    feature_stats_parser.add_argument('filepath', help='Feature file path')
    feature_stats_parser.add_argument('dimension', type=int, help='Feature dimension')
    
    args = parser.parse_args()
    
    if args.command == 'read-label':
        frames = LabelFileHandler.read_label(args.filepath)
        for frame in frames:
            print(f"{frame['start']:>12d} {frame['end']:>12d} {frame['label']}")
    
    elif args.command == 'extract-mono':
        mono = LabelFileHandler.extract_monophone(args.label)
        print(f"Monophone: {mono}")
    
    elif args.command == 'feature-stats':
        num_frames = FeatureFileHandler.get_num_frames(
            args.filepath, args.dimension, dtype='f'
        )
        print(f"Feature file: {args.filepath}")
        print(f"Dimension: {args.dimension}")
        print(f"Frames: {num_frames}")
        print(f"Total values: {num_frames * args.dimension}")


if __name__ == '__main__':
    main()
