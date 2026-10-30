FROM ultralytics/ultralytics:8.4.3-python-export
ARG WEIGHTS_PATH
ARG IMG_SIZE=352

WORKDIR /app

COPY $WEIGHTS_PATH weights.pt

RUN yolo export model=weights.pt format=ncnn simplify=True batch=1 imgsz=$IMG_SIZE

RUN rm weights.pt
