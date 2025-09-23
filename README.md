# ContainerCreator

This project focuses on creating a service for the creation of containers remotely.
The project builds a REST API which can only be accessed from approved IPs.

From the approved IP, the script is capable to...

- Contact the REST API
- Send a container recipy to the server
- The server builds the container
- The server sends back the container
- The container will be accessible directly from the command line by the user.

## Requirements

- The Apache HTTP Server with **cgi-bin** More information with https://httpd.apache.org/
  - Apptainer installed
  - Bottle https://bottlepy.org/docs/dev/
  - Python3

## Installation

1. Login into the webserver
1. Goto cgi-bin folder
1. download bottle with `wget https://bottlepy.org/bottle.py`
1. upload all files to the cgi-bin folder
1. See to it to run python on the webserver.
   1. If not applicable `apt install python-is-python3`
1. Edit ip.yaml` and add approved IP addresses.
1. Create folders for upload
   `mkdir /var/www/html/uploads`
   `chown -R www-data:www-data /var/www/html/uploads`
1. Create folders for jobs
   `mkdir /var/www/html/jobs`
   `chown -R www-data:www-data /var/www/html/jobs`
1. move `apptainer-build-worker.service` to `/etc/systemd/system/`
1. Run `sudo systemctl daemon-reload`
1. Run `sudo systemctl enable --now apptainer-build-worker.service`
