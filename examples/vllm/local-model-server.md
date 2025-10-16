### Steps to Set Up a Server to Host an LLM Model Locally
**Step 1: Download the model using Hugging Face CLI**
```shell
pip install huggingface_hub

huggingface-cli download  <model-id>

Example: 
huggingface-cli download ibm-granite/granite-3.2-8b-instruct
```
**Step 2: Create a tarball of the downloaded model folder**
- `model-id` should follow models--<account--model> format. Since vLLM expects in this format when it loads from the cache. 
Example:
`model-id` for ibm-granite/granite-3.2-8b-instruct is `models--ibm-granite--granite-3.2-8b-instruct`
```shell
tar -cvzf <model-id>.tar.gz <path-to-downloaded-model-directory>
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
**Step 5: Generate a checksum of the tarball**
- The checksum will be used to verify the integrity of the file after it is downloaded..
```shell
sha256sum <name-of-model-tar-ball> /var/www/html/<model-id>.checksum

Example
sha256sum models--ibm-granite--granite-3.2-8b-instruct.tar.gz > /var/www/html/models--ibm-granite--granite-3.2-8b-instruct.checksum
```

**Step 6: Form the URL to access the model tarball**
```
http://<Host/ip>/models--ibm-granite--granite-3.2-8b-instruct.tar.gz
```
Use the above URL in modelSource.url parameter to download model from the local server.
