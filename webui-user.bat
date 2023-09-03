@echo off
rem git pull

set PYTHON="C:\Users\korvin\miniconda3\python.exe"
set GIT=
set VENV_DIR=
set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.9,max_split_size_mb:512
set COMMANDLINE_ARGS=--opt-sdp-attention --no-half-vae --autolaunch --opt-sdp-no-mem-attention --enable-insecure-extension-access --disable-nan-check --deepdanbooru --api --gradio-img2img-tool color-sketch --disable-safe-unpickle --listen --theme dark
echo "conda1"
call conda activate automatic
echo "conda2"
call conda install pip
echo "starting"
call webui.bat
conda deactivate
