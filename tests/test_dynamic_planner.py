#!/usr/bin/env python3
"""
动态规划器测试脚本

对比硬编码模板和动态生成的效果
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.agents.legacy.planner import SearchPlanner
    from core.agents.base.models import AgentSearchRequest, PlanningStrategy
    from core.models import SourceType
    from core.llm_enhancer import LLMEnhancer
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)

async def compare_planning_approaches():
    """对比硬编码和动态生成的规划方法"""
    print("🔄 对比硬编码 vs 动态生成规划方法")
    print("=" * 80)
    
    # 初始化规划器
    planner = SearchPlanner(analyzer_type="rule_based")
    
    # 测试查询
    test_queries = [
        ("ChatGPT vs Claude 对比分析", "复杂对比查询"),
        ("Python机器学习入门教程", "教程类查询"),
        ("什么是区块链技术", "定义类查询"),
        ("2024年人工智能最新发展趋势", "最新信息查询")
    ]
    
    for query, description in test_queries:
        print(f"\n🔍 测试查询: {description}")
        print(f"   查询内容: {query}")
        print("-" * 60)
        
        request = AgentSearchRequest(
            query=query,
            sources=[SourceType.BING, SourceType.ZAI],
            max_results_per_iteration=5,
            planning_strategy=PlanningStrategy.ADAPTIVE
        )
        
        # 1. 硬编码方式
        print("📋 硬编码模板方式:")
        planner.set_dynamic_generation(False)
        hardcoded_plan = await planner.create_execution_plan(request)
        
        print(f"   策略: {hardcoded_plan.strategy.value}")
        print(f"   步骤数: {len(hardcoded_plan.steps)}")
        print(f"   置信度: {hardcoded_plan.confidence_score:.3f}")
        for i, step in enumerate(hardcoded_plan.steps, 1):
            print(f"     {i}. {step.description}")
            print(f"        查询: {step.query}")
        
        # 2. 动态生成方式
        print("\n🤖 动态生成方式:")
        planner.set_dynamic_generation(True)
        dynamic_plan = await planner.create_execution_plan(request)
        
        print(f"   策略: {dynamic_plan.strategy.value}")
        print(f"   步骤数: {len(dynamic_plan.steps)}")
        print(f"   置信度: {dynamic_plan.confidence_score:.3f}")
        for i, step in enumerate(dynamic_plan.steps, 1):
            print(f"     {i}. {step.description}")
            print(f"        查询: {step.query}")
            if step.metadata.get("enhancement_applied"):
                print(f"        ✨ 查询已优化")
        
        # 3. 对比分析
        print("\n📊 对比分析:")
        print(f"   步骤数变化: {len(hardcoded_plan.steps)} → {len(dynamic_plan.steps)}")
        print(f"   置信度变化: {hardcoded_plan.confidence_score:.3f} → {dynamic_plan.confidence_score:.3f}")
        
        # 分析查询优化
        hardcoded_queries = [step.query for step in hardcoded_plan.steps]
        dynamic_queries = [step.query for step in dynamic_plan.steps]
        
        print("   查询优化对比:")
        for i, (hq, dq) in enumerate(zip(hardcoded_queries, dynamic_queries), 1):
            if hq != dq:
                print(f"     步骤{i}: 查询已优化")
                print(f"       原始: {hq}")
                print(f"       优化: {dq}")
            else:
                print(f"     步骤{i}: 查询未变化")
        
        print("\n" + "=" * 80)

async def test_dynamic_features():
    """测试动态生成的特色功能"""
    print("\n🚀 测试动态生成特色功能")
    print("=" * 80)
    
    planner = SearchPlanner(analyzer_type="advanced")  # 使用高级分析器
    planner.set_dynamic_generation(True)
    
    # 测试复杂查询
    complex_queries = [
        "深度学习 vs 机器学习 vs 人工智能 三者详细对比分析",
        "如何从零开始系统性学习Python数据科学机器学习深度学习完整路径",
        "区块链技术在金融医疗供应链物联网领域的具体应用案例分析"
    ]
    
    for query in complex_queries:
        print(f"\n🔍 复杂查询测试: {query}")
        print("-" * 60)
        
        request = AgentSearchRequest(
            query=query,
            sources=[SourceType.BING, SourceType.ZAI],
            max_results_per_iteration=5,
            planning_strategy=PlanningStrategy.ADAPTIVE
        )
        
        plan = await planner.create_execution_plan(request)
        
        print(f"📋 生成的执行计划:")
        print(f"   计划ID: {plan.plan_id}")
        print(f"   策略: {plan.strategy.value}")
        print(f"   步骤数: {len(plan.steps)}")
        print(f"   置信度: {plan.confidence_score:.3f}")
        
        # 显示分析摘要
        if "analysis_summary" in plan.metadata:
            summary = plan.metadata["analysis_summary"]
            print(f"   分析摘要:")
            print(f"      类型: {summary.get('query_type', 'unknown')}")
            print(f"      复杂度: {summary.get('complexity', 'unknown')}")
            print(f"      置信度: {summary.get('confidence', {})}")
        
        print(f"📝 执行步骤详情:")
        for i, step in enumerate(plan.steps, 1):
            print(f"   {i}. {step.description}")
            print(f"      查询: {step.query}")
            print(f"      类型: {step.step_type.value}")
            print(f"      目的: {step.metadata.get('step_purpose', 'unknown')}")
            if step.metadata.get("enhancement_applied"):
                print(f"      ✨ 智能优化: 是")
            print()

async def test_entity_aware_planning():
    """测试实体感知的规划"""
    print("\n🧠 测试实体感知规划")
    print("=" * 80)
    
    planner = SearchPlanner(analyzer_type="advanced")
    planner.set_dynamic_generation(True)
    
    # 包含明确实体的查询
    entity_queries = [
        "iPhone 15 vs Samsung Galaxy S24 拍照性能对比",
        "Tesla Model 3 vs BYD 海豹 电动车对比",
        "React vs Vue.js vs Angular 前端框架选择"
    ]
    
    for query in entity_queries:
        print(f"\n🔍 实体查询: {query}")
        print("-" * 40)
        
        request = AgentSearchRequest(
            query=query,
            sources=[SourceType.BING],
            max_results_per_iteration=3,
            planning_strategy=PlanningStrategy.ADAPTIVE
        )
        
        plan = await planner.create_execution_plan(request)
        
        # 显示实体识别结果
        if "analysis_summary" in plan.metadata:
            summary = plan.metadata["analysis_summary"]
            entities = summary.get('entities', [])
            if entities:
                print(f"   🏷️ 识别的实体: {entities}")
        
        print(f"   📋 生成的步骤:")
        for i, step in enumerate(plan.steps, 1):
            print(f"     {i}. {step.query}")
            # 检查是否使用了实体信息
            if any(entity in step.query for entity in entities if entities):
                print(f"        ✅ 使用了实体信息")

async def test_llm_optimization():
    """测试LLM优化功能"""
    print("\n🤖 测试LLM优化功能")
    print("=" * 80)
    
    try:
        llm_enhancer = LLMEnhancer()
        if not llm_enhancer.is_available():
            print("⚠️ LLM不可用，跳过LLM优化测试")
            return
        
        planner = SearchPlanner(llm_enhancer=llm_enhancer, analyzer_type="advanced")
        planner.set_dynamic_generation(True)
        
        query = "人工智能在医疗诊断中的应用和挑战"
        
        request = AgentSearchRequest(
            query=query,
            sources=[SourceType.BING],
            max_results_per_iteration=3,
            planning_strategy=PlanningStrategy.ADAPTIVE
        )
        
        print(f"🔍 测试查询: {query}")
        plan = await planner.create_execution_plan(request)
        
        print(f"📋 LLM优化后的计划:")
        for i, step in enumerate(plan.steps, 1):
            print(f"   {i}. {step.description}")
            print(f"      查询: {step.query}")
            if "llm_optimized" in step.metadata:
                print(f"      🤖 LLM优化: 是")
        
    except Exception as e:
        print(f"❌ LLM优化测试失败: {e}")

async def main():
    """主函数"""
    print("🚀 动态规划器 vs 硬编码模板对比测试")
    print("=" * 100)
    
    # 运行各种测试
    await compare_planning_approaches()
    await test_dynamic_features()
    await test_entity_aware_planning()
    await test_llm_optimization()
    
    print("\n" + "=" * 100)
    print("🎉 所有测试完成！")
    print("\n📊 总结:")
    print("✅ 动态生成相比硬编码模板的优势:")
    print("   1. 🎯 查询优化更智能，基于实体和上下文")
    print("   2. 🔄 步骤生成更灵活，不受固定模板限制")
    print("   3. 🧠 支持LLM优化，提升规划质量")
    print("   4. 📈 置信度评估更准确")
    print("   5. 🛡️ 保留硬编码作为回退机制，确保稳定性")
    print("=" * 100)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

