# Triton

Triton inference server can be used to serve machine learning or deep learning models like classification, regression etc on CPU/GPU platforms.
Triton inference server is built on top of base image [here](../../base-image/)

## Steps to setup e2e inference flow

## Step 1: Building the images
Build container image for AI example application covered in [ai-demos](https://github.com/PDeXchange/ai-demos) using [build-steps](app/README.md)
To reuse the built container image, push the built image to container registry.
```shell
podman push <registry>/build_env
```

## Step2: Train the model
Model with ONNX runtime can be trained by running the container image built in Step 1. Follow the [training steps](app/README.md)
After the successful training completion, model(mode.onnx) and config(config.pbtxt) files will be available in path **<current_dir>/app/model_repository/fraud**

### Setting up PIM partition
Follow this [deployer section](../../README.md#deployer-steps) to setup PIM cli, configuring your AI partition and launching it.

Regarding configuration of AI application served from triton server, user need to provide generated model artifacts like model file and config file to the PIM partition as shown below in `ai.config-json` section.
```ini
  config-json = """
  {
    "modelSource": "http://<Host/IP>/fraud_detection/model.onnx",
    "configSource": "http://<Host/IP>/fraud_detection/config.pbtxt"
  }
```
Both of the model files will be available in `<current_dir>/model_repository/fraud` dir on the machine wher you have trained the model. Store these files in a simple HTTP server and pass the URI path to the PIM partition like above.

#### Steps to start http server and copy the model artifacts
```shell
# Install httpd
yum install httpd -y
systemctl enable httpd
systemctl start httpd
# Copy AI app specific artifacts like model file and model config file
mkdir -p /var/www/html/fraud_detection/
cp <current_dir>/model_repository/fraud/config.pbtxt /var/www/html/fraud_detection/
cp <current_dir>/model_repository/fraud/1/model.onnx /var/www/html/fraud_detection/
```

### Validate AI application functionality
To verify AI example application served from Triton server, Apply below speicifed configurations in [config.ini](../../config.ini).  
Sample JSON payload is provided for fraud detection usecase. Feed the appropriate JSON payload specific to AI example app to be served from triton.

```ini
  [[validation]]
    # yes, no - set yes to make the request to validate the AI app deployed as part of PIM partition
    request = "yes"
    url = "http://<PIM_LPAR_IP>:8000/v1/chat/completions"
    method = "POST" # GET, POST
    # provide headers to use in json format inside triple quotes
    headers = """
    {
      "Content-Type": "application/json"
    }
    """
    # provide payload to use in json format inside triple quotes.
    # Below JSON payload is used when fraud-detection example is served from triton server
    payload = """
    {
		"inputs": [
        {
            "name": "float_input",
            "shape": [
                1,
                7
            ],
            "datatype": "FP32",
            "data": [
                [
                    20,
                    0.5,
                    2,
                    1.0,
                    1.0,
                    1.0,
                    1.0
                ]
            ]
        }
        ],
        "outputs": [
            {
                "name": "label"
            },
            {
                "name": "probabilities"
            }
        ]
	}
    """
```

Once PIM partition is deployed with triton server serving the model of configured AI application(fraud-detection in the example above), you will get to observe the output as below
```json
{
  "model_name":"fraud",
  "model_version":"1",
  "outputs":[
  {
    "name":"label",
    "datatype":"INT64",
    "shape":[1,1],
    "data":[1]
  },
  {
    "name":"probabilities",
    "datatype":"FP32",
    "shape":[1,2],
    "data":[4.172325134277344e-7,0.9999995827674866]
  }]
}
```

### Build PIM triton server
**Step 1: Build Base image**
Follow the steps provided [here](../../base-image/README.md) to build the base image.

**Step 2: Build triton server PIM image**
Ensure to replace the `FROM` image in [Containerfile](Containerfile) with the base image you have built before building this image.

```shell
podman build -t <your_registry>/pim-triton-server

podman push <your_registry>/pim-triton-server
```
