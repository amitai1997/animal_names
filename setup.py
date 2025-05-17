"""Setup script for animal_names package."""
from setuptools import find_packages, setup  # type: ignore

setup(
    name="animal_names",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.28.1",
        "beautifulsoup4>=4.11.1",
        "jinja2>=3.1.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.1.2",
            "pytest-cov>=3.0.0",
            "black>=22.6.0",
            "flake8>=5.0.4",
            "pre-commit>=2.20.0",
        ],
    },
)
