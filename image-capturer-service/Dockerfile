FROM mafciejewiczow/cat-flap-image-capturer-base-app:master

USER root

RUN apt update -y && apt full-upgrade -y && apt install -y python3-picamera2 --no-install-recommends
RUN apt remove python3-pil -y

USER app
