#!/bin/bash
source ve/bin/activate
pip install -r app/map/requirements.txt --target ./packages
touch ./packages/google/__init__.py
if [ -d packages ]; then
  cd packages
  find . -name "*.pyc" -delete
  find . -name "*.so" -delete
  find . -name "*.dist-info" | xargs rm -rf
  find . -name "*.egg-info" | xargs rm -rf
  find . -name "Cryptodome" | xargs rm -rf
  find . -name "pyproj" | xargs rm -rf
  find . -name "xxhash" | xargs rm -rf
  find . -name "gevent" | xargs rm -rf
  rm -fr "babel/locale-data"
  zip -9mrv packages.zip .
  rm -fr ../app/packages.zip
  mv packages.zip ../app/
  cd ..
  rm -rf packages
fi
