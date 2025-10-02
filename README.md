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
  - fakeroot installed (Default on many UBUNTU installations)
  - Bottle https://bottlepy.org/docs/dev/
  - Python3

## Installation

1. Login into the webserver
1. Goto cgi-bin folder
1. download bottle with `wget https://bottlepy.org/bottle.py`
1. upload all files to the cgi-bin folder
1. See to it to run python on the webserver.
   1. If not applicable `apt install python-is-python3`
1. Edit `ip.yaml` and add approved IP addresses that you are planning to run the client from.
1. Create folders for upload
   `mkdir /var/www/html/uploads`
   `chown -R www-data:www-data /var/www/html/uploads`
1. Add permission for fakeroot by
   1. `echo "www-data::100000:65536" >> /etc/subuid`
   1. `echo "www-data::100000:65536" >> /etc/subgid`
   1. In this case **www-data** is the apache user, which could be different
1. `build_container.sh` is the client. Move to the computer you would like to run it from.
1. Edit `build_container.sh` and substitute [IP] for the IP address of the webserver.
