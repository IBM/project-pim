# Email-NER

Email Named Entity Recognition is an expample to extract entities in an email. It is worked out by TIP Spyre squad. Official repository is [here](https://github.ibm.com/redstack-power/spyre). It is using LLM inferencing to extract the Named Entities in the given text. So need to use [vLLM](../vllm/) provided by PIM as base image.

### Build
Ensure to replace the `FROM` image in [Containerfile](Containerfile) with the vLLM image you have built before building this image.
```shell
podman build -t <your_registry>/email-ner
podman push <your_registry>/email-ner
```
