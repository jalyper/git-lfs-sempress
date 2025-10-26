# Publishing to PyPI

## Current Status: NOT PUBLISHED ❌

The plugin is **ready for PyPI** but has one blocker:

### 🚨 Blocker: Sempress Dependency

The plugin requires the `sempress` library, which is not on PyPI yet.

**Two options:**

---

## Option 1: Publish Sempress Core First (Recommended)

**Steps:**

1. **Publish sempress-core to PyPI**
   ```bash
   cd /path/to/sempress-core
   
   # Create setup.py for sempress-core
   # Update version, dependencies, etc.
   
   # Build
   python setup.py sdist bdist_wheel
   
   # Publish to PyPI
   twine upload dist/*
   ```

2. **Update git-lfs-sempress dependencies**
   ```python
   # setup.py
   install_requires=[
       "click>=8.0",
       "pyyaml>=6.0",
       "pandas>=2.0",
       "numpy>=1.24",
       "scikit-learn>=1.3",
       "msgpack>=1.0",
       "zstandard>=0.20",
       "sempress>=0.1.0",  # ← Add this
   ]
   ```

3. **Publish git-lfs-sempress**
   ```bash
   cd /app/git-lfs-sempress
   
   # Build distribution
   python setup.py sdist bdist_wheel
   
   # Upload to PyPI
   twine upload dist/*
   ```

---

## Option 2: Bundle Sempress Code (Quick Fix)

**Steps:**

1. **Copy sempress code into git-lfs-sempress**
   ```bash
   cp -r /path/to/sempress/src/sempress git_lfs_sempress/
   ```

2. **Update imports**
   ```python
   # Change from:
   from sempress import encode_csv
   
   # To:
   from git_lfs_sempress.sempress import encode_csv
   ```

3. **Publish directly**
   ```bash
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

**Downside**: Users can't use sempress independently

---

## Publishing Steps (When Ready)

### 1. Create PyPI Account
- Go to https://pypi.org/account/register/
- Verify email
- Set up 2FA (required)

### 2. Create API Token
- Go to https://pypi.org/manage/account/token/
- Create token for "Entire account" or specific project
- Save token securely

### 3. Install Build Tools
```bash
pip install build twine
```

### 4. Build Package
```bash
cd /app/git-lfs-sempress

# Clean old builds
rm -rf build/ dist/ *.egg-info/

# Build distribution files
python -m build
```

This creates:
- `dist/git-lfs-sempress-0.1.0.tar.gz` (source)
- `dist/git_lfs_sempress-0.1.0-py3-none-any.whl` (wheel)

### 5. Test on TestPyPI (Optional but Recommended)
```bash
# Upload to test instance
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ git-lfs-sempress
```

### 6. Upload to PyPI
```bash
twine upload dist/*

# You'll be prompted for:
# username: __token__
# password: <your-api-token>
```

### 7. Verify
```bash
# Install from PyPI
pip install git-lfs-sempress

# Test it works
git-lfs-sempress --version
```

---

## What Happens After Publishing

### Users Can Install Easily
```bash
# Instead of:
pip install git+https://github.com/jalyper/git-lfs-sempress.git

# They can do:
pip install git-lfs-sempress
```

### PyPI Page
Your package will have a page at:
https://pypi.org/project/git-lfs-sempress/

With:
- README as description
- Download statistics
- Version history
- Dependencies listed

### Automatic Updates
```bash
# Users can update easily
pip install --upgrade git-lfs-sempress
```

---

## Version Management

### Semantic Versioning
- **0.1.0** - Initial release (current)
- **0.1.1** - Bug fixes
- **0.2.0** - New features (quality command, multi-format)
- **1.0.0** - Production-ready, stable API

### Releasing New Versions
```bash
# 1. Update version in setup.py
version="0.1.1"

# 2. Create git tag
git tag v0.1.1
git push origin v0.1.1

# 3. Build and upload
python -m build
twine upload dist/*
```

---

## Pre-Publication Checklist

### Required Files ✅
- [x] setup.py - Complete
- [x] README.md - Complete
- [x] LICENSE - Complete
- [x] requirements.txt - Complete

### Optional but Recommended
- [ ] CHANGELOG.md - Document version history
- [ ] MANIFEST.in - Include non-Python files
- [ ] .pypirc - Configure credentials (DON'T commit)

### Testing
- [x] Package builds without errors
- [x] All tests pass (15/15)
- [x] CLI commands work
- [ ] Install from built wheel works

---

## Security Considerations

### API Token Security
```bash
# NEVER commit your token
# Add to .gitignore:
echo ".pypirc" >> .gitignore

# Store in environment
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-token>

# Then upload without prompts
twine upload dist/*
```

### Package Verification
After publishing, verify:
- Download count seems reasonable
- No malicious users forking similar names
- Dependencies are correct versions

---

## Current Recommendation

**Don't publish to PyPI yet because:**

1. ❌ `sempress` library dependency not on PyPI
2. ⚠️ Better to launch on GitHub first, get feedback
3. ⚠️ May want to fix bugs before "permanent" PyPI release

**When to publish:**

1. ✅ After 100+ GitHub stars (validates demand)
2. ✅ After fixing any critical bugs found
3. ✅ After deciding: bundle sempress or publish separately?
4. ✅ After soft launch gets positive feedback

---

## Alternative: Install from GitHub

**For now, users can install directly from GitHub:**

```bash
# From GitHub (always works)
pip install git+https://github.com/jalyper/git-lfs-sempress.git

# From local clone
git clone https://github.com/jalyper/git-lfs-sempress.git
cd git-lfs-sempress
pip install -e .
```

**This is fine for launch!** Many projects start this way.

---

## Summary

**Status**: NOT on PyPI (intentional)

**Blockers**:
1. Sempress library dependency
2. Want feedback before PyPI

**Next Steps**:
1. Launch on GitHub (HackerNews, Reddit)
2. Get 100+ stars
3. Fix any bugs
4. Decide on sempress dependency strategy
5. Then publish to PyPI

**Installation for now**:
```bash
pip install git+https://github.com/jalyper/git-lfs-sempress.git
```

This is **totally normal** for alpha releases! 🚀
