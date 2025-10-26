#!/usr/bin/env python3
"""
Comprehensive data integrity test for Sempress compression.
Tests numerical accuracy, column preservation, and statistical properties.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import subprocess

def test_compression_quality(original_csv, compressed_smp, reconstructed_csv):
    """
    Run comprehensive quality checks on compressed data.
    """
    print("=" * 60)
    print("SEMPRESS DATA INTEGRITY TEST")
    print("=" * 60)
    print()
    
    # Load data
    print("Loading data...")
    df_original = pd.read_csv(original_csv)
    df_reconstructed = pd.read_csv(reconstructed_csv)
    
    print(f"  Original: {len(df_original)} rows, {len(df_original.columns)} columns")
    print(f"  Reconstructed: {len(df_reconstructed)} rows, {len(df_reconstructed.columns)} columns")
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Same shape
    print("Test 1: Shape preservation")
    if df_original.shape == df_reconstructed.shape:
        print("  ✓ Shape matches:", df_original.shape)
        tests_passed += 1
    else:
        print("  ✗ Shape mismatch!")
        print(f"    Original: {df_original.shape}")
        print(f"    Reconstructed: {df_reconstructed.shape}")
        tests_failed += 1
    print()
    
    # Test 2: Same columns
    print("Test 2: Column preservation")
    if list(df_original.columns) == list(df_reconstructed.columns):
        print(f"  ✓ All {len(df_original.columns)} columns preserved")
        tests_passed += 1
    else:
        print("  ✗ Column mismatch!")
        missing = set(df_original.columns) - set(df_reconstructed.columns)
        extra = set(df_reconstructed.columns) - set(df_original.columns)
        if missing:
            print(f"    Missing: {missing}")
        if extra:
            print(f"    Extra: {extra}")
        tests_failed += 1
    print()
    
    # Test 3: Exact match for string/ID columns
    print("Test 3: Lossless string/ID columns")
    string_cols = df_original.select_dtypes(include=['object']).columns
    if len(string_cols) > 0:
        all_match = True
        for col in string_cols:
            if not df_original[col].equals(df_reconstructed[col]):
                all_match = False
                print(f"  ✗ {col}: Mismatch!")
                diff_count = (df_original[col] != df_reconstructed[col]).sum()
                print(f"    {diff_count} differences")
            else:
                print(f"  ✓ {col}: Exact match")
        
        if all_match:
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("  (No string columns to test)")
        tests_passed += 1
    print()
    
    # Test 4: Numerical accuracy
    print("Test 4: Numerical accuracy")
    numeric_cols = df_original.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        all_accurate = True
        for col in numeric_cols:
            orig = df_original[col].values
            recon = df_reconstructed[col].values
            
            # Calculate metrics
            mae = np.mean(np.abs(orig - recon))
            rmse = np.sqrt(np.mean((orig - recon) ** 2))
            max_error = np.max(np.abs(orig - recon))
            
            # Relative error
            mean_val = np.mean(np.abs(orig))
            if mean_val > 0:
                rel_error = mae / mean_val * 100
            else:
                rel_error = 0
            
            print(f"  {col}:")
            print(f"    MAE: {mae:.6f}")
            print(f"    RMSE: {rmse:.6f}")
            print(f"    Max error: {max_error:.6f}")
            print(f"    Relative error: {rel_error:.4f}%")
            
            # Pass if relative error < 0.1%
            if rel_error < 0.1:
                print(f"    ✓ Good accuracy (< 0.1% error)")
            else:
                print(f"    ⚠ Error exceeds 0.1%")
                all_accurate = False
        
        if all_accurate:
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("  (No numeric columns to test)")
        tests_passed += 1
    print()
    
    # Test 5: Statistical properties preserved
    print("Test 5: Statistical properties")
    if len(numeric_cols) > 0:
        all_stats_match = True
        for col in numeric_cols[:3]:  # Test first 3 numeric columns
            orig_mean = df_original[col].mean()
            recon_mean = df_reconstructed[col].mean()
            orig_std = df_original[col].std()
            recon_std = df_reconstructed[col].std()
            
            mean_diff = abs(orig_mean - recon_mean) / abs(orig_mean) * 100
            std_diff = abs(orig_std - recon_std) / abs(orig_std) * 100
            
            print(f"  {col}:")
            print(f"    Mean: {orig_mean:.4f} → {recon_mean:.4f} ({mean_diff:.2f}% diff)")
            print(f"    StdDev: {orig_std:.4f} → {recon_std:.4f} ({std_diff:.2f}% diff)")
            
            if mean_diff < 1.0 and std_diff < 1.0:
                print(f"    ✓ Statistics preserved")
            else:
                print(f"    ⚠ Significant statistical change")
                all_stats_match = False
        
        if all_stats_match:
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print("  (No numeric columns to test)")
        tests_passed += 1
    print()
    
    # Test 6: Byte-level comparison
    print("Test 6: Byte-level hash")
    hash_original = subprocess.run(
        ['sha256sum', original_csv],
        capture_output=True,
        text=True
    ).stdout.split()[0]
    
    hash_reconstructed = subprocess.run(
        ['sha256sum', reconstructed_csv],
        capture_output=True,
        text=True
    ).stdout.split()[0]
    
    print(f"  Original: {hash_original[:16]}...")
    print(f"  Reconstructed: {hash_reconstructed[:16]}...")
    
    if hash_original == hash_reconstructed:
        print("  ✓ Bit-perfect reconstruction (SHA256 match)")
        tests_passed += 1
    else:
        print("  ⚠ Not bit-perfect (expected for lossy compression)")
        print("  This is OK if numerical accuracy tests passed")
        tests_passed += 1  # Still count as pass
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print()
    
    if tests_failed == 0:
        print("✓ All quality checks passed!")
        print("Data integrity verified.")
        return 0
    else:
        print("✗ Some quality checks failed")
        print("Review the output above for details")
        return 1


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python quality_test.py <original.csv> <compressed.smp> <reconstructed.csv>")
        sys.exit(1)
    
    original_csv = sys.argv[1]
    compressed_smp = sys.argv[2]
    reconstructed_csv = sys.argv[3]
    
    exit_code = test_compression_quality(original_csv, compressed_smp, reconstructed_csv)
    sys.exit(exit_code)
