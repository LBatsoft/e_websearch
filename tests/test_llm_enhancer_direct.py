#!/usr/bin/env python3
"""
直接测试 LLM 增强器
"""

import os
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env")

from core.llm_enhancer import LLMEnhancer
from core.models import SearchResult, SourceType

async def test_llm_enhancer():
    """测试 LLM 增强器"""
    
    print("🧠 测试 LLM 增强器")
    print("=" * 50)
    
    # 创建 LLM 增强器
    enhancer = LLMEnhancer()
    
    print(f"✅ LLM 增强器初始化完成")
    print(f"可用提供商: {list(enhancer.available_providers.keys())}")
    
    if not enhancer.is_available():
        print("❌ 没有可用的 LLM 提供商")
        return
    
    # 创建模拟搜索结果
    mock_results = [
        SearchResult(
            title="机器学习在医疗领域的应用",
            url="https://example.com/1",
            snippet="机器学习技术正在医疗领域发挥重要作用，包括疾病诊断、药物研发等方面。",
            source=SourceType.ZAI,
            content="机器学习技术正在医疗领域发挥重要作用，包括疾病诊断、药物研发等方面。通过分析大量医疗数据，机器学习算法能够帮助医生更准确地诊断疾病，预测患者风险，并协助药物研发过程。",
            score=0.9
        ),
        SearchResult(
            title="人工智能在金融行业的应用",
            url="https://example.com/2", 
            snippet="人工智能技术在金融行业有广泛应用，包括风险评估、欺诈检测等。",
            source=SourceType.ZAI,
            content="人工智能技术在金融行业有广泛应用，包括风险评估、欺诈检测、智能投顾等。通过机器学习算法，金融机构能够更准确地评估客户信用风险，实时检测异常交易，并提供个性化的投资建议。",
            score=0.8
        )
    ]
    
    print(f"📋 创建了 {len(mock_results)} 个模拟搜索结果")
    
    # 测试 LLM 增强
    try:
        overall_summary, overall_tags, per_result_map = await enhancer.enhance(
            results=mock_results,
            query="人工智能应用",
            options={
                "llm_summary": True,
                "llm_tags": True,
                "llm_per_result": True,
                "llm_max_items": 2,
                "language": "zh",
                "model_provider": "zhipuai",
                "model_name": "glm-4"
            }
        )
        
        print("✅ LLM 增强调用成功")
        print(f"📝 整体摘要: {overall_summary}")
        print(f"🏷️ 整体标签: {overall_tags}")
        print(f"🎯 逐条增强: {len(per_result_map)} 个结果")
        
        for url, enhanced in per_result_map.items():
            print(f"   {url}:")
            print(f"     摘要: {enhanced.get('llm_summary')}")
            print(f"     标签: {enhanced.get('labels')}")
            
    except Exception as e:
        print(f"❌ LLM 增强测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_enhancer())
