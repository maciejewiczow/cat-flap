FROM mafciejewiczow/cat-flap-servo-base-app:latest

RUN apt-get update && apt-get install -y \
    libpigpio-dev \
    pigpio

ENV PIGPIO_ADDR=localhost
ENV PIGPIO_PORT=8888
