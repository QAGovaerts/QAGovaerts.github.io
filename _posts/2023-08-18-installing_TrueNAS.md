---
title: Installing TrueNAS
date: 2023-08-18 10:00:00 +0200
categories: [truenas]
tags: [homeserver, proxmox, vm, truenas, nas, ssd, hdd] # TAG names should always be lowercase
---

One of the major purposes of my home server will be serving a NAS. For this I put 4 HDDs of 4 TB in my server and in this post I'll describe how I installed TrueNAS Core as a VM on Proxmox.


## Creating the VM

I downloaded the [TrueNAS Core ISO](https://www.truenas.com/download-truenas-core/) in Proxmox from their website. For the VM I selected a 32 GB virtual disk to install the OS on, 2 CPU cores and 8 GB of memory. Since I have 32 GB memory in my server I later increased this to 12 GB to give TrueNAS a little bit more space for its ZFS Cache. Now the easy part was done and I needed to start on the hard part of passing through the hard drives.


## Passing through the hard drives

### The configuration

Like I mentioned earlier I have four 4 TB HDDS that I want to use in a RAIDZ1 pool, so I have one parity drive. This means that one drive can fail without any data loss and I'll have a total capacity of 12 TB. I also have a 500 GB SSD that I want to use as cache drive since I do not have so much memory to give to TrueNAS.

I watched [this video](https://www.youtube.com/watch?v=M3pKprTdNqQ) from Christian Lempa and [this video](https://www.youtube.com/watch?v=MkK-9_-2oko) from TechHut, and decided to first try to pass through each drive individually. This worked from the first time without any errors. Because it is better to pass through the SATA controller that is controlling the HDDs, I later changed my installation to work with pass-through of this SATA controller as a PCI device.

> I you are following this post as a guide I highly recommend you to try to pass through the SATA controller instead of each drive individually first. [Jump directly to the SATA controller pass-through section.](#sata-controller-pass-through)
{: .prompt-tip }


### Individual drive pass-through

First I needed to discover the serial numbers of the drives because Proxmox does not pass these through by default, but TrueNAS needs those to identify the drives. This is because the name and mounting location of a drive can change on reboot, but the serial number always stays the same. To list all the connected drives and their serial number I logged in over SSH to my Proxmox node and ran this command:

```shell
lsblk -o +MODEL,SERIAL
```

Here I found my four HDDs with the names `sda`, `sdb`, `sdc`, `sdd` and the SSD with the name `nvme1n1` and their serial numbers. I wrote down those serial numbers for later.

Next I listed the drives with the command:

```shell
ls /dev/disk/by-id
```

Here I found the HDDs starting with `ata` and the SSD starting with `nvme`. Now I can add the hard drives to the VM.

```shell
sudo qm set 100 -scsi1 /dev/disk/by-id/DRIVE-ID
```

Where I replaced `DRIVE-ID` with the ID listed with the previous command and with `100` the ID of the TrueNAS VM in Proxmox. For the next drives I ran the same command with increasing the integer after `-scsi` for each drive.

The only thing that was left to do before I could start the VM is linking the serial numbers. I first made a backup of the config file.

```shell
sudo cp /etc/pve/qemu-server/100.conf 100-backup.conf
```

Then I opened the config file with nano:

```shell
sudo nano /etc/pve/qemu-server/100.conf
```

I searched for the lines starting with `scsi1`, `scsi2`, `scsi3`, `scsi4`, `scsi5` and appended `serial=SERIAL` after each line (replacing `SERIAL` with the actual serial number for each drive). Now everything was ready to start the VM.


## First boot

The TrueNAS installer makes the installation really straight forward. I just had to make sure to select the 32 GB virtual drive to install TrueNAS on. Once TrueNAS was successfully installed I removed the installation media in Proxmox and rebooted the VM.

When TrueNAS had booted up, I logged in on the web UI and checked if the hard drives where all showing up. This was the case which means that all the drives are successfully linked with the VM.

Next I gave TrueNAS a static IP to use and checked for updates. Everything was already up-to-date, so I could start creating a pool, users and shares.


## The pool

For the pool I selected the four HDDs as Data VDevs and put them in a RAIDZ1 configuration. This gives me 12 TB of capacity and one parity drives, so I could lose one drive without losing any data. I put the SSD in the Cache VDevs and created the pool.


## Making a backup

When everything was set up and working, I wanted to make a backup of my TrueNAS VM in Proxmox. There was one important thing to do before making this backup and that is excluding the HDDs and cache SSD from the backup. This can be done in the `Hardware`{: .filepath} tab in the Proxmox web UI. When they were excluded I could make a backup without problems and without it taking more than a day to complete.


## Changing my setup

As I said earlier, I wanted to change my setup. I wanted to pass through the SATA controller instead of the individual HDDs. I had also bought a smaller SSD because I wanted to use the 500 GB one for another purpose. So I decided to switch the SSDs and change the way the HDDs are pass through.


### Switching the SSD

I completely shut down the Proxmox node and installed the new SSD in one of the empty NVMe slots on the motherboard. I decided to first install the new SSD and later remove the old one. But when I booted the system I lost internet connection. After some searching around I found that the name of my Ethernet interface had changed from `enp5s0` to `enp6s0`. So I changed this in `/etc/network/interfaces`{: .filepath} and rebooted the system. Now the internet was working again, great!

Just to be sure I downloaded the config file in TrueNAS before starting to change anything. Then I removed the cache drive from the pool and checked if everything was still working.

> Because I was doing both the SSD swap and the pass-through change at the same time, I now did the SATA pass-through before coming back to the SSD.
{: .prompt-info}

After shutting down the TrueNAS VM I removed the SSD from the connected hardware in the Proxmox UI.

I repeated the process I used to connect the current SSD to connect the new SSD to the TrueNAS VM. When the SSD was correctly configured in the config file, I excluded the SSD from backups in the Proxmox UI and started the VM again.

The last thing was to add the new SSD as cache drive to the pool in TrueNAS and the SSD swap was finished.

### SATA controller pass-through

> This whole process requires a lot of rebooting which was a lot nicer to do after I disabled all my VMs to automatic start on boot.
{: .prompt-tip}

The SATA controller pass-through is a little bit more difficult. With the TrueNAS VM running, I logged in to the TrueNAS web UI. First I disabled all sharing services and periodic tasks I had set up. Next I exported the pool (making sure to uncheck the option to delete the data because I wanted the pool to remain intact). Now I could shut down the TrueNAS VM and remove the HDDs from the VM in the `Hardware`{: .filepath} tab in the Proxmox web UI.

> I followed the official Proxmox [documentation](https://pve.proxmox.com/wiki/PCI(e)_Passthrough) for this, which was actually not that hard to follow.
{: .prompt-tip}

Now it was time to enable hardware pass-through. I first shut down the Proxmox node and booted in the bios of my server to make sure hardware pass-through was enabled in the bios. Back in the Proxmox shell I changed the `intel_iommu` option to `on` in the `/etc/default/grub`{: .filepath} file.

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on"
```
{: file='/etc/default/grub'}

Next I needed to add the following lines to `/etc/modules/`{: .filepath}.

```
vfio
vfio_iommu_type1
vfio_pci
vfio_virqfd
```
{: file='/etc/modules'}

Now I needed to refresh my `initramfs` and reboot the server.

```shell
sudo update-initramfs -u -k all
sudo reboot
```

Rebooted and back in my SSH session, I ran the following command to check if the hardware pass-through was enabled.

```shell
sudo dmesg | grep -e DMAR -e IOMMU -e AMD-Vi
```

I found the line `DMAR: IOMMU enabled` which means the pass-through was enabled and ready.

Now I needed to find the driver the SATA controller is using. The next command lists all the connected hardware.

```shell
lspci -nnk
```

Here I found that the SATA controller is using the driver `ahci`. To be able to pass through the controller I need to disable this driver and replace it with the PCI driver. To do this I added the following line in the `/etc/modprobe.d/pve-blacklist.conf`{: .filepath} file.

```
blacklist ahci
```
{: file='/etc/modprobe.d/pve-blacklist.conf'}

Now I needed to refresh my `initramfs` and reboot the server again.

```shell
sudo update-initramfs -u -k all
sudo reboot
```

Back in the SSH session, I checked again and now the command `lspci -nnk` said that the SATA controller was not using any driver (the line `Kernel driver in use: ahci` was now missing in the output). This is great because now I could pass it to the TrueNAS VM with this simple command:

```shell
sudo qm set 100 -hostpci0 00:17.0
```

In this command is `100` the ID of the TrueNAS VM and `00:17.0` is the number right before `SATA controller` in the output from the `lspci -nnk` command. Now everything should be ready to start TrueNAS again.

Once logged in to the TrueNAS web UI, I checked the disks and they all showed up, victory! I was able to import my dataset again and enable the shares and periodic tasks I had running before.


## Conclusion

I was really victorious when I could make the SATA controller pass-through work. I'm still experimenting a lot with TrueNAS and finding my way, but so far everything has been working good for me. After having it running for a while I discovered that TrueNAS barely uses any CPU and needs around 3 GB of memory for its services. All the other memory is used for ZFS cache.