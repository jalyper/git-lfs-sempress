"""
Quality monitoring and reporting for Sempress compression.
Detects and reports data variations with actionable guidance.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class QualityReport:
    """Comprehensive quality report for compression/decompression"""
    
    def __init__(self, original_df: pd.DataFrame, reconstructed_df: pd.DataFrame):
        self.original = original_df
        self.reconstructed = reconstructed_df
        self.issues = []
        self.warnings = []
        self.metrics = {}
        
    def analyze(self) -> Dict:
        """Run full quality analysis"""
        
        # 1. Shape check
        if self.original.shape != self.reconstructed.shape:
            self.issues.append({
                'severity': 'CRITICAL',
                'type': 'shape_mismatch',
                'message': f"Shape changed: {self.original.shape} → {self.reconstructed.shape}",
                'fix': "This should never happen. Please report as a bug."
            })
            return self._build_report()
        
        # 2. Column check
        orig_cols = set(self.original.columns)
        recon_cols = set(self.reconstructed.columns)
        
        if orig_cols != recon_cols:
            missing = orig_cols - recon_cols
            extra = recon_cols - orig_cols
            self.issues.append({
                'severity': 'CRITICAL',
                'type': 'column_mismatch',
                'message': f"Columns changed. Missing: {missing}, Extra: {extra}",
                'fix': "This should never happen. Please report as a bug."
            })
            return self._build_report()
        
        # 3. Check each column
        for col in self.original.columns:
            self._check_column(col)
        
        # 4. Calculate overall similarity
        self._calculate_similarity()
        
        return self._build_report()
    
    def _check_column(self, col: str):
        """Check quality of a single column"""
        orig = self.original[col]
        recon = self.reconstructed[col]
        
        # String/categorical columns should be exact
        if orig.dtype == 'object' or pd.api.types.is_categorical_dtype(orig):
            matches = (orig == recon).sum()
            total = len(orig)
            match_pct = (matches / total) * 100
            
            if match_pct < 100:
                mismatches = total - matches
                self.issues.append({
                    'severity': 'ERROR',
                    'type': 'string_mismatch',
                    'column': col,
                    'message': f"{col}: {mismatches} values changed ({match_pct:.2f}% preserved)",
                    'fix': f"Add '{col}' to lock_cols in .sempress.yml for lossless storage"
                })
                
                # Show examples of differences
                diff_idx = (orig != recon).idxmax()
                if diff_idx is not None:
                    self.issues[-1]['example'] = f"Row {diff_idx}: '{orig[diff_idx]}' → '{recon[diff_idx]}'"
            
            self.metrics[col] = {'type': 'string', 'match_pct': match_pct}
        
        # Numeric columns - check error
        elif pd.api.types.is_numeric_dtype(orig):
            orig_vals = orig.values.astype(float)
            recon_vals = recon.values.astype(float)
            
            # Calculate error metrics
            mae = np.mean(np.abs(orig_vals - recon_vals))
            rmse = np.sqrt(np.mean((orig_vals - recon_vals) ** 2))
            max_error = np.max(np.abs(orig_vals - recon_vals))
            
            mean_val = np.mean(np.abs(orig_vals))
            if mean_val > 0:
                rel_error = (mae / mean_val) * 100
            else:
                rel_error = 0
            
            # Check for exact match
            exact_matches = np.sum(orig_vals == recon_vals)
            exact_pct = (exact_matches / len(orig_vals)) * 100
            
            self.metrics[col] = {
                'type': 'numeric',
                'mae': mae,
                'rmse': rmse,
                'max_error': max_error,
                'relative_error': rel_error,
                'exact_match_pct': exact_pct
            }
            
            # Warnings/errors based on thresholds
            if exact_pct == 100:
                # Perfect match - no issue
                pass
            elif rel_error < 0.01:  # < 0.01% error
                # Excellent quality - just info
                logger.info(f"{col}: Excellent quality ({rel_error:.4f}% error)")
            elif rel_error < 0.1:  # < 0.1% error
                # Good quality - minor warning
                self.warnings.append({
                    'severity': 'INFO',
                    'type': 'minor_error',
                    'column': col,
                    'message': f"{col}: Minor variations ({rel_error:.4f}% relative error)",
                    'details': f"MAE: {mae:.6f}, Max error: {max_error:.6f}",
                    'fix': "Quality is good. If you need perfect precision, add to residual_cols."
                })
            elif rel_error < 1.0:  # < 1% error
                # Acceptable but noticeable
                self.warnings.append({
                    'severity': 'WARNING',
                    'type': 'moderate_error',
                    'column': col,
                    'message': f"{col}: Noticeable variations ({rel_error:.4f}% relative error)",
                    'details': f"MAE: {mae:.6f}, Max error: {max_error:.6f}",
                    'fix': f"Add '{col}' to residual_cols in .sempress.yml for higher precision."
                })
            else:  # >= 1% error
                # Significant error
                self.issues.append({
                    'severity': 'ERROR',
                    'type': 'high_error',
                    'column': col,
                    'message': f"{col}: Significant variations ({rel_error:.2f}% relative error)",
                    'details': f"MAE: {mae:.6f}, Max error: {max_error:.6f}",
                    'fix': f"Add '{col}' to residual_cols or lock_cols in .sempress.yml."
                })
    
    def _calculate_similarity(self):
        """Calculate overall similarity score"""
        total_cells = self.original.size
        exact_matches = 0
        
        for col in self.original.columns:
            orig = self.original[col]
            recon = self.reconstructed[col]
            
            if orig.dtype == 'object':
                exact_matches += (orig == recon).sum()
            else:
                # For numeric, count as match if difference < 1e-10
                orig_vals = orig.values.astype(float)
                recon_vals = recon.values.astype(float)
                exact_matches += np.sum(np.abs(orig_vals - recon_vals) < 1e-10)
        
        similarity_pct = (exact_matches / total_cells) * 100
        self.metrics['overall_similarity'] = similarity_pct
        
    def _build_report(self) -> Dict:
        """Build final report dictionary"""
        return {
            'similarity_score': self.metrics.get('overall_similarity', 0),
            'issues': self.issues,
            'warnings': self.warnings,
            'column_metrics': self.metrics,
            'has_critical_issues': any(i['severity'] == 'CRITICAL' for i in self.issues),
            'has_errors': any(i['severity'] == 'ERROR' for i in self.issues),
            'has_warnings': len(self.warnings) > 0
        }
    
    def print_report(self, verbose=False):
        """Print human-readable report"""
        report = self.analyze() if not self.metrics else self._build_report()
        
        print("\n" + "="*60)
        print("SEMPRESS QUALITY REPORT")
        print("="*60)
        
        # Overall score
        similarity = report['similarity_score']
        print(f"\n📊 Overall Similarity: {similarity:.2f}%")
        
        if similarity == 100:
            print("✓ Perfect reconstruction - all data preserved exactly!")
        elif similarity >= 99.9:
            print("✓ Excellent quality - virtually lossless")
        elif similarity >= 99:
            print("⚠ Good quality - minor variations detected")
        elif similarity >= 95:
            print("⚠ Acceptable quality - some variations detected")
        else:
            print("✗ Poor quality - significant variations detected")
        
        # Critical issues
        if report['has_critical_issues']:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in report['issues']:
                if issue['severity'] == 'CRITICAL':
                    print(f"  ✗ {issue['message']}")
                    print(f"    Fix: {issue['fix']}")
        
        # Errors
        if report['has_errors']:
            print("\n❌ ERRORS:")
            for issue in report['issues']:
                if issue['severity'] == 'ERROR':
                    print(f"  ✗ {issue['message']}")
                    if 'example' in issue:
                        print(f"    Example: {issue['example']}")
                    print(f"    Fix: {issue['fix']}")
        
        # Warnings
        if report['has_warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in report['warnings']:
                print(f"  ⚠ {warning['message']}")
                if verbose and 'details' in warning:
                    print(f"    {warning['details']}")
                print(f"    {warning['fix']}")
        
        # Column-by-column (verbose only)
        if verbose and not report['has_critical_issues']:
            print("\n📋 COLUMN DETAILS:")
            for col, metrics in report['column_metrics'].items():
                if col == 'overall_similarity':
                    continue
                    
                if metrics['type'] == 'string':
                    match_pct = metrics['match_pct']
                    if match_pct == 100:
                        print(f"  ✓ {col} (string): 100% exact match")
                    else:
                        print(f"  ✗ {col} (string): {match_pct:.2f}% match")
                
                elif metrics['type'] == 'numeric':
                    rel_err = metrics['relative_error']
                    exact_pct = metrics['exact_match_pct']
                    
                    if exact_pct == 100:
                        print(f"  ✓ {col} (numeric): 100% exact match")
                    elif rel_err < 0.1:
                        print(f"  ✓ {col} (numeric): {rel_err:.4f}% error, {exact_pct:.1f}% exact")
                    else:
                        print(f"  ⚠ {col} (numeric): {rel_err:.4f}% error, {exact_pct:.1f}% exact")
        
        # Recommendations
        if report['has_errors'] or report['has_warnings']:
            print("\n💡 RECOMMENDATIONS:")
            print("  1. Edit .sempress.yml in your repository")
            print("  2. Add problematic columns to lock_cols or residual_cols")
            print("  3. Commit the updated config")
            print("  4. Re-compress your files")
            print("\nExample .sempress.yml:")
            print("  compression:")
            print("    lock_cols:")
            print("      - id")
            print("      - timestamp")
            print("    residual_cols:")
            print("      - amount")
            print("      - price")
        
        print("\n" + "="*60 + "\n")
        
        return report


def compare_files(original_path: str, reconstructed_path: str, verbose=False) -> Dict:
    """
    Compare original and reconstructed CSV files.
    Returns quality report dictionary.
    """
    try:
        df_original = pd.read_csv(original_path)
        df_reconstructed = pd.read_csv(reconstructed_path)
        
        qr = QualityReport(df_original, df_reconstructed)
        qr.print_report(verbose=verbose)
        
        return qr._build_report()
        
    except Exception as e:
        logger.error(f"Failed to compare files: {e}")
        return {
            'similarity_score': 0,
            'issues': [{
                'severity': 'CRITICAL',
                'type': 'comparison_failed',
                'message': f"Failed to compare files: {str(e)}",
                'fix': "Ensure both files are valid CSV files."
            }],
            'warnings': [],
            'column_metrics': {},
            'has_critical_issues': True,
            'has_errors': False,
            'has_warnings': False
        }
