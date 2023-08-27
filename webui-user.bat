@echo off
git pull

set PYTHON=
set GIT=
set VENV_DIR=
set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.9,max_split_size_mb:512
set COMMANDLINE_ARGS=--no-half-vae --xformers --autolaunch --opt-sdp-no-mem-attention --enable-insecure-extension-access --disable-nan-check --deepdanbooru --api --gradio-img2img-tool color-sketch
conda activate automatic
conda install pip
call webui.bat
conda deactivate
