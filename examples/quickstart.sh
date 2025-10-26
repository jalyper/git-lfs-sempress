#!/bin/bash
# Quick start example for Sempress Git LFS

echo "Sempress Git LFS - Quick Start Example"
echo "======================================="
echo ""

# 1. Create a new repository
echo "Step 1: Create repository"
mkdir sempress-example
cd sempress-example
git init
git config user.email "you@example.com"
git config user.name "Your Name"
echo "✓ Repository created"
echo ""

# 2. Install Git LFS
echo "Step 2: Initialize Git LFS"
git lfs install
echo "✓ Git LFS initialized"
echo ""

# 3. Initialize Sempress
echo "Step 3: Initialize Sempress"
git-lfs-sempress init
echo "✓ Sempress initialized"
echo ""

# 4. Track CSV files
echo "Step 4: Track CSV files"
git-lfs-sempress track "*.csv"
echo "✓ CSV files tracked"
echo ""

# 5. Create sample data
echo "Step 5: Create sample CSV data"
cat > sales_data.csv << 'EOF'
date,product_id,quantity,price,customer_id
2024-01-01,PROD001,5,29.99,CUST123
2024-01-01,PROD002,3,49.99,CUST456
2024-01-01,PROD003,1,99.99,CUST789
2024-01-02,PROD001,2,29.99,CUST321
2024-01-02,PROD004,7,19.99,CUST654
EOF

# Add more rows to make it larger
for i in {1..10000}; do
    echo "2024-01-0$((RANDOM % 9 + 1)),PROD00$((RANDOM % 9 + 1)),$((RANDOM % 100)),$((RANDOM % 100)).$((RANDOM % 100)),CUST$((RANDOM % 1000))" >> sales_data.csv
done

echo "✓ Sample data created ($(wc -l < sales_data.csv) rows)"
echo ""

# 6. Commit configuration
echo "Step 6: Commit configuration"
git add .sempress.yml .gitattributes
git commit -m "Initialize Sempress LFS filter"
echo "✓ Configuration committed"
echo ""

# 7. Add CSV file (compression happens automatically!)
echo "Step 7: Add CSV file (automatic compression)"
ORIGINAL_SIZE=$(stat -f%z sales_data.csv 2>/dev/null || stat -c%s sales_data.csv)
echo "   Original size: $ORIGINAL_SIZE bytes"

git add sales_data.csv
git commit -m "Add sales data (compressed)"

STORED_SIZE=$(git cat-file -s HEAD:sales_data.csv)
echo "   Stored size: $STORED_SIZE bytes"
echo "   Savings: $((ORIGINAL_SIZE - STORED_SIZE)) bytes"
echo "✓ File committed (compressed)"
echo ""

# 8. Verify decompression works
echo "Step 8: Test decompression"
rm sales_data.csv
git checkout sales_data.csv
if [ -f sales_data.csv ]; then
    echo "✓ File restored successfully"
    echo "   Lines: $(wc -l < sales_data.csv)"
else
    echo "✗ Decompression failed"
fi
echo ""

echo "======================================="
echo "Example complete!"
echo ""
echo "What happened:"
echo "1. CSV file was automatically compressed when you ran 'git add'"
echo "2. Git stored the compressed .smp file (much smaller)"
echo "3. When you checked out, it was automatically decompressed"
echo "4. You see the original CSV (seamless!)"
echo ""
echo "Try it yourself:"
echo "  cd sempress-example"
echo "  ls -lh sales_data.csv"
echo "  head sales_data.csv"
