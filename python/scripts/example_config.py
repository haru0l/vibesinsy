#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example HTS Training Configuration

This file demonstrates how to configure HTS training using Python.
You can use this as a template for your own configurations.
"""

# Project directory
prjdir = '/workspaces/nit070/python'

# Question set and version numbers
qnum = '001'
ver = '001'

# ====================================================
# Model Structure
# ====================================================

# Number of HMM states (excluding initial and final states)
nState = 5

# Set types (component and duration)
SET = ['cmp', 'dur']

# Component types (acoustic features)
cmp = ['mgc', 'lf0', 'bap']

# Duration types
dur = ['dur']

# Stream boundaries for each component
strb = {
    'mgc': 0,
    'lf0': 25,
    'bap': 26,
}

# Stream end indices
stre = {
    'mgc': 24,
    'lf0': 25,
    'bap': 30,
}

# Stream weights
strw = {
    'mgc': 1.0,
    'lf0': 1.0,
    'bap': 1.0,
}

# Multi-Space Probability Distribution (MSD) info
msdi = {
    'mgc': 0,  # 0: non-MSD, 1: MSD
    'lf0': 1,
    'bap': 0,
}

# ====================================================
# Feature Parameters
# ====================================================

# Sampling rate (Hz)
sr = 16000

# Frame shift (samples)
fs = 80

# Frame period in ms
fp = int(fs * 1000 / sr)

# Frequency warping coefficient
fw = 0.58

# Gamma value for LSP (0 = MCP, non-zero = LSP)
gm = 0

# Log gain flag (1: with log gain, 0: without)
lg = 1

# ====================================================
# Stream Orders and Windows
# ====================================================

# Order of each acoustic feature stream
ordr = {
    'mgc': 25,  # Mel-cepstral order + 1
    'lf0': 1,
    'bap': 5,   # Band-aperiodicity order + 1
    'dur': 1,
}

# Number of windows for each stream
nwin = {
    'mgc': 3,
    'lf0': 3,
    'bap': 3,
}

# ====================================================
# Reference Set Names (for duration models)
# ====================================================

# Reference mapping from acoustic to duration models
ref = {
    'cmp': ['mgc', 'lf0', 'bap'],
    'dur': ['dur'],
}

# Type to set mapping (for decision tree clustering)
t2s = {
    'mgc': 'cmp',
    'lf0': 'cmp',
    'bap': 'cmp',
    'dur': 'dur',
}

# ====================================================
# Model Tying Configuration
# ====================================================

# Minimum number of observations to form leaf node
mocc = {
    'mgc': 10,
    'lf0': 10,
    'bap': 10,
    'dur': 10,
}

# Decision tree clustering threshold
thr = {
    'mgc': '250',
    'lf0': '250',
    'bap': '250',
}

# Global variance clustering threshold
gvthr = {
    'mgc': '100',
    'lf0': '100',
    'bap': '100',
}

# ====================================================
# Variance Floor Configuration
# ====================================================

# Variance floor values
vflr = {
    'mgc': 0.6,
    'lf0': 0.6,
    'bap': 0.6,
    'dur': 0.6,
}

# ====================================================
# Training Parameters
# ====================================================

# Number of iterations for embedded re-estimation
nIte = 10

# Maximum standard deviation coefficient
maxdev = 7.0

# Minimum duration
mindur = 5

# Initial duration mean
initdurmean = 3.0

# Initial duration variance
initdurvari = 10.0

# DAEM (deterministic annealing EM) iterations
daem = 4
daem_nIte = 10
daem_alpha = 1.0

# Enable duration-consistent global variance (GV)
cdgv = 1

# ====================================================
# Global Variance (GV) Configuration
# ====================================================

# Use global variance in training
useGV = 1

# GV weight
gvWeight = 1.0

# HMM weight
hmmWeight = 1.0

# Optimization criterion (ALGOPT_GV or ALGOPT_NEWTON)
optKind = 'ALGOPT_GV'

# Maximum EM iterations for GV
maxGViter = 200

# EM epsilon for GV
GVepsilon = 0.0000001

# Minimum Euclidean norm
minEucNorm = 0.01

# Step size initialization
stepInit = 1.0

# Step size increase rate
stepInc = 1.2

# Step size decrease rate
stepDec = 0.5

# Silence phones (for GV off in silence)
nosilgv = 1
slnt = ['pau', 'sil']

# ====================================================
# Semi-Tied Covariance (STC) Configuration
# ====================================================

# Number of blocks for semi-tied covariance
nblk = {
    'mgc': 1,
    'lf0': 1,
    'bap': 1,
}

# Bandwidth for semi-tied covariance
band = {
    'mgc': 25,  # Same as order
    'lf0': 1,
    'bap': 5,
}

# ====================================================
# Postfilter Configuration
# ====================================================

# Postfilter coefficient for MCP
pf_mcp = 1.0

# Postfilter coefficient for LSP
pf_lsp = 1.0

# ====================================================
# Modulation Spectrum-based Postfilter (MSPF)
# ====================================================

# Enable MSPF
useMSPF = 0

# MSPF parameters
mspfLength = 21
mspfFFTLen = 256

# Modulation spectrum energy
mspfe = {
    'mgc': 2.0,
}

# Modulation spectrum gamma (weight)
mspfgam = {
    'mgc': 0.0,
}

# ====================================================
# EM Algorithm Configuration
# ====================================================

# Maximum EM iterations
maxEMiter = 20

# EM epsilon (convergence threshold)
EMepsilon = 0.0000001

# ====================================================
# Miscellaneous Settings
# ====================================================

# Full-context label format version
fclf = 'HTS_TTS'
fclv = '0.0'

# Use STRAIGHT for vocoder
usestraight = 0

# ====================================================
# Execution Flags
# ====================================================
# Set these to 1 to enable the following stages:

# Make environments (directories and config files)
MKEMV = 1

# Compute variance floors
HCMPV = 1

# Initialization and re-estimation
IN_RE = 1

# Make monophone MMF file
MMMMF = 1

# Embedded re-estimation (monophone)
ERST0 = 1

# Monophone to fullcontext conversion
MN2FL = 1

# Embedded re-estimation (fullcontext)
ERST1 = 1

# Tree-based context clustering
CXCL1 = 1

# Embedded re-estimation (clustered)
ERST2 = 1

# Untie parameter sharing structure
UNTIE = 1

# Embedded re-estimation (untied)
ERST3 = 1

# Second tree-based clustering
CXCL2 = 1

# Embedded re-estimation (re-clustered)
ERST4 = 1

# Forced alignment for GV
FALGN = 1

# Make global variance models
MCDGV = 1

# HHEd for unseen models (GV)
MKUSGV = 1

# HMGenS for parameter generation (1mix)
PGEN1 = 1

# Waveform generation (1mix)
WGEN1 = 1

# HHEd for increasing mixture (1mix -> 2mix)
MKUPMX = 1

# HERest for re-estimation (2mix)
ERST2MX = 1

# HHEd for unseen models (2mix)
MKUS2MX = 1

# HMGenS for parameter generation (2mix)
PGEN2 = 1

# Waveform generation (2mix)
WGEN2 = 1

# Semi-tied covariance matrices
STC = 0

# ====================================================
# HTS Command Paths
# ====================================================
# These should be set to point to your HTS installation

HCOMPV = 'HCompV'
HLIST = 'HList'
HINIT = 'HInit'
HREST = 'HRest'
HEREST = 'HERest'
HHED = 'HHEd'
HSMMALIGN = 'HSMMAlign'
HMGENS = 'HMGenS'

# SPTK commands
X2X = 'x2x'
VOPR = 'vopr'
SOPR = 'sopr'
VSTAT = 'vstat'
VSUM = 'vsum'
BCUT = 'bcut'
MERGE = 'merge'
BCP = 'bcp'
LSPCHECK = 'lspcheck'
LSP2LPC = 'lsp2lpc'
MGC2MGC = 'mgc2mgc'
MGC2SP = 'mgc2sp'
FREQT = 'freqt'
C2ACR = 'c2acr'
MC2B = 'mc2b'
B2MC = 'b2mc'
EXCITE = 'excite'
DFS = 'dfs'
MGLSADF = 'mglsadf'
RAW2WAV = 'raw2wav'
WINDOW = 'window'
FRAME = 'frame'
SPEC = 'spec'
IFFTR = 'ifftr'
PHASE = 'phase'
NAN = 'nan'
WC = 'wc'

# Perl interpreter (for backward compatibility)
PERL = 'perl'

# MATLAB (for STRAIGHT vocoder)
MATLAB = 'matlab'

# ====================================================
# Data Type Mappings
# ====================================================

# Acoustic model data type mapping
t2s = {
    'mgc': 'cmp',
    'lf0': 'cmp',
    'bap': 'cmp',
    'dur': 'dur',
}

# Global variance data type mapping
gvt = {
    'mgc': 'cmp',
    'lf0': 'cmp',
    'bap': 'cmp',
}

# ====================================================
# End of Configuration
# ====================================================
# This configuration file completes the setup for HTS training.
# Modify parameters as needed for your specific project.
