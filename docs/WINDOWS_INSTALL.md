# Windows Installation Guide

## Issue: "git-lfs-sempress is not recognized"

This happens when Python's Scripts directory isn't on your Windows PATH.

---

## Quick Fix Solutions

### Solution 1: Add to PATH (Recommended - Permanent)

**PowerShell (Run as Administrator)**:
```powershell
# Get your Python Scripts path
$scriptsPath = python -m site --user-site
$scriptsPath = $scriptsPath.Replace('site-packages', 'Scripts')

# Add to PATH for current user
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$scriptsPath",
    "User"
)

# Restart PowerShell, then test
git-lfs-sempress --version
```

**Manual PATH Addition**:
1. Press `Win + X`, select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", select "Path", click "Edit"
5. Click "New" and add:
   ```
   C:\Users\keato\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts
   ```
6. Click "OK" on all dialogs
7. **Restart PowerShell**

---

### Solution 2: Run with Full Path (Immediate)

```powershell
# Use the full path
& "C:\Users\keato\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\git-lfs-sempress.exe" init

# Or find it dynamically
$scriptsPath = python -m site --user-site
$scriptsPath = $scriptsPath.Replace('site-packages', 'Scripts')
& "$scriptsPath\git-lfs-sempress.exe" init
```

---

### Solution 3: Use Python Module (Works Everywhere)

```powershell
# Run as a Python module
python -m git_lfs_sempress.cli init

# Or use py launcher
py -m git_lfs_sempress.cli init
```

**This always works!** You can create an alias:

```powershell
# Add to your PowerShell profile
Set-Alias git-lfs-sempress "python -m git_lfs_sempress.cli"

# Or create a function
function git-lfs-sempress { python -m git_lfs_sempress.cli $args }
```

---

### Solution 4: Reinstall with pipx (Best for Tools)

```powershell
# Install pipx (isolated tool installer)
python -m pip install --user pipx
python -m pipx ensurepath

# Restart PowerShell

# Install with pipx (automatically on PATH)
pipx install git+https://github.com/jalyper/git-lfs-sempress.git

# Now it works
git-lfs-sempress --version
```

---

## Recommended: Solution 3 (Python Module)

**Why**: Works immediately, no PATH issues, cross-platform

**How to use**:

```powershell
# All commands work the same
python -m git_lfs_sempress.cli init
python -m git_lfs_sempress.cli track "*.csv"
python -m git_lfs_sempress.cli analyze
python -m git_lfs_sempress.cli stats
python -m git_lfs_sempress.cli quality original.csv reconstructed.csv
```

**Create a PowerShell alias** (add to profile):

```powershell
# Open profile
notepad $PROFILE

# Add this line:
function git-lfs-sempress { python -m git_lfs_sempress.cli $args }

# Save and reload
. $PROFILE

# Now works like normal
git-lfs-sempress init
```

---

## Testing Your Installation

After choosing a solution, test it:

```powershell
# Test version
git-lfs-sempress --version
# Should output: git-lfs-sempress, version 0.1.0

# Test help
git-lfs-sempress --help
# Should show all commands

# Test in a repo
cd your-project
git-lfs-sempress init
# Should create .sempress.yml
```

---

## Common Issues

### "Python is not recognized"

**Fix**: Install Python from Microsoft Store or python.org

### "Module not found: git_lfs_sempress"

**Fix**: Reinstall the package
```powershell
pip uninstall git-lfs-sempress
pip install git+https://github.com/jalyper/git-lfs-sempress.git
```

### "Sempress module not found"

**Fix**: Install the Sempress library
```powershell
pip install git+https://github.com/jalyper/sempress-core.git
```

---

## For Git Bash Users

If you're using Git Bash instead of PowerShell:

```bash
# Add to ~/.bashrc
export PATH="$PATH:/c/Users/keato/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/Scripts"

# Or use Python module
alias git-lfs-sempress='python -m git_lfs_sempress.cli'
```

---

## Quick Reference

| Method | Command | Permanent? | Setup Time |
|--------|---------|------------|------------|
| **Full Path** | `& "C:\...\Scripts\git-lfs-sempress.exe"` | No | 0 min |
| **Python Module** | `python -m git_lfs_sempress.cli` | No* | 0 min |
| **Add to PATH** | `git-lfs-sempress` | Yes | 5 min |
| **pipx** | `git-lfs-sempress` | Yes | 2 min |

*Can be made permanent with alias

---

## My Recommendation

**For immediate use**: Solution 3 (Python module)
```powershell
python -m git_lfs_sempress.cli init
```

**For long-term**: Solution 1 (Add to PATH) or Solution 4 (pipx)

---

## Need Help?

If none of these work, please share:
1. Python version: `python --version`
2. Pip version: `pip --version`
3. Installation output: `pip install git-lfs-sempress --verbose`
4. PATH value: `$env:PATH` (PowerShell) or `echo $PATH` (Git Bash)
