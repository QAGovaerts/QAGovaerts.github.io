---
title: Setting up Nextcloud and Cloudflare Tunnels
date: 2023-09-12 13:00:00 +0200
categories: [nextcloud]
tags: [homeserver, docker, nextcloud, container, cloudflare, dns, truenas, nas, tunnel] # TAG names should always be lowercase
---

I wanted a way to easily access my files on my TrueNAS from outside my home network and send share links to other people, so they can access a specific file or folder. Do achieve this I set up Nextcloud in my home server and used a Cloudflare tunnel to access Nextcloud from anywhere.


## Cloudflare tunnel

Setting up a Cloudflare tunnel was really easy since I already had Cloudflare configured to manage the domain that I was going to use. I followed [this guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/install-and-setup/tunnel-guide/remote/) from Cloudflare and decided to run the Cloudflared connector in a dedicated Debian container in Proxmox. That way I can easily control what services the connector can access with firewall rules in Proxmox. 

I made a new container in Proxmox and gave it a static IP address. After adding the following firewall rules to drop all traffic going to my local network I started the container.

|Type|Action|Macro|Interface|Protocol|Source|S. Port|Destination|D. Port|
|---|---|---|---|---|---|---|---|---|
|out|DROP||net0||||192.168.0.0/24||
|in|ACCEPT|SSH|net0||192.168.0.0/24||||
|in|ACCEPT|Ping|net0||192.168.0.0/24||||

Once I logged in to the container via SSH, I installed updates and installed `curl`

```shell
apt update
apt upgrade
apt install curl
```

Now I could install the Cloudflared service with the commands I got from the Cloudflare tunnels configuration page. Because I was installing Cloudflared on a Debian system the commands I needed where:

```shell
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && 
sudo dpkg -i cloudflared.deb && 
sudo cloudflared service install MY_TOKEN
```

The connector showed up on the Cloudflare tunnels page, so I could move on to adding a public hostname for my Nextcloud service. I gave it a subdomain and pointed it to port 11000 and the static private IP address of my Docker host VM. The last thing left to do was to allow outgoing TCP connections to this IP address on port 11000 in the firewall rules for my Cloudflared container in Proxmox.

## Nextcloud

### Docker compose

To easily deploy Nextcloud, I used the [Nextcloud All-in-One Docker container](https://github.com/nextcloud/all-in-one). Following [this guide](https://github.com/nextcloud/all-in-one/blob/main/reverse-proxy.md) about installing Nextcloud with a reverse proxy and using [this template](https://github.com/nextcloud/all-in-one/blob/main/compose.yaml), I came up with the following Docker compose file.

```yaml
services:
  nextcloud-aio-mastercontainer:
    image: nextcloud/all-in-one:latest
    init: true
    restart: always
    container_name: nextcloud-aio-mastercontainer
    volumes:
      - nextcloud_aio_mastercontainer:/mnt/docker-aio-config
      - /var/run/docker.sock:/var/run/docker.sock:ro
    ports:
      - 2424:8080
    environment:
      - SKIP_DOMAIN_VALIDATION=true
      - APACHE_PORT=11000
      - APACHE_IP_BINDING=0.0.0.0
      - NEXTCLOUD_DATADIR=/home/MY_USER/nextcloud/ncdata

volumes:
  nextcloud_aio_mastercontainer:
    name: nextcloud_aio_mastercontainer
```
{: file='/home/myuser/nextcloud/docker-compose.yaml'}

I opened port 2424 for the AIO interface and 11000 for Nextcloud itself in the firewall rules in Proxmox.

Then it was just spinning up the container with:

```shell
docker compose up -d
```

### Server configuration

To configure and finish the Nextcloud install, I went to the AIO interface on port 2424. Here I got the AIO password with which I logged in. I set my timezone and unchecked the Nextcloud Talk feature since I had no use for it. Now I could fill in the domain I was going to use for my Nextcloud instance and download and start the containers.

After all the containers where installed, I got greeted with the login credentials for the admin user. I logged in as the admin user and checked if everything was working.

After changing the admin password I explored the settings a bit and created a user for me.


### Connecting to TrueNAS

I was going to add some of my TrueNAS datasets as external storage in Nextcloud. In TrueNAS, I made a new user for Nextcloud and gave it permissions to those datasets.

In Nextcloud, I first installed the **External storage support** app. Now I could go to the `External storage`{: .filepath} tab in the `Administration settings`{: .filepath} and add the datasets as SFTP storage.

This worked all flawlessly. Adding my TrueNAS datasets as external storage was really easy and gave me all the benefits of Nextcloud for the files and directories on my TrueNAS system. The major downside of this I could think of is that now the home directory for each user in Nextcloud is stored in the rather limited storage of my Docker VM. For me this isn't that big of a deal because I know I should not use the home directory in Nextcloud but the external NAS storage. This also means that all the metafiles Nextcloud creates for each user are stored on the virtual drive of my Docker VM and not in the NAS. I think that's a good thing because I also connect directly to the NAS when I'm home and now I don't have to deal with all those files. Proxmox makes automatic backups of these virtual drives, so I do not have to worry about losing all those metafiles.


## Conclusion

The Cloudflare tunnel works really well. It's not the fastest connection and due to limitations of Cloudflare's free plan I cannot use it to upload files bigger than 100 MB but I can live with that. I'll mostly use it to share pictures with friends and family or to work together on some documents and I think that for such a simple installation as this, it is good enough for those use cases.
