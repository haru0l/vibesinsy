#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration loader for HTS Training Script

This module provides utilities for loading and managing HTS training configuration.
"""

import os
import re
from pathlib import Path


class ConfigLoader:
    """Load and parse HTS configuration from Config.pm or Python dict"""
    
    def __init__(self):
        self.config = {}
    
    def load_from_perl(self, config_file):
        """Load configuration from Perl Config.pm file"""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract scalar variables
        scalar_pattern = r'\$(\w+)\s*=\s*[\'"]?([^\'";\n]*)[\'"]?;'
        for match in re.finditer(scalar_pattern, content):
            var_name, var_value = match.groups()
            self.config[var_name] = var_value.strip()
        
        # Extract array variables
        array_pattern = r'@(\w+)\s*=\s*\((.*?)\);'
        for match in re.finditer(array_pattern, content, re.DOTALL):
            var_name, var_content = match.groups()
            items = re.findall(r'[\'"]([^\'"]*)[\'"]', var_content)
            self.config[var_name] = items
        
        # Extract hash variables
        hash_pattern = r'%(\w+)\s*=\s*\((.*?)\);'
        for match in re.finditer(hash_pattern, content, re.DOTALL):
            var_name, var_content = match.groups()
            hash_dict = {}
            items = re.findall(r'[\'"]([^\'"]*)[\'"]', var_content)
            for i in range(0, len(items), 2):
                if i + 1 < len(items):
                    hash_dict[items[i]] = items[i + 1]
            self.config[var_name] = hash_dict
        
        return self.config
    
    def load_from_dict(self, config_dict):
        """Load configuration from a Python dictionary"""
        self.config.update(config_dict)
        return self.config
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def get_all(self):
        """Get all configuration"""
        return self.config
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def validate(self):
        """Validate required configuration keys"""
        required_keys = [
            'prjdir', 'qnum', 'ver', 'nState', 'ordr', 
            'cmp', 'dur', 'nwin', 'fw', 'sr', 'fs'
        ]
        
        for key in required_keys:
            if key not in self.config:
                print(f"Warning: Required configuration '{key}' not found")
        
        return True


class ConfigBuilder:
    """Build configuration for HTS training"""
    
    def __init__(self, project_dir, qnum='001', ver='001'):
        self.project_dir = project_dir
        self.qnum = qnum
        self.ver = ver
        self.config = {
            'prjdir': project_dir,
            'qnum': qnum,
            'ver': ver,
        }
    
    def set_model_params(self, nstate=5, cmp_types=None, dur_types=None):
        """Set model parameters"""
        if cmp_types is None:
            cmp_types = ['mgc', 'lf0', 'bap']
        if dur_types is None:
            dur_types = ['dur']
        
        self.config['nState'] = nstate
        self.config['cmp'] = cmp_types
        self.config['dur'] = dur_types
        return self
    
    def set_stream_params(self, **kwargs):
        """Set stream parameters"""
        for key, value in kwargs.items():
            self.config[key] = value
        return self
    
    def set_hts_commands(self, **kwargs):
        """Set HTS tool command paths"""
        for key, value in kwargs.items():
            self.config[key] = value
        return self
    
    def set_flags(self, **kwargs):
        """Set execution flags (MKEMV, HCMPV, IN_RE, etc.)"""
        for key, value in kwargs.items():
            self.config[key] = value
        return self
    
    def build(self):
        """Build and return configuration dictionary"""
        return self.config
    
    def to_dict(self):
        """Export configuration as dictionary"""
        return self.config.copy()
    
    def to_perl_format(self, output_file):
        """Export configuration in Perl format"""
        with open(output_file, 'w') as f:
            f.write("#!/usr/bin/perl\n")
            f.write("# Auto-generated HTS training configuration\n\n")
            
            # Write scalars
            for key, value in self.config.items():
                if isinstance(value, (int, float, bool)):
                    f.write(f"${key} = {value};\n")
                elif isinstance(value, str):
                    f.write(f"${key} = '{value}';\n")
            
            # Write arrays
            for key, value in self.config.items():
                if isinstance(value, list):
                    items = "', '".join(str(v) for v in value)
                    f.write(f"@{key} = ('{items}');\n")
            
            # Write hashes
            for key, value in self.config.items():
                if isinstance(value, dict):
                    items = ", ".join(f"'{k}' => '{v}'" for k, v in value.items())
                    f.write(f"%{key} = ({items});\n")
            
            f.write("\n1;\n")


def load_config(config_file):
    """
    Load configuration from file
    
    Args:
        config_file: Path to configuration file (Perl or Python format)
    
    Returns:
        Dictionary of configuration variables
    """
    loader = ConfigLoader()
    
    if config_file.endswith('.pm'):
        # Perl module format
        return loader.load_from_perl(config_file)
    else:
        # Try to load as Python module or JSON
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_file)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            return loader.load_from_dict(vars(config_module))
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}


if __name__ == '__main__':
    # Example usage
    builder = ConfigBuilder('/path/to/project', qnum='001', ver='001')
    builder.set_model_params(nstate=5, cmp_types=['mgc', 'lf0', 'bap'])
    builder.set_stream_params(sr=16000, fs=80, fw=0.58)
    
    config = builder.build()
    print("Configuration built:")
    for key, value in config.items():
        print(f"  {key}: {value}")
