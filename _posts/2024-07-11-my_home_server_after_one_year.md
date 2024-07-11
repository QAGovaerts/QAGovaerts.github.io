---
title: My home server after one year
date: 2024-07-11 14:00:00 +0200
categories: [blog]
tags: [blog, homeserver, website, proxmox, docker] # TAG names should always be lowercase
---

My first home server is almost one year old, so I think it is a good time to look back on the past year. My home server expanded a lot this past year. This post will give a short overview of what changed and the services I experimented with.


## This blog

Due to my studies taking a lot of my time during the year, I did not have much time left for writing full blog posts on this blog. During the summer I have some more time, so I will write more detailed posts about some topics in this blog post in the following months.


## Proxmox

My Proxmox installation itself did not change that much. I added and removed some containers and virtual machines along the way since they are so easy to spin up and manage. 


### GPU pass through

I played around with GPU pass through to a VM running some Stable Diffusion models. It worked but since my GPU wasn't beefy enough, the generation of images took way too long to be a useful installation. And after a catastrophe where I basically removed every way of interacting with my home server when the server lost network connection due to a misconfiguration and not being able to connect a monitor because the GPU was on pass through, I removed this whole configuration. I made a mental note that day to always have one GPU in every server with the sole purpose of being there if something needs to be solved the old school way by connecting a monitor and keyboard directly to the server.


### Backups

Proxmox makes regularly backups both on an external hard drive and to my TrueNAS installation. It took some tinkering to find the right interval and backup retention policy to both have recent backups as an archive going a while back but also not taking too much space. Luckily I haven't needed a backup yet, but I'll continue making them, so there will always be a decently recent one available in case something happens. Something I still have to add is a remote location to back up to.


## Docker

The solid Docker installation with Portainer and Traefik makes it really easy to spin up a container to experiment with a new service and directly have a secure way of connecting to it. Here is a brief overview of most of the containers that are currently running.


### Containers

[ChangeDetection](https://github.com/dgtlmoon/changedetection.io)
: Changedetection.io is a really nice way to watch websites for changes. I mostly use it to track prices of products and software.

[Commafeed](https://github.com/Athou/commafeed/)
: Commafeed is my RSS feed reader. I mainly use it to watch the release pages of the containers that I have running to make it easy to spot if there are breaking changes I need to watch out for when updating the containers.

[Dozzle](https://dozzle.dev/)
: Dozzle makes it really easy to look at the logs of all the Docker containers that are running in a nice and clean interface.

[Gitea](https://about.gitea.com/products/gitea/)
: Gitea is a really nice self-hosted git service. I use it to manage all my private projects that I don't need to collaborate with other people on.

[Grafana](https://grafana.com/)
: Grafana is the dashboard to see all the statistics of your server. I set it up together with Loki, InfluxDB and Prometheus, but I'm still experimenting with it and learning to query the data.

[Homepage](https://gethomepage.dev/main/)
: I use homepage as my main dashboard to easily access all the services that I have running. I really like the looks of it, and it is very easy to add new services via the YAML files.

[Huginn](https://github.com/huginn/huginn)
: In Huginn you can have agents doing all kind of jobs based on certain events. I'm currently experimenting with it for enriching notifications. I've also used it to watch changes on website, but I moved that to my ChangeDetection container.

[Immich](https://immich.app/)
: I've grown to really like Immich to manage my personal photo's. Of all the services that I host this is the one that receives the most updates and new features.

[Nextcloud](https://nextcloud.com/)
: Nextcloud is the way I access the files on my NAS remotely and share them with others. I wrote a whole [blog post](/posts/setting_up_nextcloud_and_cloudflare_tunnels/) about it.

[Ntfy](https://ntfy.sh/)
: Ntfy is a really nice way to send push notifications about events on the server. Read my [blog post](/posts/getting_notified_with_ntfy/) about it for more info.

[Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx)
: Paperless-ngx is a really nice way of managing important documents. It gives a peace of mind knowing that all my important documents are securely saved and easily searchable and accessible in there.

[Pi-Hole](https://pi-hole.net/)
: Pi-Hole is one of the most used network wide ad blockers by blocking DNS requests to certain sites. I wrote a [blog post](/posts/setting-up-pi-hole/) about setting up Pi-Hole.

[Pix2tex](https://github.com/lukas-blecher/LaTeX-OCR)
: When writing a paper in LaTeX I sometimes need to paste a formula in there. This tool makes it really easy to generate the LaTeX code from a screenshot of a formula.

[Portainer](https://www.portainer.io/)
: Portainer is the way to manage all my Docker containers for me. I explain the installation in my [post about installing Docker](/posts/installing_docker/).

[Traefik](https://traefik.io/)
: Traefik is a reverse proxy to securely access all my services. I explain the installation in my [post about installing Docker](/posts/installing_docker/).

[Uptime Kuma](https://github.com/louislam/uptime-kuma)
: I really like Uptime Kuma to get notified when a service is down or a certificate expires.

[What's up Docker](https://github.com/fmartinou/whats-up-docker)
: I use WUD to notify me whenever a container has a update available. This way I can manually check for breaking changes before updating.


### Backups

I'm still searching for a good way of making backups of my Docker deployments and the files of every container. Having a backup of the files of every container separately would be nice when I accidentally damage a file of one container because then I don't need to revert a backup of the whole virtual machine. The main challenge of backing up these files I'm currently facing are the strict permissions some containers (like Portainer) set. 


## Hardware

Hardware wise not much changed in comparison to the server I started with a year ago. The main upgrade was adding a second network card specially for the TrueNAS virtual machine because Proxmox was slowing down the file transfer speeds by virtualizing the network interface. I then used PCIe pass through to directly connect this network card to the TrueNAS VM.


## Conclusion

I've mostly played around with new Docker containers this past year. Finding a lot of useful services that can be self-hosted. And I'm sure much more will add to this list in the coming years. I was really glad that I put enough time and research in the initial install so it would be a stable and solid foundation for all the tinkering to come.
