# Triton server

[Triton server](https://github.com/triton-inference-server/server) can be used to inference AI workloads using machine learning models. Some of pre-built example AI workloads like fraud detection, Iris classification etc are covered in the [ai-demos-repo](https://github.com/PDeXchange/ai-demos). Users can utilise them to try out the triton inference server.
Users can deploy AI workloads of their choice of model and configuration by supplying the trained model file(model.onnx) and configuration file (config.pbtxt) to http server to be used by Triton server when its run on a PIM partition. Currently tritonserver suppports serving only model tained for fraud-detection application covered in [ai-demos-repo](https://github.com/PDeXchange/ai-demos).

## Fraud detection usecase with ONNX runtime
### Pre-requisites
Below mentioned pre-requisites are needed to build container image for fraud detection example
- podman
- container registry to push the built fraud detection container image
- protobuf

### Build fraud detection container image
The [script](build_and_train.sh) builds the base container image for the AI example applications given in [ai-demos](https://github.com/PDeXchange/ai-demos). AI application name for which container image to be built is given as an argument to the script.
```shell
bash build_and_train.sh build fraud_detection
```

### Training model with ONNX runtime
Run the `build_env` base container image generated above to train the model and generate configuration for the model. Provide both AI application name and the container image built above as arguments to the script.
```shell
bash build_and_train.sh train fraud_detection localhost/build_env
```

After the successful execution, **model.onnx** file will be available on the path `<current_script_dir>/model_repository/fraud/1/model.onnx`. It also persisits configuration for the model **config.pbtxt on to the path `<current_script_dir>/model_repository/fraud/config.pbtxt`
