# Triton server

Triton server can be used to inference AI workloads using machine learning models. there are couple of referece AI workloads like fraud detection, Iris classification covered in the [repo](https://github.com/PDeXchange/ai-demos)
Users can deploy AI workloads of their choice of model and configuration by supplying the trained model file(model.onnx) and configuration file (config.pbtxt) to http server to be used by Triton server when its run on a PIM partition.

## Fraud detection usecase with ONNX runtime
Use [script](build_and_train.sh) to generate fraud detection container image and train the model using ONNX runtime
```
bash build_and_train.sh fraud_detection
```

After the successful execution, **model.onnx** file will be available on the path `<current_script_dir>/model_repository/fraud/1/model.onnx`
