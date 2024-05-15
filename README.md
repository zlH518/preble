# Code Structure
The `multi_node` directory contains the code for running as a separate abstraction layer to SGLang/vLLM in a distributed setting. This code is responsible for coordinating and managing the execution of the distributed system.

## Design Document
For more information about the design and architecture of the `multi_node` code, please refer to the [design document](https://docs.google.com/document/d/1sa0ewITYok7V1kb4tZ32uh6HXitcpcvjybOZpacWKuo/edit).

## Repository Installation
To install the repository, run the following command:

```
pip install -e "python[all]"
pip3 install scipy matplotlib datasets paramiko gurobipy
pip install flashinfer -i https://flashinfer.ai/whl/cu121/torch2.1
```

## Benchmarks

Currently the benchmarking results are all stored in onedrive.
- Add the log file, jupyter notebook for plotting, figure as a seperate marked folder

Run Server
```
python -m sglang.launch_server --model-path meta-llama/Llama-2-7b-chat-hf --port 30000
```
