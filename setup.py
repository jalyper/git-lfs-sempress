from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="git-lfs-sempress",
    version="0.1.0",
    author="Keaton Anderson",
    author_email="research@sempress.net",
    description="Git LFS filter for semantic compression of CSV files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jalyper/git-lfs-sempress",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0",
        "pyyaml>=6.0",
        "pandas>=2.0",
        "numpy>=1.24",
        "scikit-learn>=1.3",
        "msgpack>=1.0",
        "zstandard>=0.20",
        "sempress @ git+https://github.com/jalyper/sempress-core.git",
    ],
    entry_points={
        "console_scripts": [
            "git-lfs-sempress=git_lfs_sempress.cli:main",
        ],
    },
)
