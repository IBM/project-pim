# Triton server

[Triton server](https://github.com/triton-inference-server/server) can be used to inference AI workloads using machine learning models. Some of pre-built example AI workloads like fraud detection, Iris classification etc are covered in the [ai-demos-repo](https://github.com/PDeXchange/ai-demos). Users can utilise them to try out the triton inference server.
Users can deploy AI workloads of their choice of model and configuration by supplying the trained model file(model.onnx) and configuration file (config.pbtxt) to http server to be used by Triton server when its run on a PIM partition.

## Fraud detection/Iris usecase with ONNX runtime
### Pre-requisites
Below mentioned pre-requisites are needed to build container image for fraud detection example
- podman
- container registry to push the built fraud detection container image
- protobuf

### Build application container image
The [script](build_and_train.sh) builds the base container image for the AI example applications given in [ai-demos](https://github.com/PDeXchange/ai-demos). 
```shell
bash build_and_train.sh build
```

### Training model with ONNX runtime
Run the `build_env` base container image built above to train the model and generate model configuration for the AI usecase. Provide both AI application name and the container image built above as arguments to the script. Below command demonstrates the training of fraud detection usecase.
```shell
bash build_and_train.sh train fraud_detection localhost/build_env
```

After the successful execution, **model.onnx** file will be available on the path `ai-demos/fraud_detection/model_repository/fraud_detection/1/model.onnx`. It also persisits configuration for the model **config.pbtxt** on to the path `ai-demos/fraud_detection/model_repository/fraud_detection/config.pbtxt`
