#!/bin/sh

# Sanity check for CUDA, paddle, torch
# Use the project's venv python for sanity check
VENV_PY="/app/.venv/bin/python"
if [ ! -x "$VENV_PY" ]; then
  echo "Warning: $VENV_PY not found, falling back to 'uv run python'"
  VENV_PY="uv run python"
fi

$VENV_PY - <<'PY' || true
try:
    import torch
    import torchvision
    print("torch:", torch.__version__, "torch with cuda?", torch.cuda.is_available(), "build:", getattr(torch.version, "cuda", None))
    print("torchvision:", torchvision.__version__)
except Exception as e:
    print("Torch/TorchVision check failed:", e)
try:
    import paddle
    print("paddle built with cuda:", getattr(paddle.device, "is_compiled_with_cuda", lambda: None)())
except Exception as e:
    print("Paddle check failed:", e)
PY

exec uv run gunicorn \
  --bind "0.0.0.0:6201" \
  --timeout 600 \
  --chdir ./src/flask \
  backend:app
