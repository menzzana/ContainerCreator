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
from bottle import Bottle, run, request, response
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
# Variables
#-----------------------------------------------------------------------
VERSION="0.1"
IP_ADRESS_FILE="ip.yaml"
FILE_FOLDER="/var/www/html/uploads"
RECIPE_FILE="recipe.def"
TEMP_CONTAINER="tmp.sif"
CONTAINER_PATH="container.sif"
LOG_FILE="build.log"
items = {}
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
# Main
#-----------------------------------------------------------------------
# curl http://<IP>/cgi-bin/index.py/test
@app.route('/test')
def test_connection():
    client_ip = request.remote_addr
    return {"Connection": "established", "Version": VERSION, "IP": client_ip, "Approved": checkIP()}
#-----------------------------------------------------------------------
# curl -X POST -F "file=@file=@<name>.def" http://<IP>/cgi-bin/index.py/upload
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
# curl http://<IP>/cgi-bin/index.py/create
@app.get('/create/<build_id>')
def create(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    if shutil.which("apptainer") is None:
        return {"error": "AppTainer not installed"}
    folder_path = os.path.join(FILE_FOLDER,build_id)
    log_file = os.path.join(folder_path, LOG_FILE)
    with open(log_file, "w") as f:
        subprocess.Popen(
            [sys.executable, "create.py", folder_path],
            stdout=f,
            stderr=subprocess.STDOUT
        )
    return {"message": "Creation process started", "id": build_id}
#-----------------------------------------------------------------------
@app.get('/download/<build_id>')
def download(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    folder_path = os.path.join(FILE_FOLDER, build_id)
    container_path = os.path.join(folder_path, CONTAINER_PATH)
    if not os.path.exists(container_path):
        response.status = 404
        return {"error": "Container not found"}
    try:
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{container_path}"'
        return static_file(f"{container_path}", root=folder_path, download=True)
    except Exception as e:
        response.status = 500
        return {"error": "Download failed", "details": str(e)}
#-----------------------------------------------------------------------
# curl http://<IP>/cgi-bin/index.py/status/<ID>
@app.get('/status/<build_id>')
def status(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
    folder_path = os.path.join(FILE_FOLDER, build_id)
    recipe_path = os.path.join(folder_path, RECIPE_FILE)
    tmp_path = os.path.join(folder_path, TEMP_CONTAINER)
    container_path = os.path.join(folder_path, CONTAINER_PATH)
    status_info = {
        "id": build_id,
        "folder_exists": os.path.exists(folder_path),
        "recipe_exists": os.path.exists(recipe_path),
        "temporary_file_exists": os.path.exists(tmp_path),
        "container_exists": os.path.exists(container_path)
        }
    if os.path.exists(container_path):
        status_info["container_size_bytes"] = os.path.getsize(container_path)
        status_info["download_url"] = container_path
        status_info["status"] = "ready"
    else:
        status_info["status"] = "building or failed"
    return status_info
#-----------------------------------------------------------------------
# curl http://<IP>/cgi-bin/index.py/cleanup/<ID>
@app.get('/cleanup/<build_id>')
def cleanup_build(build_id):
    if not checkIP():
        return {"error": "Not allowed"}
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
