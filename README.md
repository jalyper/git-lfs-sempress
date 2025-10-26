# Git LFS Sempress Plugin

**Automatic semantic compression for Git LFS**

Compress CSV files 5-8× better than gzip with zero workflow changes.

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

- 🚀 **5-8× compression ratios** on numeric CSV files
- 🔄 **Zero workflow changes** - works with existing Git commands
- 📊 **Quality preservation** - automatic locking of IDs/timestamps
- 💾 **Smart caching** - only recompress when files change
- 📈 **Compression stats** - see savings after each commit

## Why Sempress?

**Before**: 10 GB training dataset → slow clones, expensive storage  
**After**: 1.4 GB compressed → 7× faster, 7× cheaper

## Installation

Requires Python 3.10+ and Git LFS:

```bash
# Install Git LFS first
git lfs install

# Install Sempress filter
pip install git-lfs-sempress
```

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

### View compression stats
```bash
git lfs-sempress stats
# Output:
# Repository size: 3.2 GB (was 23.4 GB)
# Compression ratio: 7.3×
# Savings: $18/month in storage costs
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

## Links

- **Website**: https://sempress.net
- **Paper**: https://sempress.net/paper.pdf
- **GitHub**: https://github.com/jalyper/git-lfs-sempress
