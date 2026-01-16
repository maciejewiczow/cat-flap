FROM mafciejewiczow/cat-flap-inference-weights:latest AS weights

FROM inference-base-app

COPY --from=weights /app/weights_ncnn_model /app/weights_ncnn_model
