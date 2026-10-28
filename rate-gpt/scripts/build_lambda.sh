#!/usr/bin/env bash
# Build the Lambda artifacts for Python 3.13 on x86_64 Linux:
#   .build/layer/python   third-party dependencies (Lambda mounts this at /opt/python, already on sys.path)
#   .build/function       our code only (rate_gpt)
# Uses manylinux wheels, so it works from macOS without Docker.
set -euo pipefail
cd "$(dirname "$0")/.."

LAYER=.build/layer
FUNCTION=.build/function
rm -rf .build
mkdir -p "$LAYER/python" "$FUNCTION"

# boto3 ships with the Lambda runtime, so it stays out of the layer.
python3 -m pip install --quiet --no-compile \
  --platform manylinux2014_x86_64 --implementation cp --python-version 3.13 \
  --only-binary=:all: --target "$LAYER/python" \
  "mcp>=2.3,<3" "httpx>=0.28" "mangum>=0.19"

cp -R src/rate_gpt "$FUNCTION/"
find .build -name __pycache__ -type d -prune -exec rm -rf {} +
echo "Built $LAYER ($(du -sh "$LAYER" | cut -f1)) and $FUNCTION ($(du -sh "$FUNCTION" | cut -f1))"
