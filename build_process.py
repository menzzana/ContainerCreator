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
#-----------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------
FILE_FOLDER="/var/www/html/uploads"
JOB_FOLDER="/var/www/html/jobs"
RECIPE_FILE="recipe.def"
CONTAINER_PATH="container.sif"
LOG_FILE="build.log"
JOB_FILE="job.json"
#-----------------------------------------------------------------------
def process_job(job_path):
    with open(job_path) as f:
        job = json.load(f)
    folder_path = job["folder"]
    file_path = os.path.join(folder_path, RECIPE_FILE)
    container_path = os.path.join(folder_path, CONTAINER_PATH)
    log_file = os.path.join(folder_path, LOG_FILE)
    build_cmd = ["apptainer", "build", container_path, file_path]
    with open(log_file, "w") as log:
        result = subprocess.run(build_cmd, stdout=log, stderr=subprocess.STDOUT)
    os.remove(job_path)
#-----------------------------------------------------------------------
def main():
    while True:
        for job in os.listdir(JOB_FOLDER):
            process_job(os.path.join(JOB_FOLDER, job))
        time.sleep(10)  # check every 10 seconds
#-----------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-----------------------------------------------------------------------
