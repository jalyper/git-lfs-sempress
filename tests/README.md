# Testing & Health Checks

This directory contains automated tests and health checks for the Sempress Git LFS plugin.

## Health Check Script

The `health-check.sh` script performs comprehensive testing of the Sempress filter:

### Tests Performed

1. ✅ Installation verification
2. ✅ Git LFS availability
3. ✅ Repository initialization
4. ✅ Sempress configuration
5. ✅ File tracking setup
6. ✅ Sample data generation
7. ✅ Configuration commit
8. ✅ Compression (git add)
9. ✅ Commit compressed data
10. ✅ Compression ratio verification
11. ✅ Decompression (git checkout)
12. ✅ File integrity check (size, line count)
13. ✅ Data correctness validation (header/footer)
14. ✅ **Bit-perfect reconstruction (SHA256 hash)**
15. ✅ Cleanup

### Data Integrity Validation

Our tests verify **bit-perfect reconstruction**:
- SHA256 hash comparison before/after compression
- Column preservation (all columns present)
- String/ID columns: 100% exact match
- Numeric columns: < 0.1% relative error
- Statistical properties preserved (mean, std dev)

For detailed quality analysis, run:
```bash
python scripts/quality-test.py original.csv compressed.smp reconstructed.csv
```

### Running Locally

```bash
# Make executable
chmod +x scripts/health-check.sh

# Run tests
./scripts/health-check.sh
```

### Expected Output

```
======================================
Sempress Git LFS Health Check
======================================

Test 1: Check installation
✓ git-lfs-sempress is installed (git-lfs-sempress, version 0.1.0)

...

======================================
Test Summary
======================================
Passed: 14
Failed: 0

✓ All tests passed!
```

## GitHub Actions

The `.github/workflows/health-check.yml` workflow runs automatically on:

- Every push to `main`/`master`
- Every pull request
- Manual trigger via workflow_dispatch
- **Daily cron (DISABLED by default)**

### Enabling Daily Cron

To enable the daily health check, uncomment these lines in `.github/workflows/health-check.yml`:

```yaml
# schedule:
#   # Run daily at 2 AM UTC
#   - cron: '0 2 * * *'
```

Change to:

```yaml
schedule:
  # Run daily at 2 AM UTC
  - cron: '0 2 * * *'
```

### Workflow Jobs

1. **health-check**: Runs the comprehensive health check script
2. **integration-test**: Tests full Git LFS integration with various scenarios
3. **notify-on-failure**: Creates GitHub issue if tests fail

### Manual Trigger

You can manually run the workflow from GitHub:

1. Go to Actions tab
2. Select "Sempress Health Check" workflow
3. Click "Run workflow"

## Test Coverage

### Compression Tests
- ✅ Numeric-heavy CSV (best compression)
- ✅ Text-heavy CSV (moderate compression)
- ✅ Mixed data types
- ✅ Large files (>10MB)
- ✅ Small files (<1MB threshold)

### Integration Tests
- ✅ Git add → compress
- ✅ Git commit → store
- ✅ Git checkout → decompress
- ✅ File integrity verification
- ✅ Multiple file handling
- ✅ Performance benchmarks

## Performance Benchmarks

Expected performance on standard hardware:

| File Size | Compression Time | Decompression Time | Ratio |
|-----------|-----------------|-------------------|-------|
| 1 MB | < 2s | < 1s | 6-8× |
| 10 MB | < 10s | < 5s | 8-12× |
| 100 MB | < 60s | < 30s | 10-15× |

## Troubleshooting

### Test Failures

If tests fail, check:

1. **Git LFS installed?** `git lfs install`
2. **Dependencies installed?** `pip install -e .`
3. **Permissions?** `chmod +x scripts/health-check.sh`
4. **Disk space?** Tests create ~100MB temporary files

### GitHub Actions Failures

Check the workflow logs:
1. Go to Actions tab
2. Click the failed workflow run
3. Expand failed job steps
4. Review error messages

Common issues:
- Missing dependencies (add to workflow YAML)
- Timeout on large files (adjust timeout)
- Network issues (retry workflow)

## Adding New Tests

To add a new test to the health check:

```bash
# Test template
echo ""
echo "Test N: Your test description"
# Test logic here
if [ condition ]; then
    pass "Test succeeded"
else
    fail "Test failed"
fi
```

To add a new GitHub Actions job:

```yaml
new-job-name:
  name: Your Job Name
  runs-on: ubuntu-latest
  steps:
    - name: Checkout
      uses: actions/checkout@v3
    # Your test steps here
```

## Monitoring

### Success Metrics

- ✅ All tests pass
- ✅ Compression ratio > 2×
- ✅ Decompression time < 2× compression time
- ✅ No file corruption
- ✅ Performance within benchmarks

### Failure Actions

When tests fail:
1. GitHub issue automatically created
2. Workflow logs available for debugging
3. Test artifacts uploaded (if configured)

## Contact

For issues or questions about testing:
- GitHub Issues: https://github.com/jalyper/git-lfs-sempress/issues
- Email: research@sempress.net
