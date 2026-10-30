FROM python:3.13-trixie

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gpg wget \
    && wget -O /tmp/raspberrypi.gpg.key http://archive.raspberrypi.org/debian/raspberrypi.gpg.key \
    && gpg --dearmor /tmp/raspberrypi.gpg.key \
    && mv /tmp/raspberrypi.gpg.key.gpg /etc/apt/trusted.gpg.d/raspberrypi.gpg \
    && rm /tmp/raspberrypi.gpg.key \
    && dpkg --add-architecture armhf \
    && echo "deb http://archive.raspberrypi.org/debian/ $(sh -c '. /etc/os-release; echo $VERSION_CODENAME') main" \
    > /etc/apt/sources.list.d/raspi.list \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libdtovl0 \
    raspi-utils \
    && rm -rf /var/lib/apt/lists/*
