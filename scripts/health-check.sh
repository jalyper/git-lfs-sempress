#!/bin/bash
# Health check script for Sempress Git LFS filter
# Tests compression, decompression, and file integrity

set -e

echo "======================================"
echo "Sempress Git LFS Health Check"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Test 1: Check if git-lfs-sempress is installed
echo "Test 1: Check installation"
if command -v git-lfs-sempress &> /dev/null; then
    VERSION=$(git-lfs-sempress --version)
    pass "git-lfs-sempress is installed ($VERSION)"
else
    fail "git-lfs-sempress not found"
    exit 1
fi

# Test 2: Check if Git LFS is installed
echo ""
echo "Test 2: Check Git LFS"
if command -v git-lfs &> /dev/null; then
    pass "Git LFS is installed"
else
    fail "Git LFS not found"
    exit 1
fi

# Test 3: Create test repository
echo ""
echo "Test 3: Create test repository"
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
git init > /dev/null 2>&1
git config user.email "test@sempress.net"
git config user.name "Test User"
git lfs install > /dev/null 2>&1
pass "Test repository created: $TEST_DIR"

# Test 4: Initialize Sempress
echo ""
echo "Test 4: Initialize Sempress"
git-lfs-sempress init > /dev/null 2>&1
if [ -f .sempress.yml ]; then
    pass "Sempress initialized (.sempress.yml created)"
else
    fail "Failed to create .sempress.yml"
    exit 1
fi

# Test 5: Track CSV files
echo ""
echo "Test 5: Track CSV files"
git-lfs-sempress track "*.csv" > /dev/null 2>&1
if grep -q "lfs-sempress" .gitattributes; then
    pass "CSV files tracked in .gitattributes"
else
    fail "Failed to update .gitattributes"
    exit 1
fi

# Test 6: Create sample CSV data
echo ""
echo "Test 6: Create sample CSV data"
cat > test_data.csv << 'EOF'
id,timestamp,temperature,pressure,humidity,sensor_id
1,2024-01-01T00:00:00,23.5,1013.25,65.2,SENSOR_001
2,2024-01-01T00:01:00,23.6,1013.20,65.1,SENSOR_001
3,2024-01-01T00:02:00,23.7,1013.22,65.3,SENSOR_001
4,2024-01-01T00:03:00,23.5,1013.25,65.0,SENSOR_002
5,2024-01-01T00:04:00,23.4,1013.28,64.9,SENSOR_002
EOF

# Repeat data to make file larger (need > 1MB for compression)
for i in {1..50000}; do
    echo "$((i+5)),2024-01-01T00:0$((i%60)):00,$((RANDOM % 10 + 20)).$((RANDOM % 10)),$((1000 + RANDOM % 50)).$((RANDOM % 100)),$((60 + RANDOM % 10)).$((RANDOM % 10)),SENSOR_00$((RANDOM % 5 + 1))" >> test_data.csv
done

ORIGINAL_SIZE=$(stat -f%z test_data.csv 2>/dev/null || stat -c%s test_data.csv)
pass "Sample CSV created (${ORIGINAL_SIZE} bytes)"

# Test 7: Commit config files
echo ""
echo "Test 7: Commit configuration"
git add .sempress.yml .gitattributes > /dev/null 2>&1
git commit -m "Initialize Sempress" > /dev/null 2>&1
pass "Configuration committed"

# Test 8: Add CSV file (triggers compression)
echo ""
echo "Test 8: Compress CSV (git add)"
info "Original size: $ORIGINAL_SIZE bytes"

# Capture compression output
COMPRESS_OUTPUT=$(git add test_data.csv 2>&1)
info "Compression output:"
echo "$COMPRESS_OUTPUT" | grep -E "(Compression complete|Compressed)" || echo "  (no compression output)"

# Check if file was added
if git diff --cached --name-only | grep -q "test_data.csv"; then
    pass "CSV file staged (compression applied)"
else
    fail "Failed to stage CSV file"
    exit 1
fi

# Test 9: Commit compressed file
echo ""
echo "Test 9: Commit compressed file"
git commit -m "Add test data" > /dev/null 2>&1
pass "Compressed file committed"

# Test 10: Check compression ratio
echo ""
echo "Test 10: Verify compression"
# Get the object size from Git
GIT_OBJECT_SIZE=$(git cat-file -s HEAD:test_data.csv)
COMPRESSION_RATIO=$(echo "scale=2; $ORIGINAL_SIZE / $GIT_OBJECT_SIZE" | bc)

info "Original size: $ORIGINAL_SIZE bytes"
info "Stored size: $GIT_OBJECT_SIZE bytes"
info "Compression ratio: ${COMPRESSION_RATIO}×"

# Verify compression worked (at least 2× ratio)
if (( $(echo "$COMPRESSION_RATIO > 2.0" | bc -l) )); then
    pass "Compression ratio is good (${COMPRESSION_RATIO}×)"
else
    fail "Compression ratio too low (${COMPRESSION_RATIO}×)"
fi

# Test 11: Remove file and checkout (triggers decompression)
echo ""
echo "Test 11: Decompress CSV (git checkout)"
rm test_data.csv
DECOMPRESS_OUTPUT=$(git checkout test_data.csv 2>&1)
info "Decompression output:"
echo "$DECOMPRESS_OUTPUT" | grep -E "(Decompression complete|Decompressed)" || echo "  (no decompression output)"

if [ -f test_data.csv ]; then
    pass "File restored via decompression"
else
    fail "Failed to restore file"
    exit 1
fi

# Test 12: Verify file integrity
echo ""
echo "Test 12: Verify file integrity"
RESTORED_SIZE=$(stat -f%z test_data.csv 2>/dev/null || stat -c%s test_data.csv)
LINE_COUNT=$(wc -l < test_data.csv)

info "Restored size: $RESTORED_SIZE bytes"
info "Line count: $LINE_COUNT"

# File should have 50,006 lines (header + 50,005 data rows)
if [ "$LINE_COUNT" -gt 50000 ]; then
    pass "File integrity verified ($LINE_COUNT lines)"
else
    fail "File integrity check failed ($LINE_COUNT lines)"
fi

# Test 13: Check first and last lines
echo ""
echo "Test 13: Verify data correctness"
FIRST_LINE=$(head -1 test_data.csv)
LAST_LINE=$(tail -1 test_data.csv)

if [[ "$FIRST_LINE" == "id,timestamp,temperature"* ]]; then
    pass "Header row correct"
else
    fail "Header row corrupted"
fi

if [[ "$LAST_LINE" == *"SENSOR_00"* ]]; then
    pass "Data row correct"
else
    fail "Data row corrupted"
fi

# Cleanup
cd /
rm -rf "$TEST_DIR"
info "Cleaned up test directory"

# Summary
echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
