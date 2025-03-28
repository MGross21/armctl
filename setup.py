from setuptools import setup, find_packages
from pathlib import Path

# Read requirements from requirements.txt
requirements_path = Path(__file__).parent / "requirements.txt"
install_requires = requirements_path.read_text().splitlines() if requirements_path.exists() else []

setup(
    name="agnostic-controller",
    version="0.1.0",
    packages=find_packages(),
    install_requires=install_requires,
)