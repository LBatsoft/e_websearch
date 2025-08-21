"""
高级查询分析器使用示例

演示如何使用不同的查询分析方法：
1. 基于BERT的语义分析
2. 基于机器学习的分类
3. 基于LLM的深度分析
4. 混合式多模型集成
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.agent.advanced_query_analyzer import (
        BERTQueryAnalyzer,
        MLQueryClassifier,
        LLMQueryAnalyzer,
        HybridQueryAnalyzer,
        QueryAnalysisResult
    )
    from core.llm_enhancer import LLMEnhancer
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在项目根目录下运行此脚本，或者安装项目依赖")
    print("运行命令: cd /Users/morein/work/python/e_websearch && python examples/advanced_query_analysis_example.py")
    sys.exit(1)


async def demo_bert_analyzer():
    """演示BERT查询分析器"""
    print("=" * 60)
    print("🤖 BERT查询分析器演示")
    print("=" * 60)
    
    analyzer = BERTQueryAnalyzer()
    
    if not analyzer.is_available():
        print("❌ BERT分析器不可用（需要安装transformers和torch）")
        return
    
    test_queries = [
        "ChatGPT vs Claude 对比分析",
        "Python机器学习入门教程",
        "什么是区块链技术",
        "最新人工智能发展趋势"
    ]
    
    for query in test_queries:
        print(f"\n🔍 分析查询: {query}")
        
        # 查询编码
        vector = await analyzer.encode_query(query)
        if vector is not None:
            print(f"   📊 语义向量维度: {vector.shape}")
            print(f"   📊 向量前5维: {vector[:5]}")
        
        # 意图分类
        intent_scores = await analyzer.classify_intent(query)
        if intent_scores:
            print(f"   🎯 意图分类: {intent_scores}")


def demo_ml_classifier():
    """演示机器学习分类器"""
    print("\n" + "=" * 60)
    print("📊 机器学习分类器演示")
    print("=" * 60)
    
    classifier = MLQueryClassifier()
    
    if not classifier.available:
        print("❌ ML分类器不可用（需要安装scikit-learn）")
        return
    
    test_queries = [
        "ChatGPT vs Claude 对比分析",
        "Python机器学习入门教程", 
        "什么是区块链技术",
        "人工智能在医疗领域的具体应用案例和未来发展前景分析"
    ]
    
    for query in test_queries:
        print(f"\n🔍 分析查询: {query}")
        
        # 查询类型预测
        query_type, type_conf = classifier.predict_query_type(query)
        print(f"   📝 查询类型: {query_type} (置信度: {type_conf:.3f})")
        
        # 复杂度预测
        complexity, comp_conf = classifier.predict_complexity(query)
        print(f"   📏 复杂度: {complexity} (置信度: {comp_conf:.3f})")
        
        # 意图预测
        intent, intent_conf = classifier.predict_intent(query)
        print(f"   🎯 意图: {intent} (置信度: {intent_conf:.3f})")


async def demo_llm_analyzer():
    """演示LLM查询分析器"""
    print("\n" + "=" * 60)
    print("🧠 LLM查询分析器演示")
    print("=" * 60)
    
    # 初始化LLM增强器
    llm_enhancer = LLMEnhancer()
    analyzer = LLMQueryAnalyzer(llm_enhancer)
    
    if not analyzer.is_available():
        print("❌ LLM分析器不可用（需要配置LLM API）")
        return
    
    test_queries = [
        "ChatGPT vs Claude 对比分析",
        "如何系统学习深度学习并应用到实际项目中"
    ]
    
    for query in test_queries:
        print(f"\n🔍 分析查询: {query}")
        
        # Chain-of-Thought分析
        print("   🔗 Chain-of-Thought分析:")
        cot_result = await analyzer.analyze_with_cot(query)
        if cot_result:
            print(f"      {json.dumps(cot_result, indent=6, ensure_ascii=False)}")
        
        # Few-shot分析
        print("   🎯 Few-shot分析:")
        few_shot_result = await analyzer.analyze_with_few_shot(query)
        if few_shot_result:
            print(f"      {json.dumps(few_shot_result, indent=6, ensure_ascii=False)}")


async def demo_hybrid_analyzer():
    """演示混合式查询分析器"""
    print("\n" + "=" * 60)
    print("🔄 混合式查询分析器演示")
    print("=" * 60)
    
    # 初始化混合分析器
    llm_enhancer = LLMEnhancer()
    analyzer = HybridQueryAnalyzer(llm_enhancer)
    
    test_queries = [
        "ChatGPT vs Claude 对比分析",
        "Python机器学习入门教程",
        "什么是区块链技术",
        "人工智能在医疗领域的具体应用案例和未来发展前景分析",
        "如何系统学习深度学习并应用到实际项目中"
    ]
    
    for query in test_queries:
        print(f"\n🔍 分析查询: {query}")
        
        # 执行混合分析
        result = await analyzer.analyze_query(query)
        
        print(f"   📝 查询类型: {result.query_type}")
        print(f"   📏 复杂度: {result.complexity}")
        print(f"   🎯 意图: {result.intent}")
        print(f"   🏷️  实体: {result.entities}")
        print(f"   🔑 关键词: {result.keywords}")
        print(f"   🔄 需要多步: {result.requires_multiple_searches}")
        print(f"   📊 置信度分数: {result.confidence_scores}")
        
        if result.suggested_refinements:
            print(f"   💡 优化建议:")
            for i, refinement in enumerate(result.suggested_refinements, 1):
                print(f"      {i}. {refinement}")
        
        if result.semantic_features is not None:
            print(f"   🧠 语义特征维度: {result.semantic_features.shape}")
        
        if result.llm_analysis:
            print(f"   🤖 LLM分析可用: ✅")


def compare_analysis_methods():
    """比较不同分析方法的特点"""
    print("\n" + "=" * 60)
    print("📊 分析方法对比")
    print("=" * 60)
    
    comparison_data = [
        {
            "方法": "基于规则",
            "准确性": "中等",
            "速度": "很快",
            "资源消耗": "很低",
            "扩展性": "有限",
            "适用场景": "简单查询、快速响应"
        },
        {
            "方法": "机器学习",
            "准确性": "较高",
            "速度": "快",
            "资源消耗": "中等",
            "扩展性": "良好",
            "适用场景": "中等复杂度查询、批量处理"
        },
        {
            "方法": "BERT模型",
            "准确性": "高",
            "速度": "中等",
            "资源消耗": "较高",
            "扩展性": "很好",
            "适用场景": "语义理解、相似度计算"
        },
        {
            "方法": "LLM分析",
            "准确性": "很高",
            "速度": "较慢",
            "资源消耗": "高",
            "扩展性": "极好",
            "适用场景": "复杂查询、深度理解"
        },
        {
            "方法": "混合方式",
            "准确性": "很高",
            "速度": "中等",
            "资源消耗": "中高",
            "扩展性": "极好",
            "适用场景": "生产环境、全面分析"
        }
    ]
    
    # 打印对比表格
    headers = list(comparison_data[0].keys())
    
    # 计算列宽
    col_widths = {}
    for header in headers:
        col_widths[header] = max(
            len(header),
            max(len(str(row[header])) for row in comparison_data)
        ) + 2
    
    # 打印表头
    header_row = "|".join(header.center(col_widths[header]) for header in headers)
    print(header_row)
    print("-" * len(header_row))
    
    # 打印数据行
    for row in comparison_data:
        data_row = "|".join(str(row[header]).center(col_widths[header]) for header in headers)
        print(data_row)


def usage_recommendations():
    """使用建议"""
    print("\n" + "=" * 60)
    print("💡 使用建议")
    print("=" * 60)
    
    recommendations = [
        {
            "场景": "快速原型开发",
            "推荐方案": "基于规则的分析器",
            "理由": "实现简单，响应快速，无需额外依赖"
        },
        {
            "场景": "中小型应用",
            "推荐方案": "机器学习分类器",
            "理由": "准确性较高，资源消耗适中，易于部署"
        },
        {
            "场景": "语义搜索应用",
            "推荐方案": "BERT查询分析器",
            "理由": "语义理解能力强，支持向量化表示"
        },
        {
            "场景": "高精度要求",
            "推荐方案": "LLM查询分析器",
            "理由": "理解能力最强，可处理复杂查询"
        },
        {
            "场景": "生产环境",
            "推荐方案": "混合式分析器",
            "理由": "综合多种方法优势，准确性和鲁棒性最佳"
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. 场景: {rec['场景']}")
        print(f"   推荐方案: {rec['推荐方案']}")
        print(f"   理由: {rec['理由']}")


async def main():
    """主函数"""
    print("🚀 高级查询分析器演示")
    print("=" * 60)
    
    try:
        # 演示各种分析器
        await demo_bert_analyzer()
        demo_ml_classifier()
        await demo_llm_analyzer()
        await demo_hybrid_analyzer()
        
        # 方法对比和建议
        compare_analysis_methods()
        usage_recommendations()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
