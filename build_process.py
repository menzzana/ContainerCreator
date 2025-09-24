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
from concurrent.futures import ProcessPoolExecutor, as_completed
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
def process_job(job_path, age):
    try:
        if not os.path.exists(job_path):
            return
        with open(job_path) as f:
            job = json.load(f)
        folder_path = job["folder"]
        if age > 3600:
            os.remove(job_path)
            shutil.rmtree(folder_path)
            return
        file_path = os.path.join(folder_path, RECIPE_FILE)
        container_path = os.path.join(folder_path, CONTAINER_PATH)
        log_file = os.path.join(folder_path, LOG_FILE)
        build_cmd = ["apptainer", "build", container_path, file_path]
        with open(log_file, "x") as log:
            result = subprocess.run(build_cmd, stdout=log, stderr=subprocess.STDOUT)
        os.remove(job_path)
    except FileExistsError:
        return
    except Exception as e:
        print(f"Build failed for {job_path}: {e}")
#-----------------------------------------------------------------------
def main():
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = set()
        while True:
            for job in os.listdir(JOB_FOLDER):
                job_path = os.path.join(JOB_FOLDER, job)
                mtime = os.path.getmtime(job_path)
                age_seconds = time.time() - mtime
                future = executor.submit(process_job, job_path, age_seconds)
                futures.add(future)
            done = {f for f in futures if f.done()}
            futures -= done
            time.sleep(10)
#-----------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-----------------------------------------------------------------------
