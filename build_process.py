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
import json
import os
import subprocess
import time
import sys
#-----------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------
FILE_FOLDER="/var/www/html/uploads"
RECIPE_FILE="recipe.def"
CONTAINER_PATH="container.sif"
LOG_FILE="build.log"
LOCK_FILE="create.lock"
#-----------------------------------------------------------------------
def create_container(build_id):
    try:
        folder_path = os.path.join(FILE_FOLDER,build_id)
        if not os.path.exists(folder_path):
            return        
        file_path = os.path.join(folder_path, RECIPE_FILE)
        container_path = os.path.join(folder_path, CONTAINER_PATH)
        log_file = os.path.join(folder_path, LOG_FILE)
        lock_file = os.path.join(folder_path,LOCK_FILE)
        result = subprocess.run(
            ["apptainer", "build", "--fakeroot", container_path, file_path],
            check=True
            )
    except FileExistsError:
        return
    except Exception as e:
        print(f"Build failed for {build_id}: {e}")
    finally:
        os.remove(lock_file)
#-----------------------------------------------------------------------
if __name__ == '__main__':
    args = sys.argv[2:]
    if sys.argv[1] == 'create':
        create_container(*args)
#-----------------------------------------------------------------------
