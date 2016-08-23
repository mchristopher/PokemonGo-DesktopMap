#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

import check_prereqs

current_path = os.path.abspath(os.path.dirname(__file__))
map_path = os.path.join(
  current_path, 'map')

# Set CA bundle for Requests library
os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(
  os.path.abspath(os.path.dirname(__file__)), 'cacert.pem')

# Set pyproj data path
os.environ['PROJ_DIR'] = os.path.join(
  os.path.abspath(os.path.dirname(__file__)),
  'pylibs', 'shared', 'pyproj_data')

# Monkey patch pkg_resources since zip files aren't
# properly supported
class Distribution:
  version = '3.0.0'

def get_distribution(dist):
  return Distribution()

import pkg_resources
pkg_resources.get_distribution = get_distribution

# Import map project and run
sys.path.append(map_path)
from runserver import main
main()
