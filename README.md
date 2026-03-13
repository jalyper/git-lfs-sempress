# git-lfs-sempress

**Automatic semantic compression for CSV files in Git repositories**

[![PyPI](https://img.shields.io/pypi/v/git-lfs-sempress)](https://pypi.org/project/git-lfs-sempress/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A Git LFS clean/smudge filter that compresses CSV files 8-12x using [sempress](https://pypi.org/project/sempress/) vector quantization. Zero workflow changes -- just `git add` and `git commit` as usual.

## Quick Start

```bash
# Install Git LFS first
git lfs install

# Install the plugin
pip install git-lfs-sempress

# Initialize in your repo
git lfs-sempress init

# Track CSV files
echo "*.csv filter=lfs-sempress diff=lfs merge=lfs -text" >> .gitattributes

# Use Git normally - compression happens automatically
git add data.csv
git commit -m "Add training data"
```

## How It Works

1. **`git add`** -- Sempress compresses CSV to `.smp` format (clean filter)
2. **Git LFS** -- stores the compressed blob
3. **`git checkout`** -- Sempress decompresses back to CSV (smudge filter)
4. **You see** -- the original CSV file, seamlessly

## Compression Results

```
$ git add training_data.csv
[sempress] Compressed: 4.0MB -> 471KB (8.5x ratio)
```

Typical ratios on real data:
- IoT sensor data: **11.8x**
- Financial OHLC: **8.5x**
- ML feature vectors: **6-10x**

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

## Commands

```bash
git lfs-sempress init              # Set up filter in current repo
git lfs-sempress track "*.csv"     # Add tracking pattern
git lfs-sempress analyze           # Estimate savings for existing files
git lfs-sempress stats             # Show compression stats for repo
git lfs-sempress quality a.csv b.csv  # Compare original vs reconstructed
```

## Quality Assurance

- **String/ID columns**: 100% exact match (automatically locked)
- **Numeric columns**: < 0.1% relative error by default
- **Residual columns**: bit-perfect reconstruction

If a column needs higher precision, add it to `residual_cols` in `.sempress.yml`.

## Installation Notes

**Windows**: If `git lfs-sempress` isn't recognized, use:
```powershell
python -m git_lfs_sempress.cli init
```

## Links

- [sempress library](https://pypi.org/project/sempress/) -- the underlying compression engine
- [Research paper](https://sempress.net/paper.pdf) -- technical details

## License

MIT License - see [LICENSE](LICENSE)
