---
title: Installing Proxmox & getting started
date: 2023-08-17 12:00:00 +0200
categories: [proxmox]
tags: [homeserver, proxmox, vm, ct, firewall] # TAG names should always be lowercase
---

After building my home server and making sure all the hardware was working correctly, it was time to install Proxmox on the system and start experimenting with virtual machines and containers.

> Because Proxmox was very new for me, I followed this wonderful YouTube playlist from the channel Learn Linux TV called [Proxmox Full Course](https://www.youtube.com/playlist?list=PLT98CRl2KxKHnlbYhtABg6cF50bYa8Ulo) that walks you through everything you need to know to get started with Proxmox.
{: .prompt-tip }

## Why Proxmox?

After seeing Proxmox being used by some other homelabbers on YouTube, I quickly decided that Proxmox was the way to go for me. Yes I've installed four HDDs for a NAS and I will be running TrueNAS for this, but I really like all the control you have with Proxmox. For me this is a discovery project and a way to quickly test new things. So with Proxmox I am able to spin up a fresh VM in a matter of seconds without the fear that everything else that is stable and running on my home server will stop working. I did look into some other hypervisors but for my use case Proxmox just made the most sense.

## The installation

The installation was really straight forward. As always with the first thing to do is to download the [Proxmox VE ISO Installer](https://www.proxmox.com/en/downloads) and flashing it to a USB thumb drive. I already had a [Ventoy](https://www.ventoy.net/en/index.html) thumb drive lying around what made this process even easier.

> [Ventoy](https://www.ventoy.net/en/index.html) is a really cool project where you install the Ventoy software on your USB thumb drive, and then you can just drag and drop multiple ISOs to the drive. When you boot from this thumb drive, you boot into a Ventoy screen listing all the ISOs that are present on the drive. From there you just have to select the ISO you want and Ventoy selects that ISO to boot from.
{: .prompt-tip }

### Target Hard disk

I selected the 1 TB SSD drive I had installed to install Proxmox on. I kept the structure on the default `ext4`. Since this is my first time using Proxmox I thought I should go for the defaults if I do not really want to use other settings.

### Networking

Because I was unable to give my home server an IP reservation through DHCP on my router, I gave Proxmox a static IP address that is outside the DHCP pool of my router. I settled on the IP address `192.168.0.75` but that was just a random choice.

### Finishing the installation

Everything was set up correctly and now I just had to wait for the installation to finish. Once it rebooted I opened a web browser on my laptop and went to `192.168.0.75:8006`. The Proxmox web UI opened and I was able to log in as root user. The installation was successful!

### Installing updates

Now the only thing I had to do before I could start spinning up virtual machines was installing updates. I went to the `Updates`{: .filepath} tab in my `homeserver`{: .filepath} node and clicked on the `Refresh`{: .filepath} button. Once Proxmox had loaded all the packages that where out-of-date I clicked the `Upgrade`{: .filepath} button to install them. When all the updates where installed, I rebooted the system.

> Note for future me: you can only install updates if you are logged in as root user.
{: .prompt-info}

## The first virtual machine

Now it was finally time to spin up my very first virtual machine. Because I was familiar with Ubuntu I choose Ubuntu Server as my OS. I copied the URL for the [Ubuntu Server LTS](https://ubuntu.com/download/server) ISO and pasted it in Proxmox so Proxmox could download it for me. Once the ISO was downloaded I clicked the `Create VM`{: .filepath} button at the top of the window. Here I filled in a hostname but left everything else on the defaults.

Now it was time to start the VM. I went through the Ubuntu installation process and chose an username and password. Once the installation was finished, I shut down the VM, removed the ISO disk from the attached hardware and I started the server again. Once it was fully booted up, I logged in over SSH and installed updates with

```bash
sudo apt-get update
sudo apt-get upgrade
```

Then I installed the QEMU guest agent with

```bash
sudo apt-get install qemu-guest-agent
```

In Proxmox I changed the `QEMU Guest Agent`{: .filepath} in the `Options`{: .filepath} tab of the VM to `Enabled` and I rebooted the VM. Now my very first VM was up and running and ready to be used.

## The first container

After starting my first VM it was time to start my first container. In the `CT Templates`{: .filepath} tab in Proxmox I downloaded the Ubuntu Focal (standard) template. Once the template was downloaded I clicked the `Create CT`{: .filepath} button at the top of the window. Here I filled in a hostname, a password and changed the IPv4 settings to use DHCP. Now it was time to spin up this container and install updates with

```bash
sudo apt-get update
sudo apt-get upgrade
```

Once all the updates where installed I rebooted the container and now I had both a container and VM to experiment with.

## User management

Because I didn't want to log in as root to the Proxmox web portal all the time, I decided to make a user account for me.

In the Proxmox web UI I added a group called _admins_ and gave this group the `Administrator`{: .filepath} role in the `Permissions`{: .filepath} tab.

Now I created a user for me in the Proxmox UI and added this user to the _admins_ group. I also created this same user in the Linux shell with the `useradd` command. Then I added this user to the sudo group in the Linux shell and created a home folder with the `mkhomedir_helper` command.

Because I had to give a password when creating this user in the Linux shell, I now could log in as this user in the Proxmox web portal and manage my VMs this way.

## Firewall

The last thing I did was experimenting with firewall rules. Before enabling the firewall I added some important rules.

### Datacenter

On the datacenter level I added the following rules.

| Type | Action | Macro | Interface | Protocol | Source         | S. Port | Destination | D. Port |
| ---- | ------ | ----- | --------- | -------- | -------------- | ------- | ----------- | ------- |
| in   | ACCEPT |       | vmbr0     | icmp     | 192.168.0.0/24 |         |             |         |
| in   | ACCEPT |       | vmbr0     | tcp      | 192.168.0.0/24 |         |             | 8006    |

The first rule allows pings so I can ping the server to check if it is online. The second rule allows access to the web portal of Proxmox.

> I add `192.168.0.0/24` as source to all my firewall rules to make sure only devices on my local network are allowed to connect to it. Normally my router's firewall should block all other connections, but this is just another level of certainty.
{: .prompt-tip}

### Homeserver node

On the homeserver node I added one rule.

| Type | Action | Macro | Interface | Protocol | Source         | S. Port | Destination | D. Port |
| ---- | ------ | ----- | --------- | -------- | -------------- | ------- | ----------- | ------- |
| in   | ACCEPT | SSH   | vmbr0     |          | 192.168.0.0/24 |         |             |         |

This rule allows me to SSH to the Proxmox shell. I could set this rule on the datacenter level instead of at the node level but since I only have one node it doesn't really matter.

### VM

On the VM I added some more rules to experiment with.

| Type | Action | Macro | Interface | Protocol | Source         | S. Port | Destination    | D. Port |
| ---- | ------ | ----- | --------- | -------- | -------------- | ------- | -------------- | ------- |
| in   | ACCEPT | Ping  | vmbr0     |          | 192.168.0.0/24 |         |                |         |
| in   | ACCEPT | SSH   | vmbr0     |          | 192.168.0.0/24 |         |                |         |
| out  | ACCEPT | Ping  | vmbr0     |          |                |         | 192.168.0.0/24 |         |
| out  | DROP   |       | vmbr0     |          |                |         | 192.168.0.0/24 |         |

The first two rules are again to allow ping and SSH connections. The last rule blocks all outgoing connections to my local network. This makes sure the VM cannot try to connect to a device on my local home network. The third rule is an exception to the last rule to allow the VM to ping devices on my local network. For the exception to work it should be higher in order than the rule it is an exception to. These last two rules where just some experimenting to see how I could minimize the network access of the VM and create exception rules on other rules I created.

## First backups

To finish my first day with Proxmox I made a manual backup of the VM and CT I created earlier. Later I installed a backup task to make daily backups of all my VMs and CTs.

## Conclusion

I've been running Proxmox for a week now and I haven't had a single regret of choosing Proxmox as my supervisor. We will see what the future brings but now I'm really happy with my setup.
