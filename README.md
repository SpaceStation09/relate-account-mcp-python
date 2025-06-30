# Relate Account (Python version)

本项目是 [relate-account-mcp](https://github.com/fengshanshan/relate-account-mcp/tree/main) 的python实现。

## Tools

- `get-related-address`: 给定用户的身份和平台，通过web3.bio 的 graphql 查询用户绑定的各种身份信息, 并进行基础的分析。

## Usage

### 安装依赖

``` bash
uv pip install -r requirements.txt 
```

### Run Server
  
```bash
  uv run relate-account.py
```

server此时可通过 http 被链接：`http://127.0.0.1:8000/relate-account/`，你可以在上一步中的ui中通过 streamable HTTP的方式去连接到mcp 并进行测试。


## Future Work

- [ ] Description for graphql schema
- [ ] More query schema support