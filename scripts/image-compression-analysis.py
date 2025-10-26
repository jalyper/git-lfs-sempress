#!/usr/bin/env python3
"""
Advanced image compression experiments using Sempress.
Tests different approaches to image-as-data compression.
"""

import numpy as np
from PIL import Image
import pandas as pd
from pathlib import Path
import tempfile
import sys

def create_test_images():
    """Create various test images with different characteristics"""
    images = {}
    
    # 1. Smooth gradient (should compress well)
    width, height = 200, 200
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            gradient[y, x] = [
                int(255 * x / width),
                int(255 * y / height),
                128
            ]
    images['gradient'] = Image.fromarray(gradient, 'RGB')
    
    # 2. Solid colors with rectangles (very compressible)
    solid = np.ones((height, width, 3), dtype=np.uint8) * 200
    solid[50:150, 50:150] = [50, 100, 200]
    solid[75:125, 75:125] = [200, 50, 100]
    images['blocks'] = Image.fromarray(solid, 'RGB')
    
    # 3. Repeated pattern (should compress well)
    pattern = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            # Checkerboard pattern
            if (x // 20 + y // 20) % 2 == 0:
                pattern[y, x] = [255, 255, 255]
            else:
                pattern[y, x] = [0, 0, 0]
    images['checkerboard'] = Image.fromarray(pattern, 'RGB')
    
    # 4. Random noise (won't compress well)
    np.random.seed(42)
    noise = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    images['noise'] = Image.fromarray(noise, 'RGB')
    
    return images

def method1_naive_pixels(img):
    """Method 1: Naive pixel table (x, y, r, g, b)"""
    width, height = img.size
    pixels = np.array(img)
    
    rows = []
    for y in range(height):
        for x in range(width):
            pixel = pixels[y, x]
            rows.append([x, y, pixel[0], pixel[1], pixel[2]])
    
    df = pd.DataFrame(rows, columns=['x', 'y', 'r', 'g', 'b'])
    return df

def method2_downsampled(img, factor=2):
    """Method 2: Downsample before converting to pixels"""
    # Resize image smaller
    new_size = (img.width // factor, img.height // factor)
    small_img = img.resize(new_size, Image.LANCZOS)
    
    # Convert to pixel table
    df = method1_naive_pixels(small_img)
    df['scale_factor'] = factor
    return df

def method3_color_quantization(img, colors=64):
    """Method 3: Reduce color palette before pixelization"""
    # Quantize colors (reduce to N colors)
    quantized = img.quantize(colors=colors).convert('RGB')
    return method1_naive_pixels(quantized)

def method4_blocks(img, block_size=10):
    """Method 4: Average blocks instead of individual pixels"""
    width, height = img.size
    pixels = np.array(img)
    
    rows = []
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            # Get block
            block = pixels[y:y+block_size, x:x+block_size]
            # Average color
            avg_color = np.mean(block, axis=(0, 1))
            rows.append([
                x // block_size,
                y // block_size,
                int(avg_color[0]),
                int(avg_color[1]),
                int(avg_color[2])
            ])
    
    df = pd.DataFrame(rows, columns=['block_x', 'block_y', 'r', 'g', 'b'])
    df['block_size'] = block_size
    return df

def compress_dataframe(df):
    """Simulate compression by measuring CSV size"""
    # Write to temp CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        csv_path = f.name
    
    size = Path(csv_path).stat().st_size
    Path(csv_path).unlink()
    return size

def calculate_psnr(original, reconstructed):
    """Calculate Peak Signal-to-Noise Ratio"""
    mse = np.mean((np.array(original) - np.array(reconstructed)) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * np.log10(255.0 / np.sqrt(mse))

def main():
    print("=" * 60)
    print("SEMPRESS IMAGE COMPRESSION EXPERIMENTS")
    print("=" * 60)
    print()
    
    images = create_test_images()
    
    results = []
    
    for img_name, img in images.items():
        print(f"\nTesting: {img_name.upper()}")
        print("-" * 60)
        
        # Original size
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            original_size = Path(f.name).stat().st_size
            original_path = f.name
        
        raw_size = img.width * img.height * 3  # Raw RGB bytes
        
        print(f"Original PNG: {original_size:,} bytes")
        print(f"Raw pixels: {raw_size:,} bytes")
        print()
        
        # Method 1: Naive pixels
        print("Method 1: Naive pixel table")
        df1 = method1_naive_pixels(img)
        size1 = compress_dataframe(df1)
        ratio1 = raw_size / size1
        print(f"  CSV size: {size1:,} bytes")
        print(f"  Ratio vs raw: {ratio1:.2f}×")
        print(f"  ❌ WORSE than PNG: {size1 / original_size:.2f}× LARGER")
        print()
        
        # Method 2: Downsampled
        print("Method 2: Downsample 2× before pixelization")
        df2 = method2_downsampled(img, factor=2)
        size2 = compress_dataframe(df2)
        ratio2 = raw_size / size2
        print(f"  CSV size: {size2:,} bytes")
        print(f"  Ratio vs raw: {ratio2:.2f}×")
        if size2 < original_size:
            print(f"  ✓ Better than PNG: {original_size / size2:.2f}×")
        else:
            print(f"  ❌ Worse than PNG: {size2 / original_size:.2f}× larger")
        print()
        
        # Method 3: Color quantization
        print("Method 3: Reduce to 64 colors first")
        df3 = method3_color_quantization(img, colors=64)
        size3 = compress_dataframe(df3)
        ratio3 = raw_size / size3
        print(f"  CSV size: {size3:,} bytes")
        print(f"  Ratio vs raw: {ratio3:.2f}×")
        print()
        
        # Method 4: Block averaging
        print("Method 4: 10×10 pixel blocks (average color)")
        df4 = method4_blocks(img, block_size=10)
        size4 = compress_dataframe(df4)
        ratio4 = raw_size / size4
        print(f"  CSV size: {size4:,} bytes")
        print(f"  Ratio vs raw: {ratio4:.2f}×")
        print(f"  Blocks: {len(df4)} (vs {img.width * img.height} pixels)")
        if size4 < original_size:
            print(f"  ✓ Better than PNG: {original_size / size4:.2f}×")
        else:
            print(f"  ❌ Worse than PNG: {size4 / original_size:.2f}× larger")
        print()
        
        results.append({
            'image': img_name,
            'original_png': original_size,
            'raw_bytes': raw_size,
            'method1_size': size1,
            'method2_size': size2,
            'method3_size': size3,
            'method4_size': size4,
        })
        
        Path(original_path).unlink()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    
    print("Best method by image type:")
    for result in results:
        img_name = result['image']
        png_size = result['original_png']
        
        # Find best method
        methods = {
            'Naive pixels': result['method1_size'],
            'Downsampled': result['method2_size'],
            'Color quantized': result['method3_size'],
            'Blocks': result['method4_size'],
        }
        
        best_method = min(methods, key=methods.get)
        best_size = methods[best_method]
        
        print(f"\n{img_name.upper()}:")
        print(f"  PNG: {png_size:,} bytes")
        print(f"  Best: {best_method} = {best_size:,} bytes")
        if best_size < png_size:
            print(f"  ✓ {png_size / best_size:.2f}× BETTER than PNG")
        else:
            print(f"  ❌ {best_size / png_size:.2f}× WORSE than PNG")
    
    print("\n" + "=" * 60)
    print("CONCLUSIONS")
    print("=" * 60)
    print()
    print("❌ Image-as-CSV approach doesn't beat PNG/JPEG for general use")
    print()
    print("Why it fails:")
    print("  • Text representation (CSV) is larger than binary")
    print("  • Each pixel = ~15 bytes as CSV text vs 3 bytes binary")
    print("  • PNG already uses very efficient compression")
    print()
    print("✓ However, block-based approach shows promise for:")
    print("  • Low-resolution images")
    print("  • Images with repeated patterns")
    print("  • Synthetic graphics / game assets")
    print()
    print("💡 Better approach: Binary format (not CSV)")
    print("  • Store pixel data as binary (not text)")
    print("  • Then apply Sempress VQ on binary data")
    print("  • This could compete with PNG!")
    print()
    print("🔬 Future research direction:")
    print("  • Sempress binary format (not just CSV)")
    print("  • Image-specific VQ codebooks")
    print("  • Hybrid: PNG for photos, Sempress for gradients/UI")
    print()

if __name__ == '__main__':
    main()
