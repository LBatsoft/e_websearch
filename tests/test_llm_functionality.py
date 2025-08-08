#!/usr/bin/env python3
"""
LLM 功能测试脚本
"""

import requests
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env")


def test_llm_functionality():
    """测试 LLM 增强功能"""
    
    print("🤖 LLM 增强功能测试")
    print("=" * 50)
    
    # 检查环境变量
    print("\n📋 环境变量检查:")
    llm_vars = [
        "ZAI_API_KEY",
        "OPENAI_API_KEY", 
        "AZURE_OPENAI_API_KEY",
        "BAIDU_API_KEY",
        "DASHSCOPE_API_KEY"
    ]
    
    available_providers = []
    for var in llm_vars:
        value = os.getenv(var, "")
        status = "✅ 已配置" if value else "❌ 未配置"
        print(f"   {var}: {status}")
        if value:
            available_providers.append(var.replace("_API_KEY", "").lower())
    
    print(f"\n可用提供商: {available_providers}")
    
    # 测试 API 健康状态
    print("\n🏥 API 健康检查:")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   状态: {health_data.get('status', 'unknown')}")
            print(f"   可用搜索源: {health_data.get('available_sources', [])}")
        else:
            print(f"   ❌ API 服务不可用 (状态码: {response.status_code})")
            return
    except Exception as e:
        print(f"   ❌ 无法连接到 API 服务: {e}")
        return
    
    # 测试基础搜索
    print("\n🔍 基础搜索测试:")
    try:
        response = requests.post(
            "http://localhost:8000/search",
            json={
                "query": "人工智能发展趋势",
                "max_results": 3,
                "sources": ["zai"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"   ✅ 基础搜索成功")
                print(f"   结果数量: {data.get('total_count', 0)}")
                print(f"   执行时间: {data.get('execution_time', 0):.2f}秒")
            else:
                print(f"   ❌ 基础搜索失败: {data.get('message', '未知错误')}")
        else:
            print(f"   ❌ API 请求失败 (状态码: {response.status_code})")
    except Exception as e:
        print(f"   ❌ 搜索请求异常: {e}")
    
    # 测试 LLM 增强功能
    print("\n🧠 LLM 增强功能测试:")
    
    if not available_providers:
        print("   ⚠️ 没有配置 LLM API 密钥，跳过 LLM 测试")
        print("   💡 请配置以下环境变量之一:")
        print("      - ZAI_API_KEY (推荐)")
        print("      - OPENAI_API_KEY")
        print("      - AZURE_OPENAI_API_KEY")
        print("      - BAIDU_API_KEY")
        print("      - DASHSCOPE_API_KEY")
        return
    
    # 选择第一个可用的提供商
    provider = available_providers[0]
    print(f"   使用提供商: {provider}")
    
    try:
        response = requests.post(
            "http://localhost:8000/search",
            json={
                "query": "机器学习应用",
                "max_results": 5,
                "sources": ["zai"],
                "llm_summary": True,
                "llm_tags": True,
                "llm_per_result": True,
                "llm_max_items": 4,
                "model_provider": provider,
                "model_name": ""
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"   ✅ LLM 增强搜索成功")
                print(f"   结果数量: {data.get('total_count', 0)}")
                print(f"   执行时间: {data.get('execution_time', 0):.2f}秒")
                
                # 检查 LLM 输出
                llm_summary = data.get("llm_summary")
                llm_tags = data.get("llm_tags", [])
                llm_per_result = data.get("llm_per_result", {})
                
                if llm_summary and llm_summary != "None":
                    print(f"   📝 摘要: {llm_summary[:100]}...")
                else:
                    print(f"   ⚠️ 摘要: 未生成或为空")
                
                if llm_tags:
                    print(f"   🏷️ 标签: {', '.join(llm_tags)}")
                else:
                    print(f"   ⚠️ 标签: 未生成或为空")
                
                if llm_per_result:
                    print(f"   🎯 逐条增强: {len(llm_per_result)} 个结果")
                else:
                    print(f"   ⚠️ 逐条增强: 未生成或为空")
                    
            else:
                print(f"   ❌ LLM 增强搜索失败: {data.get('message', '未知错误')}")
        else:
            print(f"   ❌ API 请求失败 (状态码: {response.status_code})")
    except Exception as e:
        print(f"   ❌ LLM 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")


def main():
    """主函数"""
    test_llm_functionality()


if __name__ == "__main__":
    main()
