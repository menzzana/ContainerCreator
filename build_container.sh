#!/bin/bash
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
# Constants
#-----------------------------------------------------------------------
SERVER="http://<IP>/cgi-bin/ContainerCreator/index.py"
#-----------------------------------------------------------------------
DEF_FILE=""
SANDBOX=true
VERBOSE=false
TEST=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            echo "Usage: [PARAM] <recipe.def>"
            echo "-n, --nosandbox. Does not convert a container into a sandbox"
            echo "-v, --verbose. Shows log while container is being created"
            echo "-h, --help. Shows how to use and available parameters"
            echo "-t, --test. Test connection to the remote server" 
            exit 0
            ;;
        -n|--nosandbox)
            SANDBOX=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--test)
            TEST=true
            shift
            ;;
        -*)
            error "Unknown option: $1"
            ;;
        *)
            if [[ -z "$DEF_FILE" ]]; then
                DEF_FILE="$1"
            else
                error "Multiple definition files not supported"
            fi
            shift
            ;;
    esac
done
if [[ $SERVER == *"<IP>"* ]]; then
    echo "Error: No IP is set"
    exit 1
fi
if [ "$TEST" = true ]; then
    CONNECTION=$(curl -s "$SERVER/test" | grep -Po "established")
    APPROVAL=$(curl -s "$SERVER/test" | grep -Po "Approved: true")
    if [[ $CONNECTION != "established" ]]; then
        echo "No connection to remote building server"
        exit 1
    fi  
    if [[ $APPROVAL == "\"Approved\": false" ]]; then
        echo "Connection is not accepted to remote building server"
        exit 1
    fi  
    echo "Connection is accepted to remote building server"
    exit 0
fi
CONTAINER_COMMAND=""
if command -v singularity >/dev/null 2>&1; then
    CONTAINER_COMMAND="singularity"
fi
if command -v apptainer >/dev/null 2>&1; then
    CONTAINER_COMMAND="apptainer"
fi
if [ -z "$CONTAINER_COMMAND" ]; then
    echo "Error: No command for creating containers is found"
    exit 1
fi
if [ -z "$DEF_FILE" ]; then
    echo "Error: No definition file, please --help for available commands."
    exit 1
fi
if [ ! -f "$DEF_FILE" ]; then
    echo "Error: File '$DEF_FILE' not found."
    exit 1
fi
# Upload the .def file
echo "Uploading $DEF_FILE..."
BUILD_ID=$(curl -s -X POST -F "file=@$DEF_FILE" "$SERVER/upload" \
           | grep -Po '"id":\s*"\K[^"]+')
if [ -z "$BUILD_ID" ]; then
    echo "Upload failed."
    exit 1
fi
echo "Uploaded! Build ID: $BUILD_ID"
# Building
curl -s "$SERVER/create/$BUILD_ID" > /dev/null
echo "Build queued..."
# Check status every 2 seconds. Stream log while waiting
LOG_URL="$SERVER/log/$BUILD_ID"
TMP_LOG=$(mktemp)
trap "rm -f $TMP_LOG; exit" INT TERM
LAST_SIZE=0
echo "Build started..."
while true; do
    if [ "$VERBOSE" = true ]; then
        curl -s --fail -o "$TMP_LOG" "$LOG_URL"
        CUR_SIZE=$(stat -c%s "$TMP_LOG")
        if [ "$CUR_SIZE" -lt "$LAST_SIZE" ]; then
            LAST_SIZE=0
        fi
        if [ "$CUR_SIZE" -gt "$LAST_SIZE" ]; then
            tail -c +"$((LAST_SIZE+1))" "$TMP_LOG"
            LAST_SIZE=$CUR_SIZE
        fi
    fi
    STATUS=$(curl -s "$SERVER/status/$BUILD_ID" | grep -Po '"status":\s*"\K[^"]+')
    if [ "$STATUS" == "ready" ]; then
        echo "Build finished!"
        break
    fi
    if [ "$STATUS" == "failed" ]; then
        echo "Build failed!"
        break
    fi
    sleep 2
done
rm -f "$TMP_LOG"
# Download the container
OUTPUT_FILE="$(basename "$DEF_FILE" .def).sif"
curl -s -L -o "$OUTPUT_FILE" "$SERVER/download/$BUILD_ID" > /dev/null
echo "Download complete: $OUTPUT_FILE"
# Clean Up
echo "Removing old files"
curl -s "$SERVER/cleanup/$BUILD_ID" > /dev/null
if [ "$SANDBOX" = true ]; then
    echo "Convert to sandbox"
    $CONTAINER_COMMAND build --sandbox "$(basename "$OUTPUT_FILE" .sif)" "$OUTPUT_FILE"
    rm "$OUTPUT_FILE"
fi
echo "Ready!"
