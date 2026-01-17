FROM mafciejewiczow/cat-flap-image-capturer-base-app:master

USER root

ENV PYTHONPATH=".venv/lib/python3.13/site-packages:/usr/lib/python3/dist-packages"

RUN python -V && sleep 20;

RUN apt update -y && apt full-upgrade -y && apt install -y python3-picamera2 --no-install-recommends
# RUN rm -rf /usr/lib/python3/dist-packages/PIL /usr/lib/python3/dist-packages/Pillow-9.4.0.egg-info /usr/lib/python3/dist-packages/numpy*

USER app
