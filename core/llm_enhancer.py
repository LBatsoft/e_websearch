"""
LLM 增强模块：用于对搜索结果进行整体摘要与打标签（可选）。

支持多种模型提供商：
- 智谱AI (ZhipuAI) - 通过 ZAI_API_KEY
- OpenAI - 通过 OPENAI_API_KEY  
- Azure OpenAI - 通过 AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
- 百度文心 - 通过 BAIDU_API_KEY, BAIDU_SECRET_KEY
- 阿里通义千问 - 通过 DASHSCOPE_API_KEY
- 自定义模型 - 通过 HTTP 接口

使用方式：
    enhancer = LLMEnhancer()
    summary, tags, per_result = await enhancer.enhance(results, query, options)

其中：
- results: List[SearchResult]
- query: str
- options: dict，包含：
    - llm_summary: bool
    - llm_tags: bool
    - llm_per_result: bool
    - llm_max_items: int
    - language: str (默认 zh)
    - model_provider: str (默认 auto，可选: zhipuai, openai, azure, baidu, qwen, custom)
    - model_name: str (模型名称，如 glm-4, gpt-4, qwen-plus 等)
"""

from __future__ import annotations

import asyncio
import json
import re
import aiohttp
from typing import List, Tuple, Dict, Any, Optional
from abc import ABC, abstractmethod
from loguru import logger

from .models import SearchResult
from config import (
    ZAI_API_KEY, 
    OPENAI_API_KEY,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    BAIDU_API_KEY,
    BAIDU_SECRET_KEY,
    DASHSCOPE_API_KEY
)

# 尝试导入各种 LLM SDK
try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

try:
    import openai
except ImportError:
    openai = None

try:
    from dashscope import Generation
except ImportError:
    Generation = None


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = False
    
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """生成文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass


class ZhipuAIProvider(BaseLLMProvider):
    """智谱AI提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.client = None
        
        if self.api_key and ZhipuAI:
            try:
                self.client = ZhipuAI(api_key=self.api_key)
                self.enabled = True
                logger.info("智谱AI提供商初始化成功")
            except Exception as e:
                logger.warning(f"智谱AI初始化失败: {e}")
        else:
            logger.info("智谱AI不可用（缺少API密钥或SDK）")
    
    def is_available(self) -> bool:
        return self.enabled and self.client is not None
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=kwargs.get("model", "glm-4"),
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.3),
                )
            )
            
            # 尝试不同的响应结构
            try:
                return response.choices[0].message.content
            except (AttributeError, IndexError):
                try:
                    return response.choices[0].message["content"]
                except (KeyError, AttributeError):
                    return None
                    
        except Exception as e:
            logger.error(f"智谱AI生成失败: {e}")
            return None


class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.client = None
        
        if self.api_key and openai:
            try:
                openai.api_key = self.api_key
                self.client = openai
                self.enabled = True
                logger.info("OpenAI提供商初始化成功")
            except Exception as e:
                logger.warning(f"OpenAI初始化失败: {e}")
        else:
            logger.info("OpenAI不可用（缺少API密钥或SDK）")
    
    def is_available(self) -> bool:
        return self.enabled and self.client is not None
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.ChatCompletion.create(
                    model=kwargs.get("model", "gpt-4"),
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.3),
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI生成失败: {e}")
            return None


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.endpoint = config.get("endpoint")
        self.client = None
        
        if self.api_key and self.endpoint and openai:
            try:
                openai.api_key = self.api_key
                openai.api_base = self.endpoint
                openai.api_type = "azure"
                openai.api_version = "2023-05-15"
                self.client = openai
                self.enabled = True
                logger.info("Azure OpenAI提供商初始化成功")
            except Exception as e:
                logger.warning(f"Azure OpenAI初始化失败: {e}")
        else:
            logger.info("Azure OpenAI不可用（缺少配置或SDK）")
    
    def is_available(self) -> bool:
        return self.enabled and self.client is not None
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.ChatCompletion.create(
                    engine=kwargs.get("model", "gpt-4"),
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.3),
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Azure OpenAI生成失败: {e}")
            return None


