FROM mafciejewiczow/cat-flap-inference-weights:latest AS weights

FROM mafciejewiczow/cat-flap-inference-base-app:master

COPY --from=weights /source/weights_ncnn_model /source/weights_ncnn_model
