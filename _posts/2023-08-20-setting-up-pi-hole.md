---
title: Setting up Pi-Hole
date: 2023-08-20 12:00:00 +0200
categories: [network]
tags: [homeserver, docker, ubuntu, container, traefik, dns, pi-hole] # TAG names should always be lowercase
---

[Pi-Hole](https://pi-hole.net/) is a wonderful local DNS service. Besides its main purpose being network wide add blocking, I use it also to inspect with which domains my VMs are connecting and to set up local DNS records. In this post I describe how I set up Pi-Hole as a Docker container and use Traefik to access the web UI of Pi-Hole.

> I'm installing the Pi-Hole container on my Docker host VM that has Traefik already installed. See my post about [installing Docker with Portainer & Traefik](/posts/installing_docker) for more info about Traefik.
{: .prompt-info}


## The port 53 problem

Pi-Hole uses the default port for a DNS server: port 53. But my host OS is Ubuntu server and modern releases of Ubuntu include `systemd-resolved` which is configured by default to implement a caching DNS stub resolver. This prevents Pi-Hole from listening on port 53. I followed [this guide](https://github.com/pi-hole/docker-pi-hole#installing-on-ubuntu-or-fedora) from the Pi-Hole GitHub page to resolve this.


## The Docker compose file

I used this [quick start template](https://github.com/pi-hole/docker-pi-hole/#quick-start) from the Pi-Hole GitHub repo as a base for my Docker compose file. 

```yml
version: "3"

services:
  pihole:
    container_name: pihole
    image: pihole/pihole:latest
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "6898:80/tcp"
    networks:
      - proxy
    environment:
      TZ: 'Europe/Brussels'
      WEBPASSWORD: 'MY-PASSWD'
      FTLCONF_LOCAL_IPV4: 'LOCAL-IP'
    # Volumes store your data between container upgrades
    volumes:
      - '/home/myuser/pihole/etc-pihole:/etc/pihole'
      - '/home/myuser/pihole/etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.pihole.entrypoints=web"
      - "traefik.http.routers.pihole.rule=Host(`pihole.local.mywebsite.be`)"
      - "traefik.http.middlewares.pihole-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.pihole.middlewares=pihole-https-redirect"
      - "traefik.http.routers.pihole-secure.entrypoints=websecure"
      - "traefik.http.routers.pihole-secure.rule=Host(`pihole.local.mywebsite.be`)"
      - "traefik.http.routers.pihole-secure.tls=true"
      - "traefik.http.routers.pihole-secure.service=pihole"
      - "traefik.http.services.pihole.loadbalancer.server.port=80"

networks:
  proxy:
    external: true
```
{: file='/home/myuser/pihole/docker-compose.yml'}

The port binds for port 53 are necessary for the DNS service. I also bound port 80 to a higher port (I selected port 6898 but it can be any unused port) to access the web interface without Traefik. For the environment variables, I changed `MY-PASSWD` with a password for the web UI and `LOCAL-IP` with the local IP address of my Docker host VM. The labels are all the labels that are needed for Traefik to route `pihole.local.mywebsite.be` to the web interface of Pi-Hole that is listening on port 80 in the container. We need to add a few labels to tell Traefik to connect to port 80 because Traefik will by default connect to the lowest open port and that is 53 in this case.

> I explained all these labels in my post about [setting up Traefik](/posts/installing_docker/#adding-containers).
{: .prompt-tip}

The last thing to do before I could start the container is adding firewall rules in Proxmox to allow connections to ports 53 and 6898.

Now I can start the container with:

```shell
docker compose up -d
```


## Setting Pi-Hole as the local DNS server

The last thing I needed to do was telling my VMs and other devices to use my new Pi-Hole container as their DNS server. To take full advantage of the Pi-Hole network wide add blocking, it is best to configure the Pi-Hole instance as the DNS server in the routers settings because then the router will set it as the DNS server for all the devices connected to its network. Unfortunately, I cannot change my DNS server in my routers settings because I use a router from my ISP. I'm definitely planning on changing this with my own router, but that is a project for another day. So the next best thing is to manually set the local IP address of my Pi-Hole service (that is the IP address of my Docker container) as the preferred DNS server on every device I want to use Pi-Hole with.


### In Proxmox

Adding a DNS server in Proxmox is as easy as going to the `System/DNS`{: .filepath} tab under the node and clicking the `Edit` button.


### In Ubuntu

In the `/etc/netplan/`{: .filepath} directory should be a YAML file containing the network configuration. Here I can add the DNS server (nameserver). The example below is from my Docker VM that has a static IP address.

```yaml
network:
  ethernets:
    ens18:
      addresses:
      - LOCAL-IP/24
      nameservers:
        addresses: [127.0.0.1]
        search: []
      routes:
      - to: default
        via: GATEWAY-IP
```
{: file='/etc/netplan/00-installer-config.yaml'}

Here I replaced `LOCAL-IP` with the IP address of my Docker VM and `GATEWAY-IP` with the IP address of my router. Since Pi-Hole is running as a service on this VM I can add the loopback IP address (`127.0.0.1`) as DNS server instead of the local IP address of the VM.


### TrueNAS

Adding DNS servers in TrueNAS can easily be done in the `Network/Global configuration`{: .filepath} tab.


### MacOS

Changing the DNS settings in MacOS can be done by going to the `Network`{: .filepath} tab in the System settings app. Here I selected the interface and pressed the `Details` button. Now I can add the DNS server in the `DNS`{: .filepath} tab in the new window that opened.


### iOS

The DNS settings in iOS can be found in the Settings app: go to Wi-Fi, tick the little info icon behind the Wi-Fi network and scroll down until you see the option `Configure DNS`.
