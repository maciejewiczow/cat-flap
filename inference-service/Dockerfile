FROM mafciejewiczow/cat-flap-inference-weights:latest AS weights

COPY --from=weights /app/weights_ncnn_model /app/weights_ncnn_model

FROM inference-base-app
