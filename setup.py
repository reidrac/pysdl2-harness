#!/usr/bin/env python

from setuptools import setup
import sys

sys._gen_docs= True
from harness import version

setup(name="pysdl2-harness",
      version=version,
      description="Some simple classes to make working with pysdl2 easier",
      author="Juan J. Martinez",
      author_email="jjm@usebox.net",
      url="https://github.com/reidrac/pysdl2-harness",
      license="MIT",
      include_package_data=True,
      zip_safe=False,
      install_requires=["pysdl2",],
      packages=["harness",],
      classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        "License :: OSI Approved :: MIT License",
        ],
      keywords="pysdl2 game sdl",
      )

