#!/bin/bash
# Start ComfyUI in background, then start RunPod handler
cd /workspace/ComfyUI
python main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch &

# Wait for ComfyUI to be ready
echo "Waiting for ComfyUI to start..."
until curl -s http://127.0.0.1:8188/system_stats > /dev/null; do
  sleep 2
done
echo "ComfyUI ready."

# Copy workflow files
cp /app/workflows/*.json /workspace/workflows/

# Start RunPod handler
cd /app
python handler.py
