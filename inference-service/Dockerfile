FROM mafciejewiczow/cat-flap-inference-weights:latest AS weights

FROM mafciejewiczow/cat-flap-inference-base-app:master AS app

FROM ultralytics/ultralytics:latest-python

COPY --from=weights /app/weights_ncnn_model /app/weights_ncnn_model
COPY --from=app /source /source
