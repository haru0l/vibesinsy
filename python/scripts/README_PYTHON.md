# HTS Training Script - Python Version

This is a complete Python port of the HMM-Based Speech Synthesis System (HTS) training script originally written in Perl.

## Overview

The HTS Training Script is designed to automate the training process for speech synthesis systems based on Hidden Markov Models (HMMs). This Python version maintains compatibility with the original workflow while providing cleaner code organization and better maintainability.

## Features

- **Full Feature Parity**: All functionality from the original Perl script is implemented
- **Modular Design**: Separate modules for configuration, utilities, and main training logic
- **Python 3 Compatible**: Uses modern Python 3 idioms and libraries
- **Cross-Platform**: Works on Linux, macOS, and Windows with proper shells
- **Configuration Flexibility**: Multiple configuration loading options (Perl .pm, Python, JSON)

## Requirements

- Python 3.7+
- HTS toolkit and dependencies installed
- pysptk - Python wrapper for SPTK (for feature extraction)
- scipy - Scientific Python library (for audio I/O)
- numpy - Numerical Python library
- Perl (optional, for some utility scripts)

## Installation

1. Ensure Python 3.7+ is installed:
   ```bash
   python3 --version
   ```

2. Place the Python scripts in your HTS project:
   ```bash
   cp Training.py /path/to/project/scripts/
   cp config_loader.py /path/to/project/scripts/
   ```

3. Make the main script executable:
   ```bash
   chmod +x /path/to/project/scripts/Training.py
   ```

## Usage

### Basic Usage

```bash
python3 Training.py Config.pm
```

Or with the original Perl-style invocation:

```bash
./Training.py Config.pm
```

### Configuration

The script accepts configuration in multiple formats:

#### 1. Perl Config Module (.pm format)

Create a `Config.pm` file with configuration variables:

```perl
$prjdir = '/path/to/project';
$qnum = '001';
$ver = '001';
$nState = 5;
$sr = 16000;
$fs = 80;
$fw = 0.58;

@SET = ('cmp', 'dur');
@cmp = ('mgc', 'lf0', 'bap');
@dur = ('dur');

%ordr = (
    'mgc' => 25,
    'lf0' => 1,
    'bap' => 5,
    'dur' => 1,
);
```

#### 2. Python Configuration Module

Create a `config.py` file:

```python
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

ordr = {
    'mgc': 25,
    'lf0': 1,
    'bap': 5,
    'dur': 1,
}
```

#### 3. Using ConfigBuilder

```python
from config_loader import ConfigBuilder

builder = ConfigBuilder('/path/to/project', qnum='001', ver='001')
builder.set_model_params(nstate=5, cmp_types=['mgc', 'lf0', 'bap'])
builder.set_stream_params(sr=16000, fs=80, fw=0.58)
builder.set_flags(MKEMV=True, HCMPV=True, IN_RE=True)

config = builder.build()
```

## Module Structure

### Training.py

Main training script containing:
- Core training functions
- File I/O operations
- Directory management
- Shell command execution
- HTS workflow orchestration

Key functions:
- `shell()` - Execute shell commands with error handling
- `print_time()` - Print timestamped progress messages
- `make_proto()` - Generate prototype models
- `make_config()` - Generate configuration files
- `make_edfile_*()` - Generate HTS editor files
- `gen_wave()` - Generate waveforms from parameters
- `main()` - Main training workflow

### config_loader.py

Configuration management module containing:
- `ConfigLoader` - Load configurations from various formats
- `ConfigBuilder` - Programmatically build configurations
- Configuration validation and export functions

## Workflow

The training process follows these main stages:

1. **Environment Preparation** (MKEMV)
   - Create necessary directories
   - Generate configuration files
   - Create prototype models

2. **Variance Floor Computation** (HCMPV)
   - Compute variance floors from data
   - Initialize models

3. **Initialization & Re-estimation** (IN_RE)
   - Initialize models with data
   - Re-estimate parameters

4. **Monophone Training** (ERST0)
   - Embedded re-estimation for monophone models

5. **Fullcontext Conversion** (MN2FL)
   - Convert monophone models to fullcontext

