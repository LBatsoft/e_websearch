#!/usr/bin/env python3
"""
E-WebSearch LLM 增强功能示例
演示如何使用 LLM 摘要和打标签功能
"""

import requests
import json
import time
from typing import Dict, List, Any


class EWebSearchLLMClient:
    """E-WebSearch API 客户端（支持 LLM 增强）"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "EWebSearch-LLM-Client/1.0",
            }
        )

    def search_with_llm(
        self,
        query: str,
        max_results: int = 10,
        sources: List[str] = None,
        filters: Dict[str, Any] = None,
        include_content: bool = False,
        # LLM 增强选项
        llm_summary: bool = False,
        llm_tags: bool = False,
        llm_per_result: bool = False,
        llm_max_items: int = 5,
        llm_language: str = "zh",
        model_provider: str = "auto",
        model_name: str = "",
    ) -> Dict[str, Any]:
        """执行带 LLM 增强的搜索"""

        if sources is None:
            sources = ["zai"]

        if filters is None:
            filters = {}

        data = {
            "query": query,
            "max_results": max_results,
            "include_content": include_content,
            "sources": sources,
            "filters": filters,
            # LLM 增强参数
            "llm_summary": llm_summary,
            "llm_tags": llm_tags,
            "llm_per_result": llm_per_result,
            "llm_max_items": llm_max_items,
            "llm_language": llm_language,
            "model_provider": model_provider,
            "model_name": model_name,
        }

        try:
            response = self.session.post(f"{self.base_url}/search", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"请求失败: {e}",
                "results": [],
                "total_count": 0,
            }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}


def demo_llm_summary():
    """演示 LLM 摘要功能"""

    client = EWebSearchLLMClient()

    print("📝 LLM 摘要功能演示")
    print("=" * 50)

    # 检查服务健康状态
    health = client.health_check()
    if health.get("status") != "healthy":
        print("❌ 服务不可用，请检查 API 服务是否正常运行")
        return

    # 执行带摘要的搜索
    query = "人工智能在医疗领域的应用"
    print(f"\n🔍 搜索查询: {query}")
    print("📝 启用 LLM 摘要功能...")

    result = client.search_with_llm(
        query=query,
        max_results=8,
        sources=["zai"],
        llm_summary=True,
        llm_tags=True,
        llm_per_result=False,
        llm_max_items=6,
        model_provider="zhipuai",
        model_name="glm-4",
    )

    if result["success"]:
        print(f"✅ 搜索成功，找到 {result['total_count']} 个结果")
        print(f"⏱️ 执行时间: {result['execution_time']:.2f}秒")

        # 显示 LLM 摘要
        if result.get("llm_summary"):
            print(f"\n📝 LLM 摘要:")
            print(f"   {result['llm_summary']}")

        # 显示 LLM 标签
        if result.get("llm_tags"):
            print(f"\n🏷️ LLM 标签:")
            for tag in result["llm_tags"]:
                print(f"   • {tag}")

        # 显示搜索结果
        print(f"\n📋 搜索结果:")
        for i, item in enumerate(result["results"][:3], 1):
            print(f"{i}. {item['title']}")
            print(f"   {item['snippet'][:100]}...")
            print(f"   🔗 {item['url']}")
    else:
        print(f"❌ 搜索失败: {result['message']}")


def demo_per_result_enhancement():
    """演示逐条结果增强功能"""

    client = EWebSearchLLMClient()

    print("\n🎯 逐条结果增强功能演示")
    print("=" * 50)

    query = "Python 机器学习框架"
    print(f"\n🔍 搜索查询: {query}")
    print("🎯 启用逐条结果增强...")

    result = client.search_with_llm(
        query=query,
        max_results=5,
        sources=["zai"],
        llm_summary=False,
        llm_tags=False,
        llm_per_result=True,
        llm_max_items=4,
        model_provider="zhipuai",
        model_name="glm-4",
    )

    if result["success"]:
        print(f"✅ 搜索成功，找到 {result['total_count']} 个结果")

        # 显示逐条增强结果
        per_result_data = result.get("llm_per_result", {})

        for i, item in enumerate(result["results"], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   🔗 {item['url']}")

            # 获取该结果的增强数据
            enhanced_data = per_result_data.get(item["url"], {})

            if enhanced_data.get("llm_summary"):
                print(f"   📝 摘要: {enhanced_data['llm_summary']}")

            if enhanced_data.get("labels"):
                print(f"   🏷️ 标签: {', '.join(enhanced_data['labels'])}")
    else:
        print(f"❌ 搜索失败: {result['message']}")


def main():
    """主函数"""

    import argparse

    parser = argparse.ArgumentParser(description="E-WebSearch LLM 增强功能演示")
    parser.add_argument("--summary", action="store_true", help="演示摘要功能")
    parser.add_argument("--per-result", action="store_true", help="演示逐条增强功能")
    parser.add_argument(
        "--api-url", default="http://localhost:8000", help="API 服务地址"
    )

    args = parser.parse_args()

    if args.summary:
        demo_llm_summary()
    elif args.per_result:
        demo_per_result_enhancement()
    else:
        print("请指定演示类型:")
        print("  --summary: 摘要功能演示")
        print("  --per-result: 逐条增强演示")
        parser.print_help()


if __name__ == "__main__":
    main()
