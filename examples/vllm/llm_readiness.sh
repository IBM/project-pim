#!/bin/bash

URL="http://localhost:8000/v1/models"
TIMEOUT=1800
INTERVAL=3
elapsed=0

echo "Waiting for vLLM service to become ready..."

while ! curl -sf "$URL" >/dev/null; do
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
    if [ $elapsed -ge $TIMEOUT ]; then
        echo "vLLM not ready after ${TIMEOUT}s"
        exit 1
    fi
    echo "vLLM not ready yet, retrying..."
done

echo "vLLM service is ready."
exit 0