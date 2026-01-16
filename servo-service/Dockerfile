FROM mafciejewiczow/cat-flap-servo-base-app:master

USER root

RUN apk update && apk add -y \
    libpigpio-dev \
    pigpio

ENV PIGPIO_ADDR=localhost
ENV PIGPIO_PORT=8888

USER app
