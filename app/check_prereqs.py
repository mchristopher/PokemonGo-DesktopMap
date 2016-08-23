#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

current_path = os.path.abspath(os.path.dirname(__file__))
package_path = os.path.join(
  current_path, 'packages.zip')

if not ('packages.zip' in sys.path):
  sys.path.insert(0, package_path)

import platform
# Import appropriate directory for platform
if sys.platform == "win32" or sys.platform == "cygwin":
  if platform.architecture()[0] == '32bit':
    platform_name = "win32"
  else:
    err = "Windows 64-bit processes currently unsupported."
    raise Exception(err)
elif sys.platform == "darwin":
  if platform.architecture()[0] == '64bit':
    platform_name = "osx64"
  else:
    err = "OSX 32-bit processes currently unsupported."
    raise Exception(err)
else:
  err = "Unexpected/unsupported platform '{}'.".format(sys.platform)
  raise Exception(err)

platform_path = os.path.join(current_path, "pylibs", platform_name)

if not os.path.isdir(platform_path):
  err = "Could not find {} python libraries {}".format(sys.platform, platform_path)
  raise Exception(err)

sys.path.append(platform_path)

# Import compiled python libraries
import_errors = []

try:
  import xxhash
except ImportError:
  import_errors
