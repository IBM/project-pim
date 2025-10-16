# Build vLLM

Run `./build.sh` in a P10 Linux machine to build https://github.com/vllm-project/vllm from scratch to use it as a inference server in PIM

### Prerequisite
- Podman
- Git

### Build
Run [./build.sh](build.sh) to build the vLLM application's container image from upstream vllm-project.
#### Usage
`./build.sh <stream>`

stream - mention from which stream you want to build your vLLM image. Options: *release*, *main*

***release*** - you can pass the release version after stream like this and vLLM will get built on the specified release version
```shell
./build.sh release 0.8.5.post1
```
***main*** - it will build the vLLM application from main branch
```shell
./build.sh main
```
### Push
Once you have built the image with the above steps, the image would be available in `localhost/vllm`, you need to tag it and push it your registry to use it in actual PIM AI partition deployment.
```shell
podman tag localhost/vllm <your registry>/pim:vllm-app
podman push <your registry>/pim:vllm-app
```
