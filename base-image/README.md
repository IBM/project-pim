# Base PIM Image

## Containerfile
```Dockerfile
FROM quay.io/fedora/fedora-bootc:43-ppc64le
```
Used Fedora bootc image as base image which can be converted into an bootable medium via [bootc](https://github.com/bootc-dev/bootc) or [bootc-image-builder](https://github.com/osbuild/bootc-image-builder).

There are three distros of bootc image available to use. Fedora, CentOS and RHEL
### Fedora/CentOS
- Fedora and CentOS bootc images are available in Open Source, you can consume from their quay registry.
    - [CentOS](https://quay.io/repository/centos-bootc/centos-bootc) - i.e. `quay.io/centos-bootc/centos-bootc:stream10`
    - [Fedora](https://quay.io/repository/fedora/fedora-bootc) - i.e. `quay.io/fedora/fedora-bootc:43`
### RHEL
- If you have Red Hat account and wanted to use official RHEL image, use official RHEL bootc image available in Red Hat's container catalog [here](https://catalog.redhat.com/en/software/containers/rhel10/rhel-bootc/6707d29f27f63a06f7873ee2?architecture=ppc64le&image=). 

    **Note:**
    - You need Red Hat account to get the credentials to pull the image. 
    - Need to build the image on RHEL machine where subsciption activated.



```Dockerfile
RUN dnf -y install cloud-init && \
    ln -s ../cloud-init.target /usr/lib/systemd/system/default.target.wants && \
    rm -rf /var/{cache,log} /var/lib/{dnf,rhsm}
COPY usr/ /usr/
```
Install cloud-init to configure AI image and PIM partition's network and user

```Dockerfile
COPY base_config.sh /usr/bin/
COPY base_config.service /etc/systemd/system

RUN systemctl unmask base_config.service
RUN systemctl enable base_config.service
```
systemd service to setup pimconfig like copying cloud init config and pim config files to respective directory

## Build
We have pre-built the base-image and its available to consume directly via below image
```
quay.io/powercloud/pim:base
``` 

If you wish to build your own version, you can follow below steps to build it.

**Note:** When RHEL bootc image is used to create base-image, run the build in a RHEL machine with proper subscription activated. `podman build` will use the build machine's host subscription to install pkgs in PIM image.

```shell
podman build -t localhost/pim-base .

podman tag localhost/pim-base quay.io/<account-id>/pim:base
podman push quay.io/<account-id>/pim:base
```
