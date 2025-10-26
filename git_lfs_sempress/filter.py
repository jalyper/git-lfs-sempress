"""
Git LFS filter implementation (clean/smudge protocol).
This is the core of the Sempress LFS plugin.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from .compression import SempressCompressor
from .config import Config

logger = logging.getLogger(__name__)


class SempressFilter:
    """Git LFS clean/smudge filter for Sempress compression"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize filter with configuration.
        
        Args:
            config: Configuration object (loads from .sempress.yml if None)
        """
        self.config = config or Config()
        self.compressor = SempressCompressor(self.config.get_compression_config())
    
    def clean(self, input_stream=None, filename: Optional[str] = None) -> bytes:
        """
        Clean filter: compress CSV → .smp for Git LFS storage.
        Called when staging files (git add).
        
        Args:
            input_stream: Input stream (stdin by default)
            filename: Name of the file being processed
            
        Returns:
            Compressed .smp data (or original if compression skipped)
        """
        input_stream = input_stream or sys.stdin.buffer
        
        try:
            # Read CSV data from stdin
            csv_data = input_stream.read()
            
            if not csv_data:
                logger.warning("Empty input data")
                return b''
            
            logger.info(f"Clean filter: processing {len(csv_data)} bytes" + 
                       (f" from {filename}" if filename else ""))
            
            # Estimate compression ratio
            estimated_ratio = self.compressor.estimate_compression_ratio(csv_data)
            
            # Check if we should compress
            if not self.config.should_compress(len(csv_data), estimated_ratio):
                logger.info("Skipping compression (below thresholds)")
                return csv_data
            
            # Compress with Sempress
            try:
                compressed_data = self.compressor.compress(csv_data)
                
                # Verify compression is beneficial
                actual_ratio = len(csv_data) / len(compressed_data)
                if actual_ratio < self.config.get_thresholds().get('min_compression_ratio', 1.5):
                    logger.warning(f"Actual compression ratio too low ({actual_ratio:.2f}×), using original")
                    return csv_data
                
                logger.info(f"✓ Compressed: {len(csv_data)} → {len(compressed_data)} bytes ({actual_ratio:.2f}×)")
                return compressed_data
                
            except Exception as e:
                logger.error(f"Compression failed: {e}", exc_info=True)
                logger.warning("Falling back to original file")
                return csv_data
        
        except Exception as e:
            logger.error(f"Clean filter error: {e}", exc_info=True)
            return b''
    
    def smudge(self, input_stream=None, filename: Optional[str] = None) -> bytes:
        """
        Smudge filter: decompress .smp → CSV for working tree.
        Called when checking out files (git checkout).
        
        Args:
            input_stream: Input stream (stdin by default)
            filename: Name of the file being processed
            
        Returns:
            Decompressed CSV data (or original if not compressed)
        """
        input_stream = input_stream or sys.stdin.buffer
        
        try:
            # Read data from stdin
            input_data = input_stream.read()
            
            if not input_data:
                logger.warning("Empty input data")
                return b''
            
            logger.info(f"Smudge filter: processing {len(input_data)} bytes" +
                       (f" for {filename}" if filename else ""))
            
            # Check if data is compressed (simple heuristic: check for .smp header)
            # Sempress .smp files start with msgpack data
            # If it looks like CSV text, it's not compressed
            if input_data[:100].decode('utf-8', errors='ignore').count(',') > 5:
                logger.info("Data appears to be uncompressed CSV, passing through")
                return input_data
            
            # Try to decompress
            try:
                csv_data = self.compressor.decompress(input_data)
                logger.info(f"✓ Decompressed: {len(input_data)} → {len(csv_data)} bytes")
                return csv_data
                
            except Exception as e:
                logger.error(f"Decompression failed: {e}", exc_info=True)
                logger.warning("Data may not be compressed, passing through")
                return input_data
        
        except Exception as e:
            logger.error(f"Smudge filter error: {e}", exc_info=True)
            return b''


def run_clean_filter(filename: Optional[str] = None):
    """
    Entry point for clean filter.
    Called by Git: git-lfs-sempress clean %f
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='[sempress-clean] %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    
    try:
        filter_obj = SempressFilter()
        compressed_data = filter_obj.clean(filename=filename)
        sys.stdout.buffer.write(compressed_data)
        sys.stdout.buffer.flush()
    except Exception as e:
        logger.error(f"Clean filter fatal error: {e}", exc_info=True)
        sys.exit(1)


def run_smudge_filter(filename: Optional[str] = None):
    """
    Entry point for smudge filter.
    Called by Git: git-lfs-sempress smudge %f
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='[sempress-smudge] %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    
    try:
        filter_obj = SempressFilter()
        csv_data = filter_obj.smudge(filename=filename)
        sys.stdout.buffer.write(csv_data)
        sys.stdout.buffer.flush()
    except Exception as e:
        logger.error(f"Smudge filter fatal error: {e}", exc_info=True)
        sys.exit(1)