6. **Fullcontext Re-estimation** (ERST1)
   - Re-estimate fullcontext models

7. **Tree-based Clustering** (CXCL1)
   - Perform decision tree-based clustering

8. **Further Re-estimation** (ERST2, ERST3, ERST4)
   - Additional re-estimation rounds

9. **Global Variance Training** (MCDGV)
   - Train global variance models

10. **Waveform Generation** (WGEN, WGEN1, WGEN2)
    - Generate synthesized waveforms

## Environment Variables

The script uses the following environment variables from the HTS toolkit:

- `HCOMPV` - HCompV command path
- `HLIST` - HList command path
- `HINIT` - HInit command path
- `HREST` - HRest command path
- `HEREST` - HERest command path
- `HHED` - HHEd command path
- `HSMMALIGN` - HSMMAlign command path
- `HMGENS` - HMGenS command path
- SPTK and other utility tools

## Key Differences from Perl Version

1. **Module System**: Uses Python modules instead of Perl packages
2. **String Handling**: Native Python string handling vs Perl regex
3. **Hash/Array Operations**: Python dict/list instead of Perl hashes/arrays
4. **File I/O**: Python's pathlib for cross-platform compatibility
5. **Error Handling**: Python exceptions vs Perl die statements
6. **Regular Expressions**: Python re module instead of Perl regexes

## Configuration Parameters

### Model Structure

- `nState`: Number of HMM states (default: 5)
- `cmp`: Compression types (e.g., ['mgc', 'lf0', 'bap'])
- `dur`: Duration types (e.g., ['dur'])
- `ordr`: Order of each stream

### Training Parameters

- `sr`: Sampling rate (Hz)
- `fs`: Frame shift (samples)
- `fw`: Frequency warping factor
- `gm`: Gamma for LSP (0 = MCP, non-zero = LSP)
- `vflr`: Variance floor values

### Execution Flags

- `MKEMV`: Make environments (1=yes, 0=no)
- `HCMPV`: Compute variance floors
- `IN_RE`: Initialization and re-estimation
- `MMMMF`: Make monophone MMF
- `ERST0-4`: Re-estimation iterations
- `MN2FL`: Monophone to fullcontext conversion
- `CXCL1-2`: Context clustering iterations
- `MCDGV`: Make global variance models
- `WGEN*`: Waveform generation

## Troubleshooting

### Command Not Found Errors

Ensure HTS tools are installed and in your PATH:

```bash
export PATH=$PATH:/path/to/hts/bin
```

### Configuration Loading Errors

Check that the configuration file exists and has correct syntax:

```python
from config_loader import ConfigLoader
loader = ConfigLoader()
config = loader.load_from_perl('Config.pm')
loader.validate()
```

### Directory Permission Errors

Ensure write permissions in the project directory:

```bash
chmod -R 755 /path/to/project
```

## Migration from Perl

To migrate existing Perl-based HTS projects:

1. Keep existing `Config.pm` file or convert to Python format
2. Replace `Training.pl` with `Training.py`
3. Update shell commands if using non-standard HTS tools
4. Test with a sample configuration before full training

## Performance Considerations

- Python subprocess overhead for HTS tool calls is minimal
- Regular expression performance is comparable to Perl
- File I/O is faster with pathlib than manual string concatenation

## Contributing

To enhance the Python version:

1. Follow PEP 8 style guidelines
2. Add type hints for function arguments
3. Include docstrings for all functions
4. add unit tests for critical functions
5. Update documentation with changes

## License

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the conditions in the header of this file are met.

See the LICENSE file in the main HTS toolkit directory for full details.

## References

- HTS Working Group: http://hts.sp.nitech.ac.jp/
- Python HMM Implementation: https://docs.python.org/3/
- SPTK Documentation: https://sp-tk.sourceforge.io/

## Support

For issues or questions:
1. Check the HTS documentation
2. Review the original Perl script logic
3. Consult the configuration examples
4. Check Python error messages and stack traces

## Version History

- v1.0.0 - Initial Python port from Training.pl
  - Full feature parity with original Perl script
  - Modular configuration system
  - Cross-platform compatibility
