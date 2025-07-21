import os
import sys
from setuptools import setup, find_packages

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

# Default fallback version
DEFAULT_VERSION = "v0.0.0"
VERSION_FILE = os.path.join(THIS_DIR, 'polyNOM-version.txt')

# Read version from file or fallback
if os.path.exists(VERSION_FILE):
    with open(VERSION_FILE, 'r') as f:
        version_raw = f.read().strip()
else:
    version_raw = DEFAULT_VERSION

# Validate and normalize version
if not version_raw.startswith('v'):
    raise ValueError(f"Invalid version format: {version_raw}. Expected format 'v0.0.0'.")
version = version_raw[1:]  # strip 'v'

# Optional debug flag parsing
options_def = {"--debug"}
options = {flag.lstrip("-"): False for flag in options_def}
for flag in options_def:
    if flag in sys.argv:
        options[flag.lstrip("-")] = True
        sys.argv.remove(flag)

# Read README.md as long description
def readme():
    with open(os.path.join(THIS_DIR, 'README.md'), encoding="utf-8") as f:
        return f.read()

def load_requirements(filename='requirements.txt', exclude=None):
    exclude = exclude or []
    with open(os.path.join(THIS_DIR, filename)) as f:
        return [
            line.strip() for line in f
            if line.strip() and not line.startswith('#') and line.strip() not in exclude
        ]

setup(
    name='polypheny-polynom',
    version=version,
    description='Object Mapper for Polypheny',
    long_description=readme(),
    long_description_content_type='text/markdown',
    author="The Polypheny Project",
    author_email="mail@polypheny.org",
    url="https://polypheny.com/",
    project_urls={
        "Documentation": "https://github.com/polypheny/PolyNOM/docs",
        "Code": "https://github.com/polypheny/PolyNOM",
    },
    license="Apache License, Version 2.0",
    packages=find_packages(),
    include_package_data=True,
    command_options={
        'build_sphinx': {
            'version': ('setup.py', version),
            'release': ('setup.py', version),
        },
    },
    python_requires=">=3.11",
    install_requires=load_requirements(exclude=['pytest']),
    extras_require={
        "dev": ["pytest"],
    },
)
