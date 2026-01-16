FROM mafciejewiczow/cat-flap-inference-weights:latest AS weights

FROM mafciejewiczow/cat-flap-inference-base-app:master

COPY --from=weights /app/weights_ncnn_model /app/weights_ncnn_model
