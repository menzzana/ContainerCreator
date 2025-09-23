#!/usr/bin/python
# coding=utf-8
#-----------------------------------------------------------------------
# Container creator
# Copyright (C) 2025  Henric Zazzi <henric@zazzi.se>
#
# Container creator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------
import sys
import os
import subprocess
#-----------------------------------------------------------------------
RECIPE_FILE = "recipe.def"
TEMP_CONTAINER = "tmp.sif"
CONTAINER_PATH = "container.sif"
#-----------------------------------------------------------------------
# Builds the container
#-----------------------------------------------------------------------
if len(sys.argv) < 2:
    print("Usage: create.py <folder_path>")
    sys.exit(1)
folder_path = sys.argv[1]
file_path = os.path.join(folder_path, RECIPE_FILE)
container_path = os.path.join(folder_path, CONTAINER_PATH)
tmp_path = os.path.join(folder_path, TEMP_CONTAINER)
build_cmd = ["apptainer", "build", "--fakeroot", tmp_path, file_path]
result = subprocess.run(
    build_cmd,
    text=True,
    timeout=3600
    ) 
if result.returncode == 0:
    mv_cmd = ["mv", tmp_path, container_path]
    result = subprocess.run(
        mv_cmd,
        text=True,
        timeout=3600
        ) 
#-----------------------------------------------------------------------
