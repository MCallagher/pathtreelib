""" Setup module for pathtreelib.
"""

from setuptools import setup

with open("README.rst", "r", encoding="utf8") as f:
    readme = f.read()

setup(
    name="pathtreelib",
    version="0.1.0",
    description="An tree-based extension to pathlib",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/MCallagher/pathtreelib",
    project_urls={
        "Documentation": "https://pathtreelib.readthedocs.io/en/latest/",
        "source": "https://github.com/MCallagher/pathtreelib"
    },
    author="Marco Calandro",
    author_email="marco.calandro@mensa.it",
    license="MIT",
    packages=["pathtreelib"],
    install_requires=["xlsxwriter>=3.1.9"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Filesystems",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13"
    ]
)
