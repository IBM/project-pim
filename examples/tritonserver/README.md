# Triton

Triton inference server can be used to serve machine learning or deep learning models like classification, regression etc on CPU/GPU platforms.
Steps to build Triton inference server on top of base image are [here](../../base-image/)

### Config
Since triton server can be used to serve many ML inferencing applications like fraud detection, iris classification and many more, provided below configurations to tune the triton server as per the AI use case. 

This can be fed into the application via `config-json` explained [here](../../docs/configuration-guide.md#ai)

#### modelSource
A URL that specifies the source for the model corresponding to an AI usecase like fraud detection.

#### configSource
A URL that specifies the source for the config file corresponding to an AI usecase like fraud detection.

**Sample config:**
```ini
config-json = """
  {
        "modelSource": "http://<Domain>/fraud_detection/model.onnx",
        "configSource": "http://<Domain>/fraud_detection/config.pbtxt"
  }
  """
```


### Validate AI application functionality
To verify AI example application served from Triton server, perform below speicifed configurations in [config.ini](../../config.ini).  
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

### Build
**Step 1: Build Base image**
Follow the steps provided [here](../../base-image/README.md) to build the base image.

**Step 2: Build triton server PIM image**
Ensure to replace the `FROM` image in [Containerfile](Containerfile) with the base image you have built before building this image.

```shell
podman build -t <your_registry>/pim-triton-server

podman push <your_registry>/pim-triton-server
```
