#!/bin/bash
source map/ve/bin/activate
cd map
pip install -r requirements.txt --target ./packages
touch ./packages/google/__init__.py
if [ -d packages ]; then
  cd packages
  find . -name "*.pyc" -delete
  find . -name "*.egg-info" | xargs rm -rf
  zip -9mrv packages.zip .
  mv packages.zip ..
  cd ..
  rm -rf packages
fi
