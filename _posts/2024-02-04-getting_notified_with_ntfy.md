---
title: Getting notified with Ntfy
date: 2024-02-04 18:00:00 +0200
categories: [notifications]
tags: [homeserver, docker, container, ntfy, notifications, cloudflare, tunnel, ios] # TAG names should always be lowercase
---

I was searching for a way to get more rich notifications from services running on my homeserver and stumbled upon [Ntfy](https://ntfy.sh/) which offered everything I was searching for. In this post I explain how I set up Ntfy in a Docker container and made it publicly accessible with my Cloudflare tunnel I set up earlier (see [Setting up Cloudflare tunnel](/posts/setting_up_nextcloud_and_cloudflare_tunnels)).

> NetworkChuck made [an excellent video](https://www.youtube.com/watch?v=poDIT2ruQ9M) about Ntfy which made getting started with Ntfy a lot easier.
{: .prompt-info}

## Requirements

I had some requirements I wanted for my notification system:

- Easily send notifications with simple HTTP GET and POST requests.
- Integrations for popular services like [Uptime Kuma](https://github.com/louislam/uptime-kuma).
- IOS app to receive instant notifications.

There are a lot of selfhosted notification services out there but Ntfy looked really solid for me and it fulfills all my requirements. 


## Installing Ntfy

Installing Ntfy was very easy with the Docker container they provide and they have excellent [documentation](https://docs.ntfy.sh/install/#docker). Since I had already a [Docker system with Portainer](/posts/installing_docker), I used Portainer to launch the container. But before I could start the container, I needed a configuration file. 


### The configuration file

The developers created a [template](https://github.com/binwiederhier/ntfy/blob/main/server/server.yml) which I copied to my system. Since I wanted to receive instant notifications on my iPhone, I needed to change the base url and upstream base url. I also added a path for the user database so I would be able to configure access control for my topics. The default access is set to `write-only` so that I do not need to fiddle with access tokens whenever I want a service to send notifications through Ntfy.

```yml
base-url: https://ntfy.my-website.be
upstream-base-url: "https://ntfy.sh"

auth-file: "/var/lib/ntfy/user.db"
auth-default-access: "write-only"

behind-proxy: true
```
{: file='/home/myuser/ntfy/etc/server.yml'}


### Starting the container

The next step was to create and start the container in Portainer with the following settings:

- Name: `ntfy`
- Image: `binwiederhier/ntfy:latest`
- Ports: `8080:80`
- Command: `serve --cache-file /var/cache/ntfy/cache.db`
- Restart: `unless-stopped`
- Volumes:
    - `/home/myuser/ntfy/etc:/etc/ntfy`
    - `/home/myuser/ntfy/cache:/var/cache/ntfy`
    - `/home/myuser/ntfy/lib:/var/lib/ntfy`

Off course change the published port, name and mount locations to whatever you want. The cache database is so that undelivered notifications will not be lost on a restart.

The only thing left to do was to start the container and create an entry for it in the Cloudflare dashboard.


### Creating an admin user

After starting the container and confirming the services was reachable, I entered the `bin/sh` console of the container from Portainer. Here I made an admin user with the following command. This user automatically has full read/write access to all topics.

```sh
ntfy user add --role=admin username
```

> If I needed more advanced access control for a specific topic, I can use the following commands. These are all described in more detail in the [documentation](https://docs.ntfy.sh/config/#access-control).
```sh
ntfy user add USERNAME                  # Add regular user
ntfy user change-pass USERNAME          # Change password for USERNAME
ntfy access                             # Show access control list
ntfy access USERNAME                    # Show access control list for USERNAME
ntfy access USERNAME TOPIC PERMISSION   # Set access for USERNAME to TOPIC
```
{: .prompt-info}


## Using Ntfy

The next sections are about how I use Ntfy in my homeserver. Ntfy put some handy [examples](https://docs.ntfy.sh/examples/) in their documentation which make it very easy to get started.


### Mobile app

The first thing to do is to install the [mobile app](https://docs.ntfy.sh/subscribe/phone/), connect it to my instance of Ntfy and login as my admin user to be able to receive notifications. I need to add each topic I want to receive notifications from first in the mobile app before I get notifications.


### Curl

To test everything, I experimented a bit with sending messages from the command line with `curl`. In these examples I send messages to the topic `test`.

Sending just a text message is as easy as:
```bash
curl -d "hey, this is a notification" https://ntfy.my-website.be/test
```

Sending a different notification when a command succeeds or fails:
```bash
ping 192.168.0.1 -c 3 && curl -d "It's up" https://ntfy.my-website.be/test || curl -d "It's down" https://ntfy.my-website.be/test
```

Sending a notification over 10 seconds:
```bash
curl -H "In: 10sec" -d "hey, this is a notification" https://ntfy.my-website.be/test
```


### SSH login alerts

The Ntfy notification lists a lot of examples and one I really like is a configuration to receive a notification every time someone logins to one of your servers via ssh. This requires some preparation on the server you want to receive notifications from.

The first step is to create a file:
```sh
#!/bin/bash
if [ "${PAM_TYPE}" = "open_session" ]; then
  curl \
    -H "tags:warning" \
    -d "SSH login: ${PAM_USER} from ${PAM_RHOST}" \
    https://ntfy.my-website.be/sshlogins
fi
```
{: file='/usr/bin/ntfy-ssh-login.sh'}

Then we need to make this file executable:
```bash
sudo chmod +x /usr/bin/ntfy-ssh-login.sh
```

The last step is to add a line in the PAM configuration file:
```sh
# at the end of the file
session optional pam_exec.so /usr/bin/ntfy-ssh-login.sh
```
{: file='/etc/pam.d/sshd'}


> I'll expand this post with some more use cases and configurations in the future.
{: .prompt-info }
