# vLLM

Builds vLLM inference server on top of base image built [here](../../base-image/)

### Config
Since vLLM AI image can be used as a base for many LLM inferencing applications like chatbot, entity extraction and many more, provided below configuration to tune the vLLM engine as per the AI use case. 

This can be fed into the application via `config-json` explained [here](../../docs/configuration-guide.md#ai)

#### llmImage
vLLM container image built using app section [here](app/README.md). This is given as a configurable option so that in future if there is a newer version of vLLM image available, we can just update the stack via [update-config](../../docs/deployer-guide.md#update-config)
#### llmArgs
Arguments you want to pass it to your vLLM inference engine
#### llmEnv
Environment variables that you want to set while running vLLM inference engine
#### modelSource
A JSON object that specifies the source URL for downloading the LLM model from a self-hosted HTTP server. Use this parameter to setup a offline model download location within the local network. This is suitable for environment which restricts outside connection. If this parameter is not provided, the model will be downloaded from hugging face over the internet. Follow the steps [here](#steps-to-set-up-a-server-to-host-an-llm-model-locally) to bring up slef-hosted HTTP server.

**Sample config:**
```ini
config-json = """
  {
        "llmImage": "na.artifactory.swg-devops.com/sys-pcloud-docker-local/devops/pim/apps/vllm",
        "llmArgs": "--model ibm-granite/granite-3.2-8b-instruct --max-model-len=26208 --enable-auto-tool-choice --tool-call-parser granite",
        "llmEnv": "OMP_NUM_THREADS=16",
        "modelSource": { "url": "http://<Domain>/models--ibm-granite--granite-3.2-8b-instruct.tar.gz" }
  }
  """
```

### Build
**Step 1: Build Base image**
Follow the steps provided [here](../../base-image/README.md) to build the base image.

**Step 2: Build vLLM image**
Ensure to replace the `FROM` image in [Containerfile](Containerfile) with the base image you have built before building this image.

```shell
podman build -t <your_registry>/vllm

podman push <your_registry>/vllm
```


### Steps to Set Up a Server to Host an LLM Model Locally
**Step 1: Download the model using Hugging Face CLI**
```shell
pip install huggingface_hub

huggingface-cli download  <model-id>

Example: 
huggingface-cli download ibm-granite/granite-3.2-8b-instruct
```
**Step 2: Create a tarball of the downloaded model folder**
```shell
tar -cvzf models--<model-id>.tar.gz <path-to-downloaded-model-directory>

Example:
tar -cvzf models--ibm-granite--granite-3.2-8b-instruct.tar.gz /var/huggingface/models--ibm-granite--granite-3.2-8b-instruct
```
**Step 3: Start an HTTP service on the server VM**
```shell
sudo yum install httpd
sudo systemctl start httpd
```
**Step 4: Copy the tar file to the web server directory**
```shell
cp <tarball-file-path> /var/www/html

Example
cp models--ibm-granite--granite-3.2-8b-instruct.tar.gz /var/www/html
```
**Step 5: Form the URL to access the model tarball**
```shell
http://<ip>/models--ibm-granite--granite-3.2-8b-instruct.tar.gz
```
Use the above URL in modelSource.url parameter to download model from the local server.

