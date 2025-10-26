"""
Configuration parser for .sempress.yml files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'version': 1,
    'compression': {
        'k': 64,
        'uncertainty_threshold': 0.2,
        'auto_lock': True,
        'lock_cols': [],
        'residual_cols': [],
    },
    'thresholds': {
        'min_size_mb': 1,
        'min_compression_ratio': 1.5,
    },
}

DEFAULT_CONFIG_YAML = """version: 1

# Compression settings
compression:
  # Codebook size (higher = better compression, slower)
  k: 64
  
  # Uncertainty threshold for quality tracking
  uncertainty_threshold: 0.2
  
  # Auto-detect ID and timestamp columns for lossless storage
  auto_lock: true
  
  # Additional columns to preserve losslessly
  lock_cols:
    - id
    - user_id
    - timestamp
    - created_at
  
  # High-precision columns (store residuals)
  residual_cols:
    - amount
    - price
    - balance

# File processing thresholds
thresholds:
  # Only compress files larger than this (MB)
  min_size_mb: 1
  
  # Skip compression if ratio is below this
  min_compression_ratio: 1.5

# Optional: S3 backup (Pro feature)
# backup:
#   enabled: false
#   s3_bucket: my-lfs-backup
#   region: us-west-2
"""


class Config:
    """Configuration manager for Sempress LFS filter"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Load configuration from .sempress.yml
        
        Args:
            config_path: Path to .sempress.yml file (defaults to current directory)
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()
    
    def _find_config(self) -> Optional[Path]:
        """Find .sempress.yml in current directory or parents"""
        current = Path.cwd()
        
        # Search up to 10 levels up
        for _ in range(10):
            config_file = current / '.sempress.yml'
            if config_file.exists():
                logger.info(f"Found config: {config_file}")
                return config_file
            
            # Check if we're at git root
            if (current / '.git').exists():
                break
            
            parent = current.parent
            if parent == current:
                break
            current = parent
        
        logger.warning("No .sempress.yml found, using defaults")
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse configuration file"""
        if not self.config_path or not self.config_path.exists():
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            
            # Merge with defaults (user config overrides)
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            
            # Merge nested dicts
            if 'compression' in user_config:
                config['compression'].update(user_config['compression'])
            if 'thresholds' in user_config:
                config['thresholds'].update(user_config['thresholds'])
            
            logger.info(f"Loaded config from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return DEFAULT_CONFIG.copy()
    
    def get_compression_config(self) -> Dict[str, Any]:
        """Get compression settings"""
        return self.config.get('compression', {})
    
    def get_thresholds(self) -> Dict[str, Any]:
        """Get file processing thresholds"""
        return self.config.get('thresholds', {})
    
    def should_compress(self, file_size_bytes: int, estimated_ratio: float) -> bool:
        """
        Determine if a file should be compressed based on thresholds.
        
        Args:
            file_size_bytes: Size of the file in bytes
            estimated_ratio: Estimated compression ratio
            
        Returns:
            True if file should be compressed
        """
        thresholds = self.get_thresholds()
        
        # Check minimum file size
        min_size_mb = thresholds.get('min_size_mb', 1)
        size_mb = file_size_bytes / (1024 * 1024)
        if size_mb < min_size_mb:
            logger.info(f"File too small ({size_mb:.2f} MB < {min_size_mb} MB), skipping compression")
            return False
        
        # Check minimum compression ratio
        min_ratio = thresholds.get('min_compression_ratio', 1.5)
        if estimated_ratio < min_ratio:
            logger.info(f"Compression ratio too low ({estimated_ratio:.2f}× < {min_ratio}×), skipping")
            return False
        
        return True
    
    @staticmethod
    def create_default_config(output_path: Path):
        """Create a default .sempress.yml file"""
        with open(output_path, 'w') as f:
            f.write(DEFAULT_CONFIG_YAML)
        logger.info(f"Created default config: {output_path}")
