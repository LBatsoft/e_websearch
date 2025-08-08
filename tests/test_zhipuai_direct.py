#!/usr/bin/env python3
"""
直接测试智谱AI API
"""

import os
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from zhipuai import ZhipuAI

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env")


async def test_zhipuai():
    """测试智谱AI API"""

    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print("❌ ZAI_API_KEY 未配置")
        return

    print(f"✅ ZAI_API_KEY 已配置: {api_key[:10]}...")

    try:
        client = ZhipuAI(api_key=api_key)
        print("✅ 智谱AI 客户端初始化成功")

        # 测试简单对话
        response = client.chat.completions.create(
            model="glm-4",
            messages=[{"role": "user", "content": "你好，请简单介绍一下机器学习"}],
            temperature=0.3,
        )

        print("✅ API 调用成功")
        print(f"📝 响应: {response.choices[0].message.content}")

    except Exception as e:
        print(f"❌ 智谱AI 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_zhipuai())