class BaiduProvider(BaseLLMProvider):
    """百度文心提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.secret_key = config.get("secret_key")
        self.access_token = None
        self.enabled = False
        
        if self.api_key and self.secret_key:
            self.enabled = True
            logger.info("百度文心提供商初始化成功")
        else:
            logger.info("百度文心不可用（缺少API密钥）")
    
    def is_available(self) -> bool:
        return self.enabled
    
    async def _get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        if not self.access_token:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
                    async with session.post(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.access_token = data.get("access_token")
            except Exception as e:
                logger.error(f"获取百度访问令牌失败: {e}")
        
        return self.access_token
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        if not self.is_available():
            return None
        
        access_token = await self._get_access_token()
        if not access_token:
            return None
        
        try:
            # 转换消息格式
            prompt = ""
            for msg in messages:
                if msg["role"] == "user":
                    prompt += msg["content"] + "\n"
            
            async with aiohttp.ClientSession() as session:
                url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.3)
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", "")
                    else:
                        logger.error(f"百度文心API请求失败: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"百度文心生成失败: {e}")
            return None


class QwenProvider(BaseLLMProvider):
    """阿里通义千问提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.client = None
        
        if self.api_key and Generation:
            try:
                self.client = Generation
                self.enabled = True
                logger.info("通义千问提供商初始化成功")
            except Exception as e:
                logger.warning(f"通义千问初始化失败: {e}")
        else:
            logger.info("通义千问不可用（缺少API密钥或SDK）")
    
    def is_available(self) -> bool:
        return self.enabled and self.client is not None
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            # 转换消息格式
            prompt = ""
            for msg in messages:
                if msg["role"] == "user":
                    prompt += msg["content"] + "\n"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.call(
                    model=kwargs.get("model", "qwen-plus"),
                    prompt=prompt,
                    temperature=kwargs.get("temperature", 0.3),
                )
            )
            
            return response.output.text
            
        except Exception as e:
            logger.error(f"通义千问生成失败: {e}")
            return None


