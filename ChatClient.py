from typing import List, Dict, Optional, Iterator
import json
import os
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class ModelConfig:
    name: str
    id: int
    server: str
    url: str
    api_key: str


class ChatClient:
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化ChatClient
        Args:
            config_path: 配置文件路径，如果为None则从环境变量读取
        """
        self.config: Dict[int, ModelConfig] = {}
        self.conversation_history: List[Dict] = []
        self.selected_model: Optional[ModelConfig] = None
        self.client = None

        if config_path:
            self._load_config_from_file(config_path)
        else:
            self._load_config_from_env()

        # 默认使用第一个配置的模型
        if self.config:
            self.set_model_by_id(1)

    def _load_config_from_file(self, config_path: str) -> None:
        """从文件加载配置"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"错误：配置文件 {self.config_path} 未找到")
            exit(1)
        except json.JSONDecodeError:
            print("错误：配置文件格式不正确")
            exit(1)

        server_configs = config.get("servers", {})
        if not server_configs:
            print("错误：配置文件中未定义任何服务端")
            exit(1)

        # server_name 暂未使用
        for server_name, server_data in server_configs.items():
            self._load_models_from_api(
                server_data.get("api_key", ""), server_data.get("api_url", "")
            )

    def _load_config_from_env(self) -> None:
        """从环境变量加载配置"""
        api_key = os.getenv("API_KEY")
        base_url = os.getenv("BASE_URL")
        if not api_key or not base_url:
            print("错误：环境变量中未设置 API_KEY 或 BASE_URL")
            exit(1)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self._load_models_from_api(api_key, base_url)

    def _load_models_from_api(self, api_key, base_url) -> List:
        """
        从单个API加载可用模型列表到配置中
        当从配置文件读取时，可能有多个模型配置，这个函数用于从单个API获取模型列表
        Returns:
            模型列表
        """
        client = OpenAI(api_key=api_key, base_url=base_url)
        for model in client.models.list():
            model_config = ModelConfig(
                name=model.id,
                id=len(self.config) + 1,
                server=model.owned_by,
                url=base_url,
                api_key=api_key,
            )
            self.config[model_config.id] = model_config

    def get_available_models(self) -> List[Dict[str, str]]:
        """获取所有可用的模型列表"""
        return [
            {"name": model.name, "id": model.id, "server": model.server}
            for model in self.config.values()
        ]

    def set_model_by_id(self, model_identifier: int) -> None:
        """
        设置要使用的模型
        Args:
            model_identifier: 模型的ID或名称
        """
        for model in self.config.values():
            if model_identifier in (model.id, model.name):
                self.selected_model = model
                # 初始化对应的client
                self.client = OpenAI(api_key=model.api_key, base_url=model.url)
                return
        raise ValueError(f"Model {model_identifier} not found in config")

    def get_selected_model(self) -> Optional[ModelConfig]:
        """获取当前选择的模型配置"""
        return self.selected_model

    def chat(self, message: str) -> str:
        """
        发送消息给LLM并获取非流式的回复
        没有单独针对推理模型的输出，主要考虑到推理细节其实大部分时候不需要暴露给用户
        Args:
            message: 用户输入的消息
        Returns:
            LLM的回复
        """
        if not self.selected_model:
            raise ValueError("No model selected")

        # 实现实际的对话逻辑
        self.conversation_history.append({"role": "user", "content": message})
        try:
            response = self.client.chat.completions.create(
                model=self.selected_model.name,
                messages=self.conversation_history,
                stream=False,
            )
            reply_content = response.choices[0].message.content
            self.conversation_history.append(
                {"role": "assistant", "content": reply_content}
            )
            return reply_content
        except Exception as e:
            print(f"API 请求失败：{str(e)}")
            return

    def stream_chat(self, message: str) -> Iterator[str]:
        """
        发送消息给LLM并获取流式迭代器
        Args:
            message: 用户输入的消息
        Returns:
            一个可迭代的流式回复生成器，每次迭代生成一个字符串
        """
        if not self.selected_model:
            raise ValueError("No model selected")

        self.conversation_history.append({"role": "user", "content": message})

        try:
            response_stream = self.client.chat.completions.create(
                model=self.selected_model.name,
                messages=self.conversation_history,
                stream=True,
            )
            for response_chunk in response_stream:
                yield response_chunk.choices[0].delta.content
        except Exception as e:
            print(f"API 请求失败：{str(e)}")
            return

    def json_chat(self, message: str) -> Dict:
        """
        发送消息给LLM并获取JSON格式的回复
        使用需要设置 system prompt ，并给出希望模型输出的 JSON 格式的样例
        Args:
            message: 用户输入的消息
        Returns:
            LLM的回复，解析为JSON对象
        """
        if not self.selected_model:
            raise ValueError("No model selected")
        self.conversation_history.append({"role": "user", "content": message})
        try:
            response = self.client.chat.completions.create(
                model=self.selected_model.name,
                messages=self.conversation_history,
                stream=False,
                response_format={"type": "json_object"},
            )
            reply_content = response.choices[0].message.content
            self.conversation_history.append(
                {"role": "assistant", "content": reply_content}
            )
            return json.loads(reply_content)
        except json.JSONDecodeError:
            print("错误：模型返回的内容无法解析为JSON")
            return {}
        except Exception as e:
            print(f"API 请求失败：{str(e)}")
            return

    def chat_cleanup(self):
        """清理对话历史"""
        self.conversation_history = []

    def get_history(self) -> List[Dict]:
        """获取当前的对话历史"""
        return self.conversation_history

    def append_history(self, role: str, content: str):
        """
        向当前的对话历史添加一条消息
        TODO: 当前的对话历史被设计为只能在最后追加内容，也许可以考虑更灵活的插入位置
        Args:
            role: 消息角色，通常为"user"或"assistant"
            content: 消息内容
        """
        self.conversation_history.append({"role": role, "content": content})

    def set_system_prompt(self, content: str):
        """
        设置当前的系统提示，为对话设定背景或任务
        完全等价于 append_history("system", content)
        建议在调用之前先清理对话历史 chat_cleanup()
        args:
            content: 系统提示内容
        """
        self.conversation_history.append({"role": "system", "content": content})

    def _check_context_length(self, message: str) -> bool:
        """检查消息是否超过上下文长度限制"""
        # TODO: 实现上下文长度检查
        pass

    def _split_long_message(self, message: str) -> List[str]:
        """将过长的消息分片"""
        # TODO: 实现消息分片逻辑
        pass
