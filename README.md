<div align="center">
  
English | [日本語](./docs/README_ja.md)</p>

<h1 id="title">📅 NL Calender 📅</h1>

</div>

This is a web-based tool that applies appointments described in natural language to a calendar.

Here are the main features of this tool:
- Save your events locally
- Edit or delete events with natural language queries

# How to use

## Setup of the environment
> [!NOTE]
> Highly recommend to setup the python environment in some virtual environments.

install the required library from requirements.txt & torch such as:
- requirements.txt
```
pip install -r requirements.txt
```
- torch (optional)

> [!NOTE]
> Please install a version of torch that is compatible with the CUDA version of your PC.
```
pip install torch
```

## Prepare Qwen3
This app uses [Qwen3](https://github.com/QwenLM/Qwen3).

It does not work with other LLMs due to parameter dependence,
So you should download Qwen3 model from [HuggingFace](https://huggingface.co/Qwen) to Local.

It is recommended that the model size be within the VRAM capacity of the GPU.

Or you can modify the "NLParser.py" codes to use different LLMs.

## Pass the LLM path
Then, you should write the downloaded path to setting.env file
```
MODEL_PATH = path\to\qwen3
```

## Run UI
Move to the app directory
```
cd /path/to/this/app
```
In this environment, run the following command
```
streamlit run UI.py
```
Now you're ready to use calender UI! 🔥

# License

This repository is licensed under the Apache License 2.0. See the [LICENSE](./LICENSE) file for details.

> [!IMPORTANT]
> This project uses the [Qwen3](https://huggingface.co/Qwen) developed by Alibaba Cloud, which is released under the [Qianwen License Version 2](https://github.com/QwenLM/Qwen/blob/main/LICENSE).
> Please review the official model license before using this project in production or for commercial purposes.
