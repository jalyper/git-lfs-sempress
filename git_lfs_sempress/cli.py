"""
Command-line interface for git-lfs-sempress.
"""

import click
import sys
import logging
from pathlib import Path
from . import __version__
from .filter import run_clean_filter, run_smudge_filter
from .config import Config

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose):
    """Git LFS Sempress Plugin - Automatic semantic compression for Git LFS"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[sempress] %(levelname)s: %(message)s'
    )


@main.command()
@click.argument('filename', required=False)
def clean(filename):
    """
    Clean filter: compress CSV → .smp (called by Git internally).
    
    Usage: git-lfs-sempress clean %f
    """
    run_clean_filter(filename)


@main.command()
@click.argument('filename', required=False)
def smudge(filename):
    """
    Smudge filter: decompress .smp → CSV (called by Git internally).
    
    Usage: git-lfs-sempress smudge %f
    """
    run_smudge_filter(filename)


@main.command()
def init():
    """
    Initialize Sempress in the current Git repository.
    
    This will:
    - Create .sempress.yml configuration file
    - Configure Git filter for LFS
    - Create .gitattributes if needed
    """
    try:
        # Check if we're in a Git repo
        if not (Path.cwd() / '.git').exists():
            click.echo("❌ Not a Git repository. Run 'git init' first.", err=True)
            sys.exit(1)
        
        click.echo("🚀 Initializing Sempress LFS filter...\n")
        
        # Create .sempress.yml
        config_path = Path.cwd() / '.sempress.yml'
        if config_path.exists():
            click.echo(f"✓ Config file already exists: {config_path}")
        else:
            Config.create_default_config(config_path)
            click.echo(f"✓ Created config file: {config_path}")
        
        # Configure Git filter
        import subprocess
        
        commands = [
            ('git', 'config', 'filter.lfs-sempress.clean', 'git-lfs-sempress clean %f'),
            ('git', 'config', 'filter.lfs-sempress.smudge', 'git-lfs-sempress smudge %f'),
            ('git', 'config', 'filter.lfs-sempress.required', 'true'),
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                click.echo(f"❌ Failed to configure Git: {result.stderr}", err=True)
                sys.exit(1)
        
        click.echo("✓ Git filter configured")
        
        # Check .gitattributes
        gitattributes = Path.cwd() / '.gitattributes'
        if not gitattributes.exists():
            click.echo(f"\n📝 Next steps:")
            click.echo(f"  1. Track CSV files: git lfs-sempress track \"*.csv\"")
            click.echo(f"  2. Add and commit: git add .sempress.yml && git commit -m \"Add Sempress compression\"")
        else:
            click.echo(f"\n✓ .gitattributes exists")
            click.echo(f"  Run 'git lfs-sempress track \"*.csv\"' to track CSV files")
        
        click.echo(f"\n✅ Sempress initialized successfully!")
        
    except Exception as e:
        click.echo(f"❌ Initialization failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('pattern')
def track(pattern):
    """
    Track files with Sempress compression.
    
    Example: git lfs-sempress track "*.csv"
    """
    try:
        gitattributes = Path.cwd() / '.gitattributes'
        
        # Create or append to .gitattributes
        line = f"{pattern} filter=lfs-sempress diff=lfs merge=lfs -text\n"
        
        # Check if already tracked
        if gitattributes.exists():
            content = gitattributes.read_text()
            if pattern in content and 'lfs-sempress' in content:
                click.echo(f"✓ Pattern '{pattern}' already tracked")
                return
        
        # Append to .gitattributes
        with open(gitattributes, 'a') as f:
            f.write(line)
        
        click.echo(f"✓ Now tracking: {pattern}")
        click.echo(f"  Files matching this pattern will be compressed automatically")
        click.echo(f"\n📝 Next: git add .gitattributes && git commit -m \"Track {pattern} with Sempress\"")
        
    except Exception as e:
        click.echo(f"❌ Failed to track pattern: {e}", err=True)
        sys.exit(1)


@main.command()
def analyze():
    """
    Analyze repository and estimate potential compression savings.
    """
    try:
        import glob
        
        click.echo("🔍 Analyzing repository for CSV files...\n")
        
        # Find all CSV files
        csv_files = list(Path.cwd().rglob('*.csv'))
        
        if not csv_files:
            click.echo("No CSV files found in repository")
            return
        
        total_size = 0
        file_info = []
        
        for csv_file in csv_files:
            if '.git' in str(csv_file):
                continue
            
            try:
                size = csv_file.stat().st_size
                total_size += size
                file_info.append((csv_file.relative_to(Path.cwd()), size))
            except:
                continue
        
        if not file_info:
            click.echo("No accessible CSV files found")
            return
        
        # Sort by size
        file_info.sort(key=lambda x: x[1], reverse=True)
        
        # Display results
        click.echo(f"Found {len(file_info)} CSV files:\n")
        
        for path, size in file_info[:10]:  # Top 10
            size_mb = size / (1024 * 1024)
            click.echo(f"  {path}: {size_mb:.2f} MB")
        
        if len(file_info) > 10:
            click.echo(f"  ... and {len(file_info) - 10} more")
        
        total_mb = total_size / (1024 * 1024)
        total_gb = total_size / (1024 * 1024 * 1024)
        
        # Estimate compression (average 6× ratio for numeric CSV)
        estimated_ratio = 6.0
        compressed_size = total_size / estimated_ratio
        compressed_mb = compressed_size / (1024 * 1024)
        savings_pct = ((total_size - compressed_size) / total_size) * 100
        
        click.echo(f"\n📊 Summary:")
        click.echo(f"  Total size: {total_gb:.2f} GB ({total_mb:.0f} MB)")
        click.echo(f"  Estimated compressed: {compressed_mb:.0f} MB")
        click.echo(f"  Estimated ratio: {estimated_ratio}×")
        click.echo(f"  Potential savings: {savings_pct:.0f}%")
        
        # Storage cost estimate ($0.023/GB/month for GitHub LFS)
        monthly_cost_before = total_gb * 0.023
        monthly_cost_after = (compressed_size / (1024**3)) * 0.023
        monthly_savings = monthly_cost_before - monthly_cost_after
        
        click.echo(f"\n💰 Estimated storage cost (GitHub LFS pricing):")
        click.echo(f"  Current: ${monthly_cost_before:.2f}/month")
        click.echo(f"  After compression: ${monthly_cost_after:.2f}/month")
        click.echo(f"  Savings: ${monthly_savings:.2f}/month")
        
        click.echo(f"\n✨ Run 'git lfs-sempress init' to get started!")
        
    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)
        logger.error(f"Analysis error: {e}", exc_info=True)
        sys.exit(1)


@main.command()
def stats():
    """
    Show compression statistics for the current repository.
    """
    try:
        # Check if Sempress is configured
        import subprocess
        
        result = subprocess.run(
            ['git', 'config', 'filter.lfs-sempress.clean'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            click.echo("❌ Sempress filter not configured. Run 'git lfs-sempress init' first.")
            return
        
        click.echo("📊 Sempress Statistics\n")
        click.echo("✓ Filter configured: Yes")
        
        # Check for .sempress.yml
        config_path = Path.cwd() / '.sempress.yml'
        if config_path.exists():
            click.echo(f"✓ Config file: {config_path}")
            
            # Load and display config
            config = Config(config_path)
            comp_config = config.get_compression_config()
            click.echo(f"\n  Compression settings:")
            click.echo(f"    k: {comp_config.get('k', 64)}")
            click.echo(f"    Uncertainty threshold: {comp_config.get('uncertainty_threshold', 0.2)}")
            click.echo(f"    Lock columns: {comp_config.get('lock_cols', []) or 'auto-detect'}")
        else:
            click.echo("⚠ Config file: Not found (using defaults)")
        
        # Check .gitattributes
        gitattributes = Path.cwd() / '.gitattributes'
        if gitattributes.exists():
            content = gitattributes.read_text()
            patterns = [line.split()[0] for line in content.split('\n') 
                       if 'lfs-sempress' in line and line.strip()]
            
            if patterns:
                click.echo(f"\n✓ Tracked patterns ({len(patterns)}):")
                for pattern in patterns:
                    click.echo(f"    {pattern}")
            else:
                click.echo(f"\n⚠ No files tracked yet")
                click.echo(f"  Run 'git lfs-sempress track \"*.csv\"' to start")
        else:
            click.echo(f"\n⚠ .gitattributes: Not found")
        
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Failed to get stats: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('original', type=click.Path(exists=True))
@click.argument('reconstructed', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed column-by-column metrics')
def quality(original, reconstructed, verbose):
    """
    Compare original and reconstructed files for quality.
    
    Example: git lfs-sempress quality original.csv reconstructed.csv
    """
    try:
        from .quality import compare_files
        
        click.echo(f"Comparing files...")
        click.echo(f"  Original: {original}")
        click.echo(f"  Reconstructed: {reconstructed}")
        
        report = compare_files(original, reconstructed, verbose=verbose)
        
        # Exit with error code if there are issues
        if report['has_critical_issues'] or report['has_errors']:
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Quality check failed: {e}", err=True)
        logger.error(f"Quality check error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
