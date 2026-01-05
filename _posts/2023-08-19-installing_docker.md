---
title: Installing Docker with Portainer & Traefik
date: 2023-08-19 16:15:00 +0200
categories: [docker]
tags: [homeserver, vm, docker, ubuntu, container, portainer, traefik, reverse-proxy, dns, cloudflare, ssl] # TAG names should always be lowercase
---

Most the services that I'll be running on my home server will be Docker containers. Therefore, I decided to make a dedicated virtual machine in Proxmox to be my Docker host machine. I'll install Portainer to manage my Docker containers and Traefik to securely connect to my containers.

> The Traefik configuration described in this post is only for internal access. None of my services are exposed to the public. I'm planning on exposing some of my services but I'll use a different setup for that.
{: .prompt-warning}


## Creating a new VM

The first step is to create a new VM and choosing the host OS. After searching around and trying some Linux distributions (like Alpine), I settled on Ubuntu server because I was already familiar with Ubuntu and I wanted something that would just work. I really like the idea behind Alpine Linux, but it was too much hassle for me to get it up and running correctly. Maybe I'll move my Docker containers to a new VM running Alpine in the future.

I gave the VM a virtual disk of 64 GB, 4 GB of memory and 2 CPU cores. After deploying some containers I discovered that my memory usage average was around 80%, so I increased the memory for the VM to 6 GB. I enabled the firewall and made rules for ping and SSH connections.

Now it was time to start the VM for the first time. I followed mostly the default settings during installation except for the IP, I disabled DHCP and set a static IP outside my routers DHCP range. What's handy on Ubuntu is that at the end of the installation procedure you can already select some packages to install. Here I selected Docker so Ubuntu would install it directly for me.

When the VM was up and running, I logged in to the VM over SSH and installed updates.

```shell
sudo apt update
sudo apt upgrade
```

Secondly I installed the QEMU Guest Agent.

```shell
sudo apt-get install qemu-guest-agent
```

When the QEMU Guest Agent was installed, I shut down the VM, enabled the QEMU Guest Agent in Proxmox in the tab `Options`{: .filepath} and started the VM again. 

The last thing I did was setting a firewall rule to block all outgoing connections to my local network. This made sure that the containers could not access any service outside the VM by default. Later I can add exceptions like allowing access to my TrueNAS sharing service.

> After checking that the Docker service was working, I made a backup in Proxmox.
{: .prompt-tip}


### Finishing the Docker installation

I checked if Docker was installed by running the `hello-world` container.

```shell
sudo docker run hello-world
```

This printed a success message in the terminal. The only thing that bothered me was that I needed `sudo` to access Docker. I followed the official Docker [documentation](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user) to change this behaviour, so I could manage Docker as non-root user.


## Portainer

### Quick start

