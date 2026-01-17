FROM mafciejewiczow/cat-flap-image-capturer-base-app:master

USER root

RUN apt update -y && apt upgrade -y && apt install git vim -y

RUN apt install libcamera-tools libcamera-apps-lite -y
RUN apt install libcap-dev libcamera-dev -y
RUN apt install libatlas-base-dev libopenjp2-7 libkms++-dev libfmt-dev libdrm-dev -y
RUN pip install rpi-libcamera -C setup-args="-Dversion=unknown"
RUN pip install rpi-kms

RUN apt install -y python3-picamera2 --no-install-recommends
RUN pip install picamera2

USER app
