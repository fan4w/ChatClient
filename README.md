# ChatClient

对 OpenAI SDK 的简单封装，可以调用 LLM API 进行简单的对话,
主要面向脚本开发等场景

考虑到大部分自动化处理文件的场景不需要获取思维链，
目前暂不支持输出推理模型的思维链

只需要初始化 `ChatClient`，就可以直接调用 API 获取回复

## ChatClient 初始化

API 的 `base_url` 和 `api_key` 支持两种方式读取：配置文件或环境变量。
从配置文件读取时，可以配置多个 `base_url` 和 `api_key`

```python
# 从环境变量中读取 API_KEY 和 BASE_URL
client = ChatClient()
# 或从配置文件中读取
client = ChatClient(config_path="config.json")
```

配置文件的格式如下：

```json
{
  "servers": {
    "<name>": {
      "api_key": "<your-api-key>",
      "api_url": "<your-api-url>"
    }
  }
}
```

## 模型选择

`ChatClient` 会根据输入的 `base_url` 和 `api_key` 获取可用的模型列表，
**默认**使用获取到的模型列表中的第一个

支持通过 `id` , `name`来配置使用的模型，对于有多个模型提供商的情况，
可以指定模型提供商和模型，来选择要使用的模型。

`ChatClient` 提供了接口来获取当前可用的模型，模型信息包括：

- name，模型名称，此字段对应获取到的 `model.id`
- id，模型ID，根据获取到的顺序，`ChatClient`自动分配，从 1 开始
- server，模型服务商，此字段对应获取到的 `model.owned_by`
- url，模型URL，初始化时获取
- api_key，模型api_key，初始化时获取

使用示例

```python
# 获取当前可用的模型列表
models = client.get_available_models()
# 遍历可用模型列表
for model in models:
    print(f"- {model['name']} (ID: {model['id']}, server by: {model['server']})")
# 根据名字选择使用的模型
client.set_model_by_name("deepseek-chat")
# 获取当前使用的模型信息
selected_model = client.get_selected_model()
# 输出获取到的模型信息
print(f"Selected model: {selected_model.name} (ID: {selected_model.id}, server by: {selected_model.server})")
```

还可以使用以下接口选择使用的模型：

```python
# 通过模型列表中的 ID 选择
client.set_model_by_id(1)
# 支持泛型，可以根据 ID 或者模型名称选择
client.set_model(1)
# 或
client.set_model("deepseek-chat")
# 也可以指定模型提供商
client.set_model_by_name_and_server("deepseek-chat", "deepseek")
```

## 与 LLM 进行对话

通常情况下，至此就可以向 LLM API 发送数据了。对话支持非流式输出和流式输出。
目前不支持返回推理模型的思维链内容。

```python
# 设置用户输入
user_input = "Hello, how are you?"
# 调用 API 进行对话，返回值是一个字符串
response = client.chat(user_input)
print(f"\nUser: {user_input}")

# 或，使用流式输出，返回一个字符串迭代器
stream_response = client.stream_chat(user_input)
print("\nStreaming response:")
for chunk in stream_response:
    if chunk:
        print(chunk, end="", flush=True)
```

与常见的 API 默认行为不同，`ChatClient` 提供**有状态**的服务，即会自动存储对话历史，用于多轮对话。
当需要清空上下文状态时，可以调用 `chat_cleanup` 清空对话历史。
*未来*计划支持更灵活的对话历史修改。

## system prompt

目前 `ChatClient` 支持追加对话内。为了方便使用，
可以直接通过 `set_system_prompt` 设置 `system_prompt`，
此时 `ChatClient` 不会直接删除对话历史，
但推荐用户在设置 `system_prompt` 之前清空历史。

## JSON OUTPUT

若模型支持 JSON OUTPUT，`ChatClient` 也提供了接口输出 JSON 格式的内容

### 注意事项

- 用户传入的 system 或 user prompt 中必须含有 json 字样，并给出希望模型输出的 JSON 格式的样例，以指导模型来输出合法 JSON。
- 输出的 JSON 是否合法，需要依赖于具体模型的能力

### 使用示例

```python
json_system_prompt = """
    The user will provide some exam text. Please parse the "question" and "answer" and output them in JSON format.

    EXAMPLE INPUT:
    Which is the highest mountain in the world? Mount Everest.

    EXAMPLE JSON OUTPUT:
    {
        "question": "Which is the highest mountain in the world?",
        "answer": "Mount Everest"
    }
"""
client.set_system_prompt(json_system_prompt)
user_input = "Which is the longest river in the world? The Nile River."

json_response = client.json_chat(user_input)
print("\nJSON response:")
print(json_response)
```
