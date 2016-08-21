#!/bin/bash
source ve/bin/activate
pip install -r app/map/requirements.txt --target ./packages
touch ./packages/google/__init__.py
if [ -d packages ]; then
  cd packages
  find . -name "*.pyc" -delete
  find . -name "*.so" -delete
  find . -name "*.egg-info" | xargs rm -rf
  find . -name "Cryptodome" | xargs rm -rf
  find . -name "pyproj" | xargs rm -rf
  find . -name "xxhash" | xargs rm -rf
  zip -9mrv packages.zip .
  mv packages.zip ..
  cd ..
  rm -rf packages
fi
