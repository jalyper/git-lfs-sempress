"""
Extended format support for Sempress compression.
Handles Parquet, JSON, Excel, and experimental image formats.
"""

import tempfile
from pathlib import Path
from typing import Tuple, Optional
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed - image compression unavailable")


class FormatConverter:
    """Convert various formats to/from CSV for Sempress compression"""
    
    @staticmethod
    def detect_format(filepath: str) -> str:
        """Detect file format from extension"""
        ext = Path(filepath).suffix.lower()
        format_map = {
            '.csv': 'csv',
            '.parquet': 'parquet',
            '.json': 'json',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.bmp': 'image',
            '.tiff': 'image',
        }
        return format_map.get(ext, 'unknown')
    
    @staticmethod
    def to_csv(input_path: str, output_path: str) -> dict:
        """
        Convert various formats to CSV for compression.
        Returns metadata needed for reconstruction.
        """
        format_type = FormatConverter.detect_format(input_path)
        
        if format_type == 'csv':
            # Already CSV, just copy
            import shutil
            shutil.copy(input_path, output_path)
            return {'format': 'csv'}
        
        elif format_type == 'parquet':
            df = pd.read_parquet(input_path)
            df.to_csv(output_path, index=False)
            return {
                'format': 'parquet',
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
        
        elif format_type == 'json':
            # Try to read as records (list of dicts)
            df = pd.read_json(input_path)
            df.to_csv(output_path, index=False)
            return {
                'format': 'json',
                'columns': list(df.columns),
                'orient': 'records'
            }
        
        elif format_type == 'excel':
            df = pd.read_excel(input_path)
            df.to_csv(output_path, index=False)
            return {
                'format': 'excel',
                'columns': list(df.columns),
                'sheet_name': 'Sheet1'
            }
        
        elif format_type == 'image':
            if not PIL_AVAILABLE:
                raise ImportError("Pillow required for image compression: pip install Pillow")
            
            metadata = FormatConverter.image_to_csv(input_path, output_path)
            return metadata
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    @staticmethod
    def from_csv(csv_path: str, output_path: str, metadata: dict):
        """
        Convert CSV back to original format using metadata.
        """
        format_type = metadata.get('format')
        
        if format_type == 'csv':
            import shutil
            shutil.copy(csv_path, output_path)
        
        elif format_type == 'parquet':
            df = pd.read_csv(csv_path)
            # Restore dtypes if available
            if 'dtypes' in metadata:
                for col, dtype in metadata['dtypes'].items():
                    try:
                        df[col] = df[col].astype(dtype)
                    except:
                        pass
            df.to_parquet(output_path, index=False)
        
        elif format_type == 'json':
            df = pd.read_csv(csv_path)
            orient = metadata.get('orient', 'records')
            df.to_json(output_path, orient=orient)
        
        elif format_type == 'excel':
            df = pd.read_csv(csv_path)
            sheet_name = metadata.get('sheet_name', 'Sheet1')
            df.to_excel(output_path, sheet_name=sheet_name, index=False)
        
        elif format_type == 'image':
            FormatConverter.csv_to_image(csv_path, output_path, metadata)
        
        else:
            raise ValueError(f"Cannot reconstruct format: {format_type}")
    
    @staticmethod
    def image_to_csv(image_path: str, csv_path: str) -> dict:
        """
        Convert image to CSV representation.
        Each pixel becomes a row: (x, y, r, g, b, [alpha])
        
        This is experimental - semantic compression on pixel data!
        """
        img = Image.open(image_path)
        
        # Convert to RGB or RGBA
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        width, height = img.size
        has_alpha = img.mode == 'RGBA'
        
        # Convert to numpy array
        pixels = np.array(img)
        
        # Reshape to table: (x, y, r, g, b, [alpha])
        rows = []
        for y in range(height):
            for x in range(width):
                pixel = pixels[y, x]
                if has_alpha:
                    rows.append([x, y, pixel[0], pixel[1], pixel[2], pixel[3]])
                else:
                    rows.append([x, y, pixel[0], pixel[1], pixel[2]])
        
        # Create DataFrame
        if has_alpha:
            df = pd.DataFrame(rows, columns=['x', 'y', 'r', 'g', 'b', 'alpha'])
        else:
            df = pd.DataFrame(rows, columns=['x', 'y', 'r', 'g', 'b'])
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Converted image to CSV: {width}×{height} = {len(rows)} pixels")
        
        return {
            'format': 'image',
            'width': width,
            'height': height,
            'mode': img.mode,
            'original_format': img.format or 'PNG'
        }
    
    @staticmethod
    def csv_to_image(csv_path: str, image_path: str, metadata: dict):
        """
        Reconstruct image from CSV pixel data.
        """
        df = pd.read_csv(csv_path)
        
        width = metadata['width']
        height = metadata['height']
        mode = metadata['mode']
        
        # Create empty image array
        if mode == 'RGBA':
            img_array = np.zeros((height, width, 4), dtype=np.uint8)
            channels = ['r', 'g', 'b', 'alpha']
        else:
            img_array = np.zeros((height, width, 3), dtype=np.uint8)
            channels = ['r', 'g', 'b']
        
        # Fill pixels from dataframe
        for _, row in df.iterrows():
            x = int(row['x'])
            y = int(row['y'])
            
            # Clip coordinates to image bounds
            if 0 <= x < width and 0 <= y < height:
                for i, channel in enumerate(channels):
                    # Clip values to valid range [0, 255]
                    value = np.clip(row[channel], 0, 255)
                    img_array[y, x, i] = int(value)
        
        # Create image
        img = Image.fromarray(img_array, mode=mode)
        
        # Save in original format
        original_format = metadata.get('original_format', 'PNG')
        img.save(image_path, format=original_format)
        
        logger.info(f"Reconstructed image: {width}×{height} as {original_format}")


class MultiFormatCompressor:
    """Wrapper around Sempress for multiple formats"""
    
    def __init__(self, compressor):
        self.compressor = compressor
        self.converter = FormatConverter()
    
    def compress(self, input_data: bytes, filename: str) -> Tuple[bytes, dict]:
        """
        Compress any supported format.
        Returns (compressed_data, metadata)
        """
        # Detect format
        format_type = self.converter.detect_format(filename)
        
        # Write input to temp file
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_input:
            tmp_input.write(input_data)
            input_path = tmp_input.name
        
        try:
            # Convert to CSV
            csv_path = input_path + '.csv'
            metadata = self.converter.to_csv(input_path, csv_path)
            
            # Compress CSV
            with open(csv_path, 'rb') as f:
                csv_data = f.read()
            
            compressed_data = self.compressor.compress(csv_data)
            
            # Clean up
            Path(input_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)
            
            return compressed_data, metadata
            
        except Exception as e:
            # Clean up on error
            Path(input_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)
            raise e
    
    def decompress(self, compressed_data: bytes, metadata: dict, output_filename: str) -> bytes:
        """
        Decompress and convert back to original format.
        """
        # Decompress to CSV
        csv_data = self.compressor.decompress(compressed_data)
        
        # Write CSV to temp file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_csv:
            tmp_csv.write(csv_data)
            csv_path = tmp_csv.name
        
        try:
            # Convert from CSV to original format
            output_path = csv_path.replace('.csv', Path(output_filename).suffix)
            self.converter.from_csv(csv_path, output_path, metadata)
            
            # Read result
            with open(output_path, 'rb') as f:
                result_data = f.read()
            
            # Clean up
            Path(csv_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)
            
            return result_data
            
        except Exception as e:
            Path(csv_path).unlink(missing_ok=True)
            raise e
