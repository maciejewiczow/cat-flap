FROM python:3.13-trixie

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gpg gpgv wget \
    && wget -O /tmp/raspberrypi.gpg.key https://archive.raspberrypi.org/debian/raspberrypi.gpg.key \
    && gpg --dearmor --output /usr/share/keyrings/raspberrypi.gpg /tmp/raspberrypi.gpg.key \
    && test "$(gpg --show-keys --with-colons /usr/share/keyrings/raspberrypi.gpg | awk -F: '$1 == "fpr" { print $10; exit }')" = "CF8A1AF502A2AA2D763BAE7E82B129927FA3303E" \
    && rm /tmp/raspberrypi.gpg.key \
    && dpkg --add-architecture armhf \
    && echo "deb [signed-by=/usr/share/keyrings/raspberrypi.gpg] https://archive.raspberrypi.org/debian/ $(sh -c '. /etc/os-release; echo $VERSION_CODENAME') main" \
    > /etc/apt/sources.list.d/raspi.list \
    && apt-get -o Apt::Key::gpgvcommand=/usr/bin/gpgv update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libdtovl0 \
    raspi-utils \
    && rm -rf /var/lib/apt/lists/*
