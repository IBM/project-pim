# Custom Simple Entity Extraction

Builds a simple entity extraction application that leverages vLLM's OpenAI APIs to do extraction. It's built on top of [vllm](../vllm/)

### Build
- Make sure to use vLLM image built from [here](../vllm) as your base image(FROM) in [Containerfile](Containerfile).
- Replace image built from [app](app) here in `entity.container`'s `image` field in `Container` section. Since its an sample application image is hardcoded in `.container` file, if you want to configure this, you can create config systemd service to read from PIM's [ai.config-json](../../docs/configuration-guide.md#ai) similar to how vLLM reads config from systemd [here](../vllm/llm_config.service)

```shell
podman build . -t <your registry>/pim:entity-extraction

podman push <your registry>/pim:entity-extraction
```