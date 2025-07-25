# Custom Examples

Examples that utilises PIM base image built [here](https://github.ibm.com/project-pim/base-images) to showcase various use cases that can be built on PIM 

### Structure
All the custom examples contains following files

**Containerfile**

```Dockerfile
FROM <REGISTRY>/pim/base
```
Base Image built from [here](https://github.ibm.com/project-pim/base-images) 
```Dockerfile
COPY vllm.container /usr/share/containers/systemd
```
Container systemd configuration to start the desired AI application when you bring up PIM stack using the image built

**\<app\>.container systemd**

This is similar to regular systemd.service configuration with block dedicated to configure container related inputs
Read more [here](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html) to understand the mapping and various configuration parameters available

### Stpes to create a new application

To create a new application, run the generator script. This will set up the application structure and guide you through the next steps.

***Example***
```shell
python3.9 generator.py --app <app-name> --image <image-name>
```
***Parameters***

- `--app` - Name of the application
- `--image` - Base bootc image to be used for the application
|