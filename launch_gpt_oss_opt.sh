#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${HUGGING_FACE_HUB_TOKEN:-${HF_TOKEN:-}}" ]]; then
	echo "Set HUGGING_FACE_HUB_TOKEN or HF_TOKEN before launching." >&2
	exit 1
fi
export HUGGING_FACE_HUB_TOKEN="${HUGGING_FACE_HUB_TOKEN:-$HF_TOKEN}"
export HF_TOKEN="${HF_TOKEN:-$HUGGING_FACE_HUB_TOKEN}"

kernel_cache=/home/dchichkov/pixtral/cache/kernel
mkdir -p "$kernel_cache"/{triton,inductor,vllm,flashinfer}
export TRITON_CACHE_DIR="$kernel_cache/triton"
export TORCHINDUCTOR_CACHE_DIR="$kernel_cache/inductor"
export VLLM_CACHE_ROOT="$kernel_cache/vllm"
export FLASHINFER_AUTOTUNER_CACHE_DIR="$kernel_cache/flashinfer"

while true; do
	echo "Starting optimized vLLM container... $(date)"

	docker run --rm -it \
		--gpus all \
		--shm-size=16g \
		--ipc=host \
		--ulimit memlock=-1 \
		--ulimit stack=67108864 \
		-v "$kernel_cache:$kernel_cache" \
		-v /home/dchichkov/pixtral/cache/huggingface:/root/.cache/huggingface \
		-p 8001:8000 \
		--env HUGGING_FACE_HUB_TOKEN \
		--env HF_TOKEN \
		--env TRITON_CACHE_DIR \
		--env TORCHINDUCTOR_CACHE_DIR \
		--env VLLM_CACHE_ROOT \
		--env FLASHINFER_AUTOTUNER_CACHE_DIR \
		--env CUDA_DEVICE_ORDER=PCI_BUS_ID \
		--env TRANSFORMERS_OFFLINE=0 \
		--env HF_HUB_OFFLINE=0 \
		vllm/vllm-openai:v0.23.0 \
		--model /root/.cache/huggingface/hub/models--openai--gpt-oss-120b/snapshots/b5c939de8f754692c1647ca79fbf85e8c1e70f8a \
		--served-model-name gpt-oss-120b \
		--tensor-parallel-size 2 \
		--max-model-len 32768 \
		--max-num-seqs 32 \
		--max-num-batched-tokens 32768 \
		--gpu-memory-utilization 0.90 \
		--async-scheduling \
		--enable-chunked-prefill \
		--enable-prefix-caching \
		--cudagraph-capture-sizes 1 2 4 8 16 32 \
		--enable-flashinfer-autotune

	echo "Container exited. Restarting... $(date)"
	sleep 5
done
