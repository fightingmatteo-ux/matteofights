"""RunPod serverless handler for ComfyUI generation jobs."""
import json
import os
import time
import urllib.request
import runpod

COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_DIR = "/workspace/workflows"


def load_workflow(workflow_name: str) -> dict:
    path = os.path.join(WORKFLOW_DIR, f"{workflow_name}.json")
    with open(path) as f:
        return json.load(f)


def inject_prompt(workflow: dict, prompt: str, image_path: str | None = None) -> dict:
    """Replace PLACEHOLDER values in workflow with actual prompt."""
    workflow_str = json.dumps(workflow)
    workflow_str = workflow_str.replace("PLACEHOLDER_PROMPT", prompt)
    if image_path:
        workflow_str = workflow_str.replace("PLACEHOLDER_IMAGE_PATH", image_path)
    return json.loads(workflow_str)


def queue_prompt(workflow: dict) -> str:
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["prompt_id"]


def wait_for_output(prompt_id: str, timeout: int = 300) -> list[str]:
    """Poll ComfyUI history until job completes. Returns list of output file paths."""
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as resp:
            history = json.loads(resp.read())
        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]
            files = []
            for node_outputs in outputs.values():
                for key in ("images", "gifs", "videos"):
                    if key in node_outputs:
                        for item in node_outputs[key]:
                            files.append(
                                f"/workspace/ComfyUI/output/{item['filename']}"
                            )
            return files
        time.sleep(2)
    raise TimeoutError(f"ComfyUI job {prompt_id} timed out after {timeout}s")


def handler(job: dict) -> dict:
    """
    Expected job input:
    {
        "workflow": "generate_still" | "generate_clip" | "generate_video",
        "prompt": "your prompt here",
        "image_path": "/path/to/still.jpg"  # required for generate_clip
    }
    Returns: {"output_files": ["/workspace/ComfyUI/output/filename.ext"]}
    """
    inp = job["input"]
    workflow_name = inp["workflow"]
    prompt = inp["prompt"]
    image_path = inp.get("image_path")

    workflow = load_workflow(workflow_name)
    workflow = inject_prompt(workflow, prompt, image_path)
    prompt_id = queue_prompt(workflow)
    output_files = wait_for_output(prompt_id)

    return {"output_files": output_files}


runpod.serverless.start({"handler": handler})
