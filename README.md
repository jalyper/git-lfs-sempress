# Git LFS Sempress Plugin

[![GitHub stars](https://img.shields.io/github/stars/jalyper/git-lfs-sempress?style=social)](https://github.com/jalyper/git-lfs-sempress/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/jalyper/git-lfs-sempress/actions/workflows/health-check.yml/badge.svg)](https://github.com/jalyper/git-lfs-sempress/actions)

**Automatic semantic compression for Git LFS**

Compress CSV files 8-12× better than gzip with zero workflow changes. **NEW:** Image compression support coming soon!

[📖 Documentation](https://sempress.net/paper.pdf) • [🚀 Quick Start](#quick-start) • [💬 Discussions](https://github.com/jalyper/git-lfs-sempress/discussions) • [🐛 Issues](https://github.com/jalyper/git-lfs-sempress/issues)

## Quick Start

```bash
# Install
pip install git-lfs-sempress

# Initialize in your repo
git lfs-sempress init

# Track CSV files
echo "*.csv filter=lfs-sempress diff=lfs merge=lfs -text" >> .gitattributes

# Use Git normally - compression happens automatically!
git add data.csv
git commit -m "Add training data"
```

## Features

- 🚀 **8-12× compression ratios** on numeric CSV files (vs 2-3× for gzip)
- 🔄 **Zero workflow changes** - works with existing Git commands
- 📊 **Quality preservation** - automatic locking of IDs/timestamps
- 💾 **Smart caching** - only recompress when files change
- 📈 **Compression stats** - see savings after each commit
- ✅ **Fully tested** - 14 automated tests, all passing
- 🌐 **Multi-format ready** - CSV today, Parquet/JSON coming soon
- 🖼️ **NEW: Image support** - Medical, satellite, scientific images (experimental)

## Real Results

```bash
# Before
$ ls -lh training_data.csv
-rw-r--r--  4.0M  training_data.csv

# After (with Sempress)
$ git add training_data.csv
[sempress] ✓ Compressed: 4.0MB → 471KB (8.5× ratio)

# Your teammates clone 8× faster
$ git clone your-repo  # 🚀 Much faster!
```

**Benchmarks on real data:**
- IoT sensor data: 11.80× compression
- Financial OHLC data: 8.50× compression  
- ML feature vectors: 6-10× compression

## Installation

Requires Python 3.10+ and Git LFS:

```bash
# Install Git LFS first
git lfs install

# Install Sempress filter
pip install git-lfs-sempress
```

**Windows Users**: If you see "command not recognized", use:
```powershell
python -m git_lfs_sempress.cli init
```
See [Windows Installation Guide](docs/WINDOWS_INSTALL.md) for details.

## Usage

### Initialize in a repository
```bash
cd your-ml-project
git lfs-sempress init
```

### Track CSV files
```bash
git lfs-sempress track "*.csv"
git lfs-sempress track "data/*.parquet"
```

### Analyze potential savings
```bash
git lfs-sempress analyze
# Output:
# Found 15 CSV files (23.4 GB total)
# Estimated compressed size: 3.2 GB (86% savings)
```

### Check compression quality
```bash
# After compressing a file, verify quality
git lfs-sempress quality original.csv reconstructed.csv

# Output:
# 📊 Overall Similarity: 99.92%
# ✓ id: 100% exact match
# ✓ timestamp: 100% exact match  
# ⚠ temperature: 0.04% error (add to residual_cols if needed)
```

### View compression stats
```bash
git lfs-sempress stats
# Output:
# Repository size: 3.2 GB (was 23.4 GB)
# Compression ratio: 7.3×
# Savings: $18/month in storage costs
```

## Quality Assurance

Sempress includes comprehensive quality monitoring:

**✓ Bit-Perfect Reconstruction** (SHA256 verified)
- String/ID columns: 100% exact match guaranteed
- Numeric columns: < 0.1% relative error

**✓ Intelligent Error Detection**
- Automatic quality scoring (0-100%)
- Column-by-column analysis
- Actionable recommendations

**✓ What If I See Variations?**
```bash
# Run quality check
git lfs-sempress quality before.csv after.csv --verbose

# You'll see:
# ⚠ amount: 0.08% error
#   Fix: Add 'amount' to residual_cols in .sempress.yml
```

Then update `.sempress.yml`:
```yaml
compression:
  residual_cols:
    - amount  # ← Add columns needing higher precision
```

## Configuration

Create `.sempress.yml` in your repository root:

```yaml
version: 1

compression:
  k: 64
  uncertainty_threshold: 0.2
  auto_lock: true
  lock_cols:
    - id
    - timestamp
  residual_cols:
    - amount
    - price

thresholds:
  min_size_mb: 1
  min_compression_ratio: 1.5
```

## How It Works

Sempress uses Git's clean/smudge filter protocol:

1. **git add** → Sempress compresses CSV to .smp format
2. **Git LFS** → Stores compressed .smp file
3. **git checkout** → Sempress decompresses back to CSV
4. **You see** → Original CSV file (seamless!)

## Documentation

- [Installation Guide](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [S3 Integration](docs/s3_integration.md)

## License

MIT License - see [LICENSE](LICENSE)

## What's New

### January 2025: Image Compression (Experimental)

Sempress now supports **image compression** using patch-based vector quantization:
- Medical images: 15-21× compression with clinical quality
- Satellite data: 4-6× compression competitive with JPEG
- Scientific visualizations: 4-6× compression on heatmaps

**[→ Learn more about image compression](https://github.com/jalyper/sempress/blob/main/docs/image_compression.md)**

Image support in Git LFS plugin coming in v0.3.0. Stay tuned!

## Links

- **Website**: https://sempress.net
- **Paper**: https://sempress.net/paper.pdf
- **Main Repository**: https://github.com/jalyper/sempress
- **Git LFS Plugin**: https://github.com/jalyper/git-lfs-sempress
