#!/bin/bash

AI_DEMOS_REPO="https://github.com/PDeXchange/ai-demos"
REPO_NAME="ai-demos"
REGISTRY="localhost"
CONTAINER_IMAGE="$REGISTRY/build_env"

show_help() {
cat << EOF
  Usage: $(basename "$0") [build, train] [options]

  This is a bash script to build the AI application container image and train its machine learning/deep learning model.

  Available commands:
    build      Build the container image with an AI application name as an argument .
    train      Train a model by passing the AI application container image as an argument.
    help       Display the help message.

EOF
}

build_image() {
  shift

  if [ "$#" -ne 1 ]; then
    echo "Error: 'build' command requires an argument: application_name" >&2
    echo "Usage: $0 build <app_name>" >&2
    exit 1
  fi

  local APP="$1"

  if [ ! -d "$REPO_NAME" ]; then
    echo "Cloning source code from $AI_DEMOS_REPO"
    git clone $AI_DEMOS_REPO
  fi

  cd $REPO_NAME

  echo "find the app directory"
  app_dir=$(find . -maxdepth 1 -type d -iname "*$APP*" | head -n 1)
  echo "app dir: $app_dir"
  if [ -d "$app_dir" ]; then
      cd "$app_dir" || return
  fi

  echo "Building container image: $CONTAINER_IMAGE"
  podman build . -t $CONTAINER_IMAGE
}

train_model() {
  shift

  if [ "$#" -ne 2 ]; then
    echo "Error: 'train' command requires exactly two arguments: application_name and container_image" >&2
    echo "Usage: $0 train <app_name> <container_image>" >&2
    exit 1
  fi

  local APP="$1"
  local CONTAINER_IMAGE="$2"

  echo "Executing 'train' command..."
  echo "  APPLICATION: $APP"
  echo "  CONTAINER IMAGE: $CONTAINER_IMAGE"

  if [ ! -d "$REPO_NAME" ]; then
    echo "Cloning source code from $AI_DEMOS_REPO"
    git clone $AI_DEMOS_REPO
  fi

  cd $REPO_NAME

  echo "find the app directory"
  app_dir=$(find . -maxdepth 1 -type d -iname "*$APP*" | head -n 1)
  echo "app dir: $app_dir"
  if [ -d "$app_dir" ]; then
      cd "$app_dir" || return
  fi

  echo "Train the model using $CONTAINER_IMAGE container"
  # Run the app image to generate the model file
  podman run --rm  --name $APP -v $(pwd):/app:Z -v $(pwd)/model_repository:/app/model_repository \
          --entrypoint="/bin/sh" $CONTAINER_IMAGE -c "cd /app && make train && make prepare" || { echo "Failed to train the model for $APP" >&2; exit 1; }
  echo "Model has been trained successfuly and available at path: $(pwd)/model_repository/fraud/1"

  echo "Generating model configuration file"
  make generate-config || { echo "Failed to generate model configuration for $APP" >&2; exit 1; }
  echo "Model config file is available at path: $(pwd)/model_repository/fraud"
}

# If no subcommands or args passed, display help
if [ $# -eq 0 ]; then
  show_help
  exit 1
fi

SUBCOMMAND="$1"
case "$SUBCOMMAND" in
  build)
    build_image "$@"
    ;;
  train)
    train_model "$@"
    ;;
  help)
    show_help
    ;;
  *)
    echo "Error: Unknown command '$SUBCOMMAND'" >&2
    show_help
    exit 1
    ;;
esac
