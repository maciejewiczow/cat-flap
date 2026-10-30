FROM mafciejewiczow/cat-flap-image-capturer-base-app:master

# USER root

ENV PYTHONPATH=".venv/lib/python3.13/site-packages:/usr/lib/python3/dist-packages"

RUN apt-get -o Apt::Key::gpgvcommand=/usr/bin/gpgv update \
	&& apt-get full-upgrade -y \
	&& apt-get install -y --no-install-recommends python3-picamera2
# RUN rm -rf /usr/lib/python3/dist-packages/PIL /usr/lib/python3/dist-packages/Pillow-9.4.0.egg-info /usr/lib/python3/dist-packages/numpy*

# USER app
