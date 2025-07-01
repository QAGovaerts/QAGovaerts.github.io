---
title: Hosting My Own Overleaf Instance
date: 2025-07-01 15:00:00 +0200
categories:
  - student
tags:
  - latex
  - student
  - docker
  - overleaf
  - vm
  - mail
---

As a student, I write a lot of reports and assignments in LaTeX. [Overleaf](https://www.overleaf.com) is a really nice online LaTeX editor that is popular among my fellow students. Its collaboration tools, which allow multiple people to write together on the same project in real time, are particularly good. This made Overleaf the go-to LaTeX editor whenever we needed to write a report for a group assignment. Unfortunately, Overleaf changed its pricing plans, removing all collaboration features from the free version. Additionally, Overleaf experienced some downtimes during the deadline seasons, making it hard to rely on it when you're working close to a deadline. 

Luckily, Overleaf has an open-source community edition you can host on your own server and share with your friends. This edition includes the collaboration features and that completely for free! In this blog post I'll explain how I run my own Overleaf instance on my home server and share it with friends to work on LaTeX projects.


## Creating and Preparing a VM

I started by creating a new Ubuntu server VM in Proxmox. I've found that 4 GB of memory and 64 GB of disk space are sufficient when only a few users work simultaneously. Less disk space can also work if you only want to use the bare minimum installation and don't want to include additional LaTeX packages. After the VM's first boot, I installed updates and the QEMU Guest Agent:
```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install qemu-guest-agent
```
Because the updates included a new kernel, I restarted the VM before installing Docker. 

Because the Overleaf instance will run inside a Docker container, we need Docker installed on the VM. I followed the [official installation instructions](https://docs.docker.com/engine/install/ubuntu/) to install Docker as follows:
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install the Docker packages
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add my user to the docker group to avoid needing sudo
sudo groupadd docker
sudo usermod -aG docker $USER
```
After logging out and back in, we can test if Docker works:
```bash
docker run hello-world
```


## Installing Overleaf

I've installed Overleaf using [Overleaf Toolkit](https://github.com/overleaf/toolkit), which includes the standard tools for running a local Overleaf instance. This toolkit makes installing and maintaining an own Overleaf instance really easy. The following installation steps are from the [toolkits documentation](https://github.com/overleaf/toolkit/blob/master/doc/README.md).

### Install
We start by cloning the Overleaf Toolkit repository:
```bash
git clone https://github.com/overleaf/toolkit.git ./overleaf-toolkit
```
Next, we move into the cloned directory
```bash
cd ./overleaf-toolkit
```
From here, we can control the Overleaf instance.

### Initialize the Configuration
We can create a new standard configuration by running:
```bash
bin/init
```
This will create the following three configuration files inside the `config` subdirectory:
- `overleaf.rc` : the main top-level configuration file
- `variables.env` : environment variables loaded into the Docker container
- `version` : the version of the Docker image to use

For now we can leave the default configuration values.

### First Run
Starting the instance is as easy as running:
```bash
bin/up
```
This starts two database containers (Mongo and Redis) and one ShareLaTeX container, which contains all the Overleaf logic. We are attached to this ShareLaTeX container so pressing `CTRL+C` stops the containers. 

### Creating the Admin Account
We first need to create an admin account which we can later use to add new users. We can create this account by going to [http://localhost/launchpad](http://localhost/launchpad). Because I'm running Overleaf inside a VM, I allowed incoming HTTP traffic in the Proxmox firewall for the VM, and visited the launchpad endpoint by replacing `localhost` with the VM's local IP address. When the admin account is created, we can log in as admin on [http://localhost/login](http://localhost/login). 

We can create projects like any other user, and as admins, we also have the admin options in the top left corner. Via the `Manage Site` page, we can set messages that are visible for all users. Via the `Manage Users` page, we can register new users by providing their email addresses. However, before we can invite new users, we need to configure a mail account for the instance.

### Configuring the Overleaf Instance
After we've tested that the instance works, we can change the configuration to better suit our preferences. We use the environment variables in the `config/variables.env` file that we created earlier. 

#### Giving the Instance a Name
We can change the name of our instance by setting the `OVERLEAF_APP_NAME` and `OVERLEAF_NAV_TITLE` variables. We can also set footer text, for example, with an email address to reach the admin:
```
OVERLEAF_ADMIN_EMAIL=adminmail@maildomain

OVERLEAF_LEFT_FOOTER='[{"text": "Contact me", "url": "mailto:adminmail@maildomain"}]'
OVERLEAF_RIGHT_FOOTER='[{"text": "Enjoy"}]'
```

#### Public Access to the Instance
I wanted to share my instance with friends so we could work together on LaTeX projects. Therefore, I needed to make it available on the Internet. I used my [Cloudflare Tunnel setup](/posts/setting_up_nextcloud_and_cloudflare_tunnels/#cloudflare-tunnel), which I configured earlier, to point a domain to my instance through this tunnel. For this to work, I also needed to set the `OVERLEAF_SITE_URL` environment variable to this same domain.

Since I use Cloudflare to enable HTTPS for my instance, I did not need to enable Nginx in the configuration files.
#### Configuring Mail
To invite my friends, I needed to configure a mail account for my Overleaf instance so that the instance could send invitation emails. I like to use [Migadu](https://migadu.com) to give my self-hosted projects an email account. After creating a new mail box for my Overleaf instance, I configured it as follows:
```
OVERLEAF_EMAIL_FROM_ADDRESS=overleaf@mymaildomain.be
OVERLEAF_EMAIL_SMTP_HOST=smtp.migadu.com
OVERLEAF_EMAIL_SMTP_PORT=465
OVERLEAF_EMAIL_SMTP_SECURE=true
OVERLEAF_EMAIL_SMTP_USER=overleaf@mymaildomain.be
OVERLEAF_EMAIL_SMTP_PASS=**the-mailbox-password**
OVERLEAF_EMAIL_SMTP_NAME=overleaf@mymaildomain.be
# OVERLEAF_EMAIL_SMTP_LOGGER=false
# OVERLEAF_EMAIL_SMTP_TLS_REJECT_UNAUTH=true
# OVERLEAF_EMAIL_SMTP_IGNORE_TLS=false
OVERLEAF_CUSTOM_EMAIL_FOOTER="Here I put a personal message to my friends"
```

> Whenever you change anything in the configuration files, you need to remove and restart the containers as follows:
> ```bash
> bin/docker-compose down
> bin/docker-compose up -d
> ```
{: .prompt-warning }


## Building Our Own ShareLaTeX Image
The default ShareLaTeX image is fine if you only need basic LaTeX features. However, I needed more packages than the ShareLaTeX image offers. The [documentation](https://github.com/overleaf/toolkit/blob/master/doc/ce-upgrading-texlive.md) mentions a methodology for installing extra packages in the running container. While this works fine, those steps must be repeated every time the container is destroyed. Therefore, I created my own Docker image based on the ShareLaTeX image, which includes all these extra packages and additional support. The Dockerfile I used for this is based on the [sharelatex-full](https://github.com/tuetenk0pp/sharelatex-full) image.

```docker
FROM sharelatex/sharelatex:5.5.1

SHELL ["/bin/bash", "-cx"]

# update tlmgr itself
RUN wget "https://mirror.ctan.org/systems/texlive/tlnet/update-tlmgr-latest.sh" \
    && sh update-tlmgr-latest.sh \
    && tlmgr --version

# enable tlmgr to install ctex
RUN tlmgr update texlive-scripts 

# update packages
RUN tlmgr update --all

# install all the packages
RUN tlmgr install scheme-full

# recreate symlinks
RUN tlmgr path add

# update system packages
RUN apt-get update && apt-get upgrade -y

# install inkscape for svg support
RUN apt-get install inkscape -y

# install lilypond
RUN apt-get install lilypond -y
```
{: file='mysharelatex/Dockerfile'}

I can then build this image by running the following command in the same directory where the Dockerfile is stored.
```bash
docker build -t local/mysharelatex:5.5.1 .
```

Lastly, I needed to configure the toolkit to use this image by setting:
```
OVERLEAF_IMAGE_NAME=local/mysharelatex
```
{: file='config/overleaf.rc'}
In the `overleaf.rc` config file and the correct image version (`5.5.1` in this case) in the `version` config file.

Now I can use this image by destroying the existing containers and starting the new containers as follows:
```bash
bin/docker-compose down
bin/docker-compose up -d
```


## Making Backups
Because my friends and I are using this instance for important projects, I wanted to have backups of all the project files. In addition to the backups Proxmox already makes of the entire VM, I also created a little backup script to backup the configuration files, project files, and the MongoDB database. I did not back up the Redis database since it only stores the current sessions and pending document updates before they are flushed to the MongoDB database (see the [Overleaf Developer Wiki](https://github.com/overleaf/overleaf/wiki/Data-and-Backups)). 

### Backup Script

```bash
#!/bin/bash

# Variables
FILE_TIMESTAMP=$(date "+%Y%m%d-%H%M%S")
LOG_FILE="/home/myuser/overleaf/backup_logs/backup-$FILE_TIMESTAMP.log"
ERROR_COUNT=0
MAX_BACKUPS=10

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "Starting backup task"
echo "[$(date)] INFO: Backup task started" >> "$LOG_FILE"
echo "Log file: $LOG_FILE"

# Function to send ntfy notification
send_ntfy_notification() {
  local message=$1
  curl \
     -T "$LOG_FILE" \
     -H "Title: $message" \
     -H "Tags: file_cabinet,open_file_folder" \
     -H "Filename: backup_logs_${FILE_TIMESTAMP}.txt" \
     https://ntfy.my-website.be/backups
}

################
### PROJECTS ###
################

cd /home/myuser/overleaf/overleaf-toolkit
echo "[$(date)] INFO: Creating backup of all projects" >> "$LOG_FILE"

# Create destination dir
EXPORT_DIR="/mnt/mynas/backup/projects"
DEST_DIR="$EXPORT_DIR/$FILE_TIMESTAMP"
mkdir $DEST_DIR

# Test if destination dir exists
if [ ! -d "$DEST_DIR" ]; then
  echo "[$(date)] ERROR: Destination directory $DEST_DIR does not exist." >> "$LOG_FILE"
  send_ntfy_notification "Overleaf Backup Error: directory $DEST_DIR does not exist."
  exit 1
fi

# Make project backups
bin/docker-compose exec sharelatex /bin/bash -ce "cd /overleaf/services/web && node modules/server-ce-scripts/scripts/export-user-projects.mjs --export-all --output-dir /mnt/backup/projects/$FILE_TIMESTAMP" >> "$LOG_FILE"

if [ $? -eq 0 ]; then
  echo "[$(date)] INFO: projects successfully exported." >> "$LOG_FILE"
else
  echo "[$(date)] ERROR: error while exporting projects." >> "$LOG_FILE"
  ((ERROR_COUNT++))
fi

# Manage backups: Keep only the latest 10 backups
BACKUPS=($(ls -t "$EXPORT_DIR"))  # List export directories sorted by modification time
BACKUP_COUNT=${#BACKUPS[@]}

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
  echo "[$(date)] INFO: Found $BACKUP_COUNT project exports. Removing oldest export to retain only $MAX_BACKUPS." >> "$LOG_FILE"
  for ((i = MAX_BACKUPS; i < BACKUP_COUNT; i++)); do
    echo "[$(date)] INFO: Deleting old export ${BACKUPS[$i]}." >> "$LOG_FILE"
    rm -rdf "$EXPORT_DIR/${BACKUPS[$i]}" && rmdir "$EXPORT_DIR/${BACKUPS[$i]}"
    if [ $? -ne 0 ]; then
      echo "[$(date)] ERROR: Failed to delete ${BACKUPS[$i]}." >> "$LOG_FILE"
    else
      echo "[$(date)] INFO: Deleted ${BACKUPS[$i]} successfully." >> "$LOG_FILE"
    fi
  done
else
  echo "[$(date)] INFO: Project export count is within limit ($BACKUP_COUNT/$MAX_BACKUPS). No deletion needed." >> "$LOG_FILE"
fi

#####################
### STOP OVERLEAF ###
#####################

cd /home/myuser/overleaf/overleaf-toolkit
echo "[$(date)] INFO: Stopping overleaf" >> "$LOG_FILE"
docker stop sharelatex

if [ $? -eq 0 ]; then
  echo "[$(date)] INFO: sharelatex container successfully stopped." >> "$LOG_FILE"
else
  echo "[$(date)] ERROR: error while stopping sharelatex container." >> "$LOG_FILE"
  ((ERROR_COUNT++))
fi


#####################
### CONFIGURATION ###
#####################

DEST_DIR="/mnt/mynas/backup/config"

echo "Backing up configuration"
echo "[$(date)] INFO: Starting backup of configuration to $DEST_DIR" >> "$LOG_FILE"

# Test if destination dir exists
if [ ! -d "$DEST_DIR" ]; then
  echo "[$(date)] ERROR: Destination directory $DEST_DIR does not exist." >> "$LOG_FILE"
  send_ntfy_notification "Overleaf Backup Error: directory $DEST_DIR does not exist."
  exit 1
fi

bin/backup-config $DEST_DIR >> "$LOG_FILE"

# Check if the backup was successful
if [ $? -eq 0 ]; then
  echo "[$(date)] INFO: Config backup completed successfully." >> "$LOG_FILE"
else
  echo "[$(date)] ERROR: Config backup encountered errors." >> "$LOG_FILE"
  ((ERROR_COUNT++))
fi


###################
### FILE SYSTEM ###
###################

SOURCE_DIR="/home/myuser/overleaf/overleaf-toolkit/data/overleaf"
DEST_DIR="/mnt/mynas/backup/filesystem"

echo "Backing up file system"
echo "[$(date)] INFO: Starting backup of file system to $DEST_DIR" >> "$LOG_FILE"

# Test if source dir exists
if [ ! -d "$SOURCE_DIR" ]; then
  echo "[$(date)] ERROR: Source directory $SOURCE_DIR does not exist." >> "$LOG_FILE"
  send_ntfy_notification "Overleaf Backup Error: directory $SOURCE_DIR does not exist."
  exit 1
fi

# Test if destination dir exists
if [ ! -d "$DEST_DIR" ]; then
  echo "[$(date)] ERROR: Destination directory $DEST_DIR does not exist." >> "$LOG_FILE"
  send_ntfy_notification "Overleaf Backup Error: directory $DEST_DIR does not exist."
  exit 1
fi

# Create a zip file of the source directory
ZIP_FILE="$DEST_DIR/overleaf-backup-$FILE_TIMESTAMP.zip"
echo "[$(date)] INFO: Creating backup zip file $ZIP_FILE." >> "$LOG_FILE"
zip -qr "$ZIP_FILE" "$SOURCE_DIR" >> "$LOG_FILE"

# Check if the backup was successful
if [ $? -eq 0 ]; then
  echo "[$(date)] INFO: File system backup completed successfully." >> "$LOG_FILE"
else
  echo "[$(date)] ERROR: File system backup encountered errors." >> "$LOG_FILE"
  ((ERROR_COUNT++))
fi

# Manage backups: Keep only the latest 10 backups
BACKUPS=($(ls -t "$DEST_DIR"/*.zip))  # List zip files sorted by modification time
BACKUP_COUNT=${#BACKUPS[@]}

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
  echo "[$(date)] INFO: Found $BACKUP_COUNT backups. Removing oldest backups to retain only $MAX_BACKUPS." >> "$LOG_FILE"
  for ((i = MAX_BACKUPS; i < BACKUP_COUNT; i++)); do
    echo "[$(date)] INFO: Deleting old backup ${BACKUPS[$i]}." >> "$LOG_FILE"
    rm -f "${BACKUPS[$i]}"
    if [ $? -ne 0 ]; then
      echo "[$(date)] ERROR: Failed to delete ${BACKUPS[$i]}." >> "$LOG_FILE"
    else
      echo "[$(date)] INFO: Deleted ${BACKUPS[$i]} successfully." >> "$LOG_FILE"
    fi
  done
else
  echo "[$(date)] INFO: Backup count is within limit ($BACKUP_COUNT/$MAX_BACKUPS). No deletion needed." >> "$LOG_FILE"
fi


#############
### MONGO ###
#############

DEST_DIR="/mnt/mynas/backup/mongodb"

echo "Backing up mongodb"
echo "[$(date)] INFO: Starting backup of mongodb to $DEST_DIR" >> "$LOG_FILE"

# Test if destination dir exists
if [ ! -d "$DEST_DIR" ]; then
  echo "[$(date)] ERROR: Destination directory $DEST_DIR does not exist." >> "$LOG_FILE"
  send_ntfy_notification "Overleaf Backup Error: directory $DEST_DIR does not exist."
  exit 1
fi

# Create archive with mongodump
echo "[$(date)] INFO: Creating backup gzip file $DEST_DIR/overleaf_mongobd_backup_$FILE_TIMESTAMP.gz." >> "$LOG_FILE"
mongodump -h="localhost:27017" --archive="$DEST_DIR/overleaf_mongobd_backup_$FILE_TIMESTAMP.gz" --gzip --quiet >> "$LOG_FILE"

# Check if the backup was successful
if [ $? -eq 0 ]; then
  echo "[$(date)] INFO: MongoDB backup completed successfully." >> "$LOG_FILE"
else
  echo "[$(date)] ERROR: MongoDB backup encountered errors." >> "$LOG_FILE"
  ((ERROR_COUNT++))
fi

# Manage backups: Keep only the latest 10 backups
BACKUPS=($(ls -t "$DEST_DIR"/*.gz))  # List gzip files sorted by modification time
BACKUP_COUNT=${#BACKUPS[@]}

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
  echo "[$(date)] INFO: Found $BACKUP_COUNT backups. Removing oldest backups to retain only $MAX_BACKUPS." >> "$LOG_FILE"
  for ((i = MAX_BACKUPS; i < BACKUP_COUNT; i++)); do
    echo "[$(date)] INFO: Deleting old backup ${BACKUPS[$i]}." >> "$LOG_FILE"
    rm -f "${BACKUPS[$i]}"
    if [ $? -ne 0 ]; then
      echo "[$(date)] ERROR: Failed to delete ${BACKUPS[$i]}." >> "$LOG_FILE"
    else
      echo "[$(date)] INFO: Deleted ${BACKUPS[$i]} successfully." >> "$LOG_FILE"
    fi
  done
else
  echo "[$(date)] INFO: Backup count is within limit ($BACKUP_COUNT/$MAX_BACKUPS). No deletion needed." >> "$LOG_FILE"
fi


###########
### End ###
###########

# Manage logfiles: Keep only the latest 10 logs
LOGS=($(ls -t "/home/myuser/overleaf/backup_logs"/*.log))  # List gzip files sorted by modification time
LOG_COUNT=${#LOGS[@]}

if [ "$LOG_COUNT" -gt "$MAX_BACKUPS" ]; then
  echo "[$(date)] INFO: Found $LOG_COUNT logfiles. Removing oldest logs to retain only $MAX_BACKUPS." >> "$LOG_FILE"
  for ((i = MAX_LOGS; i < LOG_COUNT; i++)); do
    echo "[$(date)] INFO: Deleting old logfile ${LOGS[$i]}." >> "$LOG_FILE"
    rm -f "${LOGS[$i]}"
    if [ $? -ne 0 ]; then
      echo "[$(date)] ERROR: Failed to delete ${LOGS[$i]}." >> "$LOG_FILE"
    else
      echo "[$(date)] INFO: Deleted ${LOGS[$i]} successfully." >> "$LOG_FILE"
    fi
  done
else
  echo "[$(date)] INFO: log count is within limit ($LOG_COUNT/$MAX_LOGS). No deletion needed." >> "$LOG_FILE"
fi

# Start overleaf
echo "[$(date)] INFO: Starting overleaf" >> "$LOG_FILE"
docker start sharelatex

if [ $? -eq 0 ]; then
  echo "[$(date)] INFO: sharelatex container successfully started." >> "$LOG_FILE"
else
  echo "[$(date)] ERROR: error while starting sharelatex container." >> "$LOG_FILE"
  ((ERROR_COUNT++))
fi

# If there are errors, send a notification
if [ $ERROR_COUNT -gt 0 ]; then
  echo "[$(date)] INFO: Backup completed with $ERROR_COUNT error(s)." >> "$LOG_FILE"
  send_ntfy_notification "Overleaf backup completed with $ERROR_COUNT error(s)."
else
  echo "[$(date)] INFO: Backup completed successfully with no errors." >> "$LOG_FILE"
fi

echo "Backup process completed"

exit 0
```
{: file='backup.sh'}

This script does a series of actions to back up different files from the Overleaf instance. It logs everything to a log file and sends me a message over an [Ntfy instance I host](/posts/getting_notified_with_ntfy/) if an error occurs. The backups are saved to a NAS share mounted to the VM. 

A recent version of the ShareLaTeX image includes a script that we can use to export all projects present in the instance. It is called in the script in line 45. You can run the following command to see all available options:
```bash
bin/docker-compose exec sharelatex /bin/bash -ce "cd /overleaf/services/web && node modules/server-ce-scripts/scripts/export-user-projects.mjs --help"
```
The `--export-all` option results in one zip file for each user, each containing a zip file for each of the user's projects. For the export to work, I needed to mount the destination directory to the ShareLaTeX container by adding a line to the `docker-compose.base.yml` file:
```yaml
volumes:
    - "${OVERLEAF_DATA_PATH}:${OVERLEAF_IN_CONTAINER_DATA_PATH}"
    - "/mnt/mynas/backup/projects:/mnt/backup/projects"
```
{: file='lib/docker-compose.base.yml'}

To prevent corruption when making a backup of the file system the ShareLaTeX container is using, it is best to stop this container while making a backup. At the end of the script, we can start this container again. This means the Overleaf instance will be unavailable while the backup script runs.

We can use a handy tool called [mongodump](https://docs.mongodb.com/manual/reference/program/mongodump/) in line 191 to back up the MongoDB.

Lastly, the script includes some logic to clean up and remove old backups. I configured it so that only the 10 most recent backups are retained.

### Automatic Backup
By making the backup script executable (`chmod +x backup.sh`), we can add a cron job to run this script automatically:
```
50 5 * * * /home/myuser/overleaf/backup.sh
```
{: file='crontab'}
I configured it to run daily at 5:50 in the morning since it is unlikely my friends will be using the instance so early in the morning. 


## Conclusion
I've hosted this instance for almost a year, and I'm really happy I put the time and effort into setting it up. It allows my friends and me to continue using Overleaf as we were used to with the official Overleaf instance. The only issue I've encountered is that sometimes the online editor does not load the compiled PDF file. Luckily, this issue only happens sporadically and can be fixed by a simple container restart. 