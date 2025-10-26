"""
Compression wrapper for Sempress library.
Interfaces with the sempress encoder/decoder.
"""

import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Import sempress from the installed package
try:
    from sempress import encode_csv, decode_to_csv
    from sempress.table_encoder import EncodeConfig
except ImportError:
    logging.error("Sempress library not found. Please install: pip install /path/to/sempress")
    sys.exit(1)

logger = logging.getLogger(__name__)


class SempressCompressor:
    """Wrapper around Sempress compression library"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize compressor with configuration.
        
        Args:
            config: Configuration dictionary with compression settings
        """
        self.config = config or {}
        self.lock_cols = self.config.get('lock_cols', [])
        self.residual_cols = self.config.get('residual_cols', [])
        self.k = self.config.get('k', 64)
        self.uncertainty_threshold = self.config.get('uncertainty_threshold', 0.2)
        self.auto_lock = self.config.get('auto_lock', True)
    
    def compress(self, csv_data: bytes) -> bytes:
        """
        Compress CSV data to .smp format.
        
        Args:
            csv_data: Raw CSV file content as bytes
            
        Returns:
            Compressed .smp file as bytes
        """
        # Write CSV to temporary file (Sempress needs file path)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
            tmp.write(csv_data)
            tmp_path = tmp.name
        
        try:
            # Create Sempress configuration
            encode_config = EncodeConfig(
                lock_cols=self.lock_cols,
                residual_cols=self.residual_cols,
                k=self.k,
                uncertainty_thresh=self.uncertainty_threshold,
                random_state=42
            )
            
            # Compress with Sempress
            logger.info(f"Compressing CSV with k={self.k}, lock_cols={self.lock_cols}")
            compressed_blob = encode_csv(tmp_path, encode_config)
            
            # Calculate compression ratio
            original_size = len(csv_data)
            compressed_size = len(compressed_blob)
            ratio = original_size / compressed_size if compressed_size > 0 else 0
            
            logger.info(f"Compression complete: {original_size} → {compressed_size} bytes ({ratio:.2f}×)")
            
            return compressed_blob
            
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    def decompress(self, smp_data: bytes) -> bytes:
        """
        Decompress .smp data back to CSV format.
        
        Args:
            smp_data: Compressed .smp file content as bytes
            
        Returns:
            Original CSV file as bytes
        """
        # Write .smp to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.smp', delete=False) as tmp_smp:
            tmp_smp.write(smp_data)
            smp_path = tmp_smp.name
        
        # Create temporary output path
        csv_path = smp_path.replace('.smp', '_recon.csv')
        
        try:
            # Decompress with Sempress
            logger.info(f"Decompressing .smp file ({len(smp_data)} bytes)")
            decode_to_csv(smp_path, csv_path)
            
            # Read reconstructed CSV
            with open(csv_path, 'rb') as f:
                csv_data = f.read()
            
            logger.info(f"Decompression complete: {len(smp_data)} → {len(csv_data)} bytes")
            
            return csv_data
            
        finally:
            # Clean up temp files
            Path(smp_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)
    
    def estimate_compression_ratio(self, csv_data: bytes) -> float:
        """
        Estimate compression ratio without full compression.
        Quick heuristic based on file size and numeric density.
        
        Args:
            csv_data: Raw CSV file content
            
        Returns:
            Estimated compression ratio
        """
        # Simple heuristic: larger numeric-heavy files compress better
        # This is fast and avoids full compression for analysis
        
        size_mb = len(csv_data) / (1024 * 1024)
        
        # Baseline estimate: 3-5× for typical numeric CSVs
        if size_mb < 1:
            return 2.5  # Small files don't compress as well
        elif size_mb < 10:
            return 4.0
        elif size_mb < 100:
            return 5.5
        else:
            return 7.0  # Large files with repetitive patterns
        
        # TODO: Improve this by sampling the CSV and checking numeric density
