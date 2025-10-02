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
from bottle import Bottle, run, request, response, static_file
import os
import subprocess
import shutil
import re
import base64
import time
import sys
import json
import yaml
import random
import string
from enum import Enum
#-----------------------------------------------------------------------
app = Bottle()
#-----------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------
VERSION="0.1"
IP_ADRESS_FILE="ip.yaml"
FILE_FOLDER="/var/www/html/uploads"
RECIPE_FILE="recipe.def"
CONTAINER_PATH="container.sif"
LOG_FILE="build.log"
LOCK_FILE="create.lock"
#-----------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------
# Check that the command originates from approved IPs
def checkIP():
    client_ip = request.remote_addr
    with open(IP_ADRESS_FILE, "r") as f:
        ips = yaml.safe_load(f)
    ip_list = ips.get("ip", [])
    return client_ip in ip_list
#-----------------------------------------------------------------------
def cleanOldBuilds():
    for build in os.listdir(FILE_FOLDER):
        build_path = os.path.join(FILE_FOLDER, build)
        mtime = os.path.getmtime(build_path)
        age_seconds = time.time() - mtime
        if age_seconds > 3600:
            shutil.rmtree(build_path)
#-----------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------
# curl http://<IP>/cgi-bin/ContainerCreator/index.py/test
@app.route('/test')
def test_connection():
    client_ip = request.remote_addr
    return {"Connection": "established", "Version": VERSION, "IP": client_ip, "Approved": checkIP()}
#-----------------------------------------------------------------------
# curl -X POST -F "file=@<name>.def" http://<IP>/cgi-bin/ContainerCreator/index.py/upload
@app.post('/upload')
def upload():
    if not checkIP():
        return {"error": "Not allowed"}
    upload = request.files.get('file')
    if not upload:
        return {"error": "No file uploaded"}
    data = upload.file.read().decode("utf-8")
    random_string = ''.join(random.choices(string.ascii_letters, k=10))
    folder_path = os.path.join(FILE_FOLDER,random_string)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, RECIPE_FILE)
    with open(file_path, "w") as f:
        f.write(data)
    return {"message": "Uploaded file", "id": random_string}
#-----------------------------------------------------------------------
# curl http://<IP>/cgi-bin/ContainerCreator/index.py/create
@app.get('/create/<build_id>')
def create(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    if shutil.which("apptainer") is None:
        return {"error": "AppTainer not installed"}
    folder_path = os.path.join(FILE_FOLDER,build_id)
    lock_file = os.path.join(folder_path,LOCK_FILE)
    if os.path.exists(lock_file):
        return {"error": "Creation process is already running"}
    log_file = os.path.join(folder_path, LOG_FILE)
    with open(log_file, "x") as log:
        proc=subprocess.Popen(
            [sys.executable,'build_process.py','create',build_id],
            stdout=log,
            stderr=subprocess.STDOUT
            )
    with open(lock_file, "w") as f:
        json.dump({"pid": proc.pid, "id": build_id}, f)
    return {"message": "Creation process started", "id": build_id}
#-----------------------------------------------------------------------
# curl -o <FILENAME>.sif http://<IP>/cgi-bin/ContainerCreator/index.py/download/<ID>
@app.get('/download/<build_id>')
def download(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    folder_path = os.path.join(FILE_FOLDER, build_id)
    if not os.path.exists(os.path.join(folder_path, CONTAINER_PATH)):
        response.status = 404
        return {"error": "Container not found"}
    try:
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{CONTAINER_PATH}"'
        return static_file(CONTAINER_PATH, root=folder_path, download=True)
    except Exception as e:
        response.status = 500
        return {"error": "Download failed", "details": str(e)}
#-----------------------------------------------------------------------
# curl http://<IP>/cgi-bin/ContainerCreator/index.py/status/<ID>
@app.get('/status/<build_id>')
def status(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    folder_path = os.path.join(FILE_FOLDER, build_id)
    recipe_path = os.path.join(folder_path, RECIPE_FILE)
    container_path = os.path.join(folder_path, CONTAINER_PATH)
    lock_file = os.path.join(folder_path,LOCK_FILE)
    status_info = {
        "id": build_id,
        "folder_exists": os.path.exists(folder_path),
        "job_exists": os.path.exists(lock_file),
        "recipe_exists": os.path.exists(recipe_path),
        "container_exists": os.path.exists(container_path)
        }
    if os.path.exists(container_path):
        status_info["container_size_bytes"] = os.path.getsize(container_path)
        status_info["download_url"] = container_path
        status_info["status"] = "ready"
        return status_info
    if os.path.exists(lock_file):
        status_info["status"] = "building"
    else:
        status_info["status"] = "failed"
    return status_info
#-----------------------------------------------------------------------
# curl -o <LOGFILENAME> http://<IP>/cgi-bin/ContainerCreator/index.py/log/<ID>
@app.get('/log/<build_id>')
def getLog(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    folder_path = os.path.join(FILE_FOLDER, build_id)
    if not os.path.exists(os.path.join(folder_path, LOG_FILE)):
        response.status = 404
        return {"error": "Container not found"}
    try:
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{LOG_FILE}"'
        return static_file(LOG_FILE, root=folder_path, download=True)
    except Exception as e:
        response.status = 500
        return {"error": "Download failed", "details": str(e)}
#-----------------------------------------------------------------------
# curl http://<IP>/cgi-bin/ContainerCreator/index.py/cleanup/<ID>
@app.get('/cleanup/<build_id>')
def cleanup_build(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    cleanOldBuilds()
    folder_path = os.path.join(FILE_FOLDER, build_id)
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            return {"message": "Build files cleaned up", "build_id": build_id}
        except Exception as e:
            return {"error": "Cleanup failed", "details": str(e)}
    else:
        return {"message": "Build folder not found", "id": build_id}
#-----------------------------------------------------------------------
if __name__ == "__main__":
    run(app, debug=True, server='cgi')     
#-----------------------------------------------------------------------