class CustomProvider(BaseLLMProvider):
    """自定义HTTP接口提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("endpoint")
        self.headers = config.get("headers", {})
        self.enabled = bool(self.endpoint)
        
        if self.enabled:
            logger.info(f"自定义提供商初始化成功: {self.endpoint}")
        else:
            logger.info("自定义提供商不可用（缺少endpoint）")
    
    def is_available(self) -> bool:
        return self.enabled
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            # 转换消息格式
            prompt = ""
            for msg in messages:
                if msg["role"] == "user":
                    prompt += msg["content"] + "\n"
            
            payload = {
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.3),
                **kwargs
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint, 
                    json=payload, 
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response") or data.get("content") or data.get("text")
                    else:
                        logger.error(f"自定义API请求失败: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"自定义提供商生成失败: {e}")
            return None


class LLMEnhancer:
    """基于大模型的摘要与打标签增强器。"""

    def __init__(self):
        # 初始化所有提供商
        self.providers = {
            "zhipuai": ZhipuAIProvider({"api_key": ZAI_API_KEY}),
            "openai": OpenAIProvider({"api_key": OPENAI_API_KEY}),
            "azure": AzureOpenAIProvider({
                "api_key": AZURE_OPENAI_API_KEY,
                "endpoint": AZURE_OPENAI_ENDPOINT
            }),
            "baidu": BaiduProvider({
                "api_key": BAIDU_API_KEY,
                "secret_key": BAIDU_SECRET_KEY
            }),
            "qwen": QwenProvider({"api_key": DASHSCOPE_API_KEY}),
        }
        
        # 检查是否有可用的提供商
        self.available_providers = {
            name: provider for name, provider in self.providers.items() 
            if provider.is_available()
        }
        
        if self.available_providers:
            logger.info(f"LLM 增强器初始化成功，可用提供商: {list(self.available_providers.keys())}")
        else:
            logger.info("LLM 增强器未启用（无可用提供商）")

    def is_available(self) -> bool:
        return len(self.available_providers) > 0
    
    def _select_provider(self, provider_name: str = "auto") -> Optional[BaseLLMProvider]:
        """选择提供商"""
        if provider_name == "auto":
            # 按优先级选择：zhipuai > openai > azure > baidu > qwen
            priority_order = ["zhipuai", "openai", "azure", "baidu", "qwen"]
            for name in priority_order:
                if name in self.available_providers:
                    return self.available_providers[name]
            return None
        else:
            return self.available_providers.get(provider_name)

    async def enhance(
        self,
        results: List[SearchResult],
        query: str,
        options: Dict[str, Any],
    ) -> Tuple[str | None, List[str], Dict[str, Dict[str, Any]]]:
        """执行增强。

        返回: (overall_summary, tags, per_result_dict)
        per_result_dict: { url: {"llm_summary": str | None, "labels": List[str]} }
        """
        want_summary: bool = bool(options.get("llm_summary", False))
        want_tags: bool = bool(options.get("llm_tags", False))
        per_result: bool = bool(options.get("llm_per_result", False))
        max_items: int = int(options.get("llm_max_items", 5))
        language: str = options.get("language", "zh")
        provider_name: str = options.get("model_provider", "auto")
        model_name: str = options.get("model_name", "")

        if not (want_summary or want_tags):
            return None, [], {}

        if not self.is_available():
            logger.info("LLM 增强未启用或不可用，跳过摘要/打标签。")
            return None, [], {}

        # 选择提供商
        provider = self._select_provider(provider_name)
        if not provider:
            logger.warning(f"指定的提供商 '{provider_name}' 不可用")
            return None, [], {}

        # 选取前 max_items 个结果用于整体摘要/标签
        top_items = results[: max(0, max_items)] if results else []
        overall_summary: str | None = None
        overall_tags: List[str] = []

        # 构造上下文
        def build_items_payload(items: List[SearchResult]) -> str:
            lines = []
            for idx, item in enumerate(items, start=1):
                snippet = (item.content or item.snippet or "").strip()
                if len(snippet) > 500:
                    snippet = snippet[:500] + "..."
                lines.append(
                    f"[{idx}] 标题: {item.title}\nURL: {item.url}\n摘要: {snippet}"
                )
            return "\n\n".join(lines)

        items_text = build_items_payload(top_items)

        system_prompt = (
            "你是一个高质量的信息整理助手，请用简洁准确的中文输出。"
            if language.startswith("zh")
            else "You are a high-quality information summarization assistant."
        )

        user_prompt_parts = [
            f"查询: {query}",
            "以下是检索到的网页要点：",
            items_text or "(无内容)",
        ]

        want_parts = []
        if want_summary:
            want_parts.append("1) 请输出不超过 200 字的整体总结。")
        if want_tags:
            want_parts.append(
                "2) 请输出 5-8 个中文标签（名词短语），只返回 JSON: {\"summary\": string|null, \"tags\": string[]}"
            )
        if want_parts:
            user_prompt_parts.append("\n".join(want_parts))

        user_prompt = "\n\n".join(user_prompt_parts)

        try:
            # 生成内容
            content = await provider.generate(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=model_name if model_name else None,
                temperature=0.3,
            )

            parsed: Dict[str, Any] = {"summary": None, "tags": []}
            if content:
                # 尝试解析为 JSON；若失败，做简单提取
                try:
                    parsed = json.loads(content)
                except Exception:
                    # 简单正则提取标签行
                    summary_guess = content.strip()
                    tags_guess: List[str] = []
                    m = re.search(r"\[.*\]", content, flags=re.S)
                    if m:
                        try:
                            tags_guess = json.loads(m.group(0))
                        except Exception:
                            tags_guess = []
                    parsed = {"summary": summary_guess, "tags": tags_guess}

            overall_summary = (
                str(parsed.get("summary")).strip() if want_summary else None
            )
            overall_tags = (
                [str(t).strip() for t in (parsed.get("tags") or [])]
                if want_tags
                else []
            )

        except Exception as e:
            logger.warning(f"LLM 生成整体摘要/标签失败: {e}")

        per_result_map: Dict[str, Dict[str, Any]] = {}
        if per_result and (want_summary or want_tags) and results:
            # 为控制成本，只对前 max_items 个做逐条增强
            async def enhance_single(item: SearchResult) -> None:
                try:
                    item_prompt = (
                        f"请基于以下内容生成精炼摘要(<=80字)和 3-6 个中文标签，返回 JSON: "
                        f"{{\"llm_summary\": string, \"labels\": string[]}}\n\n"
                        f"标题: {item.title}\nURL: {item.url}\n内容: {(item.content or item.snippet or '')[:800]}"
                    )
                    
                    content = await provider.generate(
                        [
                            {
                                "role": "system",
                                "content": system_prompt,
                            },
                            {"role": "user", "content": item_prompt},
                        ],
                        model=model_name if model_name else None,
                        temperature=0.2,
                    )

                    summary_val = None
                    labels_val: List[str] = []
                    if content:
                        try:
                            data = json.loads(content)
                            summary_val = data.get("llm_summary")
                            labels_val = list(map(str, data.get("labels", [])))
                        except Exception:
                            summary_val = content.strip()

                    per_result_map[item.url] = {
                        "llm_summary": summary_val,
                        "labels": labels_val,
                    }
                except Exception as e:
                    logger.debug(f"逐条增强失败: {e}")

            sem = asyncio.Semaphore(3)

            async def with_sem(item: SearchResult):
                async with sem:
                    await enhance_single(item)

            await asyncio.gather(
                *[with_sem(r) for r in results[: max(0, max_items)]]
            )

        return overall_summary, overall_tags, per_result_map

    async def close(self):
        """关闭并清理资源"""
        logger.info("正在关闭LLM增强器...")
        
        # 清理所有提供商的资源
        for provider in self.providers.values():
            if hasattr(provider, 'close') and callable(getattr(provider, 'close')):
                try:
                    await provider.close()
                except Exception as e:
                    logger.warning(f"关闭LLM提供商时出错: {e}")
        
        # 等待一小段时间确保所有异步任务完成
        await asyncio.sleep(0.1)
        
        logger.info("LLM增强器已关闭")