Getting started with Portainer was really easy when following the [official documentation](https://docs.portainer.io/start/install-ce/server/docker/linux). I added a firewall rule in Proxmox to allow incoming traffic on port 9443. Now I could browse to the web UI and created an user account.


### Docker compose

Starting the Portainer container from the CLI is great to get started, but it becomes a real hassle when you have to add a lot of labels to it. Luckily there is a great solution for this: Docker compose. In my home folder, I created a directory for Portainer and a subdirectory `data`{: .filepath}.

```
mkdir portainer
cd portainer
mkdir data
```

In the `portainer`{: .filepath} directory, I created a `docker-compose.yml`{: .filepath} file containing all the relevant settings.

```yml
version: "3"

services:
  portainer:
    container_name: portainer
    image: portainer/portainer-ce:latest
    ports:
      - 9443:9443
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /home/myuser/portainer/data:/data
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.portainer.entrypoints=web"
      - "traefik.http.routers.portainer.rule=Host(`portainer.local.mywebsite.be`)"
      - "traefik.http.middlewares.portainer-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.portainer.middlewares=portainer-https-redirect"
      - "traefik.http.routers.portainer-secure.entrypoints=websecure"
      - "traefik.http.routers.portainer-secure.rule=Host(`portainer.local.mywebsite.be`)"
      - "traefik.http.routers.portainer-secure.tls=true"
      - "traefik.http.routers.portainer-secure.service=portainer"
      - "traefik.http.services.portainer.loadbalancer.server.port=9443"
      - "traefik.http.services.portainer.loadbalancer.server.scheme=https"

networks:
  proxy:
    external: true
```
{: file='/home/myuser/portainer/docker-compose.yml'}

> In this Docker compose file I already included all the needed labels for Traefik.
{: .prompt-info}


## Configuring Traefik

The objective is to have a series of DNS records (like `portainer.local.mywebsite.be`, `pihole.local.mywebsite.be`...) all pointing to the internal IP address of my Docker host container. In this container I'll have Traefik listening on ports 80 and 443 for HTTP and HTTPS request and route those request to the corresponding service/container. I have my domain managed by Cloudflare, so I can configure wildcard SSL certificates with Cloudflare so all of my internal domains have a valid SSL certificate.

Getting all of this working was a real hassle with a lot of trial-and-error. I'll not walk you through everything I did while trying to get it working. Instead, I'll walk you through all the steps I would have to do if I had to set it all up again from scratch.

> There isn't one guide or video that I followed, but there are [some videos and documentations](#resources) that were especially helpful.


### File structure

Before we can start the Traefik container we need to make the required file structure. This can be done with the `mkdir` command to make directories and the `touch` command to make files. The final structure is listed below. I made the `traefik`{: .filepath} directory in my users home folder but it can be anywhere.

```shell
traefik/
├── data
│   ├── certs
│   │   └── acme.json
│   ├── config.yml
│   └── traefik.yml
└── docker-compose.yml
```

A short description of the use case for every file I made:

`traefik/data/certs/acme.json`{: .filepath}
: Here can Traefik store the SSL certs it gets from Cloudflare.

`traefik/data/config.yml`{: .filepath}
: For manual static configuration. Here I can add routes to services outside the VM.

`traefik/data/traefik.yml`{: .filepath}
: Contains all the required configuration for Traefik.

`traefik/docker-compose.yml`{: .filepath}
: The Docker compose file to start the Traefik container.

Next we need to change the permissions of the `traefik/data/certs/acme.json`{: .filepath} file.

```shell
chmod 600 /home/myuser/traefik/data/certs/acme.json
```


### The Cloudflare API token

We need an API token for Traefik to be able to get SSL certificates from Cloudflare. So I created an API token in the Cloudflare dashboard with the following permissions:

- Zone / Zone / Read
- Zone / DNS / Edit


### Creating the Traefik network

In order for the dynamic configuration of Traefik to work, we need to make a Docker network to which both the Traefik container as well as all the containers Traefik needs to route to, have to connect. I called my Traefik network `proxy` but the name can be anything.

```shell
docker network create proxy
```


### The Traefik configuration file

Next we need to populate the `traefik/data/traefik.yml`{: .filepath} file. This file contains all the Traefik configuration. I based mine on the lovely boilerplate from Christian Lempa (see [resources](#resources)).

```yml
global:
  checkNewVersion: false
  sendAnonymousUsage: false

# -- Enable API and Dashboard
api:
  dashboard: true
  insecure: true

# -- Change EntryPoints here...
entryPoints:
  web:
    address: :80
    # -- (Optional) Redirect all HTTP to HTTPS
    # http:
    #   redirections:
    #     entryPoint:
    #       to: websecure
    #       scheme: https
  websecure:
    address: :443

# -- Configure CertificateResolver here...
certificatesResolvers:
  cloudflare:
    acme:
      email: MY-EMAIL
      storage: /etc/traefik/certs/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "1.0.0.1:53"

# -- Disable TLS Cert verification check
serversTransport:
  insecureSkipVerify: true

# -- List the providers here...
providers:
  docker:
    exposedByDefault: false
  file:
    directory: /etc/traefik
    watch: true
```
{: file='home/myuser/traefik/data/traefik.yml'}

I decided to not redirect all HTTP to HTTPS by default but instead configure that for each container individually, so I've more control over when the redirection happens and when not.

I replaced `MY-EMAIL` with the email-address with which my Cloudflare account is registered.

The `insecureSkipVerify: true` is necessary to be able to connect to services from Traefik over HTTPS that have self-signed certificates. An example of such a service is Portainer when you connect to it over the port 9443. So this label tells Traefik that it can accept self-signed certificates from the services.

As last thing we need to list the providers that provide the routing information for Traefik. The first provider is the Docker host itself. This enables me to dynamically configure new routes when adding new containers through labels on these containers (see [adding containers](#adding-containers)). I set `exposedByDefault: false` so that Traefik only configures routes for containers containing the `traefik.enable=true` label. The second provider is a static provider. Traefik will watch the contents of the `/etc/traefik`{: .filepath} directory (inside the container) and apply any routers and middlewares I configure in configuration files inside this directory. This is where I can add routes to services outside my Docker VM.


### Adding authentication

One of the nice things about Traefik is that I can easily add authentication for a service by enabling a Basic-Auth middleware. I added this config to my static configuration file to have a `my-auth` middleware that I can use anywhere when a service does not have any authentication build in.

```yml
http:
  middlewares:
    my-auth:
      basicAuth:
        users:
          - myuser:HASHED-PASSWD
        headerField: "X-WebAuth-User"
        removeHeader: true
```
{: file='/home/myuser/traefik/data/config.yml'}

I replaced `myuser` with the username I wanted to use and generated the hashed password.

```shell
htpasswd -n myuser
```


### The Docker compose file

The last thing to do before I can deploy the Traefik container is writing the Docker compose file.

```yml
version: '3'

services:
  reverse-proxy:
    image: traefik:latest
    container_name: traefik
    networks:
      - proxy
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /home/myuser/traefik/data:/etc/traefik
      - /etc/localtime:/etc/localtime:ro
    environment:
      - CF_DNS_API_TOKEN=CLOUDFLARE-API-TOKEN
      - CF_ZONE_API_TOKEN=CLOUDFLARE-API-TOKEN
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.entrypoints=web"
      - "traefik.http.routers.traefik.rule=Host(`traefik-dashboard.local.mywebsite.be`)"
      - "traefik.http.middlewares.traefik-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.middlewares.sslheader.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.routers.traefik.middlewares=traefik-https-redirect"
      - "traefik.http.routers.traefik-secure.entrypoints=websecure"
      - "traefik.http.routers.traefik-secure.rule=Host(`traefik-dashboard.local.mywebsite.be`)"
      - "traefik.http.routers.traefik-secure.tls=true"
      - "traefik.http.routers.traefik-secure.tls.certresolver=cloudflare"
      - "traefik.http.routers.traefik-secure.tls.domains[0].main=local.mywebsite.be"
      - "traefik.http.routers.traefik-secure.tls.domains[0].sans=*.local.mywebsite.be"
      - "traefik.http.routers.traefik-secure.service=api@internal"
      - "traefik.http.routers.traefik-secure.middlewares=my-auth@file"
    restart: unless-stopped

networks:
  proxy:
    external: true
```
{: file='home/myuser/traefik/docker-compose.yml'}

I connect the Traefik container to the `proxy` network I prepared earlier and I bound ports 80 and 443 for HTTP and HTTPS traffic. I also bound port 8080 to access the Traefik dashboard in case the `traefik-dashboard.local.mywebsite.be` domain I set up does not work.

The first bound volume is so that Traefik can scan for new containers and configure routes accordingly. The second is the directory with the static routes configuration files and the Traefik configuration file, and the last volume is simply to set the correct timezone in the Traefik container.

There are only two environment variables necessary, those to pass the Cloudflare API token to the Traefik container.

Lastly we come to the list of labels. Most of them are described in a [next section](#default-labels) because they are the same for each container for which I want to enable Traefik. The following three labels is where the real magic for the wildcard SSL certificates happens:

```yml
      - "traefik.http.routers.traefik-secure.tls.certresolver=cloudflare"
      - "traefik.http.routers.traefik-secure.tls.domains[0].main=local.mywebsite.be"
      - "traefik.http.routers.traefik-secure.tls.domains[0].sans=*.local.mywebsite.be"
```


### Deploying the container

Now everything is ready to deploy the container. One last thing to do is adding firewall rules in Proxmox to allow HTTP and HTTPS connections, and adding DNS records in Cloudflare for each domain I want to use pointing at the internal IP address of my Docker host VM.

Now it is just as simple as

```shell
docker compose up -d
```

to launch the Traefik container.

After launching some more containers with the correctly configured labels, I was able to see all the configured routes in the Traefik dashboard. And the SSL certificates where working wonderfully so after a lot of struggling I found the correct configurations 🥳.


### Resources

- [Is this the BEST Reverse Proxy for Docker? // Traefik Tutorial](https://www.youtube.com/watch?v=wLrmmh1eI94&t=947s) by Christian Lempa
- [Put Wildcard Certificates and SSL on EVERYTHING - Traefik Tutorial](https://www.youtube.com/watch?v=liV3c9m_OX8&t=512s) by Techno Tim
- [Official Traefik documentation](https://doc.traefik.io/traefik/)
- [Lego docs about Cloudflare API](https://go-acme.github.io/lego/dns/cloudflare/)
- [Traefik boilerplates](https://github.com/ChristianLempa/boilerplates/tree/main/library/compose/traefik) by Christian Lempa
- [Cloudflare API docs](https://developers.cloudflare.com/fundamentals/api/)
- And a lot of forum posts


## Adding containers

This post is getting long enough, so I'll write separate posts for each container and service I deploy containing the Traefik labels. To have some general overview I'm ending this post with an overview of the default labels I need to add to a container to make it work with Traefik.


### Default labels

```yml
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.MY-SERVICE.entrypoints=web"
      - "traefik.http.routers.MY-SERVICE.rule=Host(`MY-SERVICE.local.mywebsite.be`)"
      - "traefik.http.middlewares.MY-SERVICE-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.MY-SERVICE.middlewares=MY-SERVICE-https-redirect"
      - "traefik.http.routers.MY-SERVICE-secure.entrypoints=websecure"
      - "traefik.http.routers.MY-SERVICE-secure.rule=Host(`MY-SERVICE.local.mywebsite.be`)"
      - "traefik.http.routers.MY-SERVICE-secure.tls=true"
```

I can replace `MY-SERVICE` with anything I want, but I'll change it mostly to the name of the container.

`traefik.enable=true`
: Enable Traefik for this container.

`traefik.http.routers.MY-SERVICE.entrypoints=web`
: Accept HTTP requests for this service.

``traefik.http.routers.MY-SERVICE.rule=Host(`MY-SERVICE.local.mywebsite.be`)``
: Configure HTTP domain for this service.

`traefik.http.middlewares.MY-SERVICE-https-redirect.redirectscheme.scheme=https`
: Create a middleware that redirects any HTTP requests to HTTPS requests.

`traefik.http.routers.MY-SERVICE.middlewares=MY-SERVICE-https-redirect`
: Use the freshly configured redirect middleware for HTTP connections.

`traefik.http.routers.MY-SERVICE-secure.entrypoints=websecure`
: Accept HTTPS request for this service.

``traefik.http.routers.MY-SERVICE-secure.rule=Host(`MY-SERVICE.local.mywebsite.be`)``
: Configure HTTPS domain for this service.

`traefik.http.routers.MY-SERVICE-secure.tls=true`
: Use SSL certificates for the HTTPS connections.


### Optional labels

These labels are for the websecure (HTTPS) router. I can off course change them for the web (HTTP) router if needed.

`traefik.http.routers.MY-SERVICE-secure.middlewares=my-auth@file`
: Use my authentication middleware to authenticate users for this service.

`traefik.http.routers.MY-SERVICE-secure.service=MY-SERVICE`
`traefik.http.services.MY-SERVICE.loadbalancer.server.port=PORT`
: Traefik forwards by default to the first port the container is listening to. This way I can tell Traefik to which port it should forward all the requests for this service.

`traefik.http.routers.MY-SERVICE-secure.service=MY-SERVICE`
`traefik.http.services.MY-SERVICE.loadbalancer.server.scheme=https`
: By default Traefik connects to services over HTTP, this is to tell Traefik to use HTTPS instead of HTTP for this service.

`traefik.docker.network=proxy`
: Explicitly tell Traefik which Docker network to use if there are multiple Docker networks connected to the container. 


### Network

Lastly, do not forget to put the container in the `proxy` network!

```yml
services:
  container:
    ...
    networks:
      - proxy

networks:
  proxy:
    external: true
```
