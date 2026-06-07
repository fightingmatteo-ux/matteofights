FROM runpod/pytorch:2.2.1-py3.11-cuda12.1.1-devel-ubuntu22.04

WORKDIR /workspace

# Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install -r requirements.txt

# Install ComfyUI custom nodes for Wan2.1
RUN cd /workspace/ComfyUI/custom_nodes && \
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    cd ComfyUI-WanVideoWrapper && \
    pip install -r requirements.txt

# Create output and workflow dirs
RUN mkdir -p /workspace/ComfyUI/output /workspace/workflows

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY handler.py .
COPY start.sh .
COPY workflows/ ./workflows/

RUN chmod +x start.sh

CMD ["/app/start.sh"]
