#!/usr/bin/env python3
"""
示例运行脚本

解决 Python 路径问题，方便运行各种示例
"""

import sys
import os
import asyncio
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_basic_example():
    """运行基础搜索示例"""
    print("🚀 运行基础搜索示例")
    try:
        from examples.basic_example import main
        main()
    except ImportError as e:
        print(f"❌ 基础示例不可用: {e}")
    except Exception as e:
        print(f"❌ 运行基础示例时出错: {e}")

def run_llm_example():
    """运行LLM增强示例"""
    print("🤖 运行LLM增强示例")
    try:
        from examples.llm_enhanced_example import main
        asyncio.run(main())
    except ImportError as e:
        print(f"❌ LLM示例不可用: {e}")
    except Exception as e:
        print(f"❌ 运行LLM示例时出错: {e}")

def run_agent_example():
    """运行Search Agent示例"""
    print("🤖 运行Search Agent示例")
    try:
        from examples.agent_search_example import main
        main()
    except ImportError as e:
        print(f"❌ Agent示例不可用: {e}")
    except Exception as e:
        print(f"❌ 运行Agent示例时出错: {e}")

async def run_advanced_analyzer_example():
    """运行高级查询分析器示例"""
    print("🧠 运行高级查询分析器示例")
    try:
        from examples.advanced_query_analysis_example import main
        await main()
    except ImportError as e:
        print(f"❌ 高级分析器示例不可用: {e}")
        print("请安装可选依赖: pip install transformers torch scikit-learn")
    except Exception as e:
        print(f"❌ 运行高级分析器示例时出错: {e}")

def show_menu():
    """显示菜单"""
    print("\n" + "=" * 60)
    print("🎯 E-WebSearch 示例运行器")
    print("=" * 60)
    print("1. 基础搜索示例")
    print("2. LLM增强搜索示例")
    print("3. Search Agent示例")
    print("4. 高级查询分析器示例")
    print("5. 运行所有示例")
    print("0. 退出")
    print("=" * 60)

def main():
    """主函数"""
    while True:
        show_menu()
        
        try:
            choice = input("请选择要运行的示例 (0-5): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                run_basic_example()
            elif choice == "2":
                run_llm_example()
            elif choice == "3":
                run_agent_example()
            elif choice == "4":
                asyncio.run(run_advanced_analyzer_example())
            elif choice == "5":
                print("🚀 运行所有示例...")
                run_basic_example()
                print("\n" + "-" * 40 + "\n")
                run_llm_example()
                print("\n" + "-" * 40 + "\n")
                run_agent_example()
                print("\n" + "-" * 40 + "\n")
                asyncio.run(run_advanced_analyzer_example())
            else:
                print("❌ 无效选择，请输入 0-5")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 运行时出错: {e}")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main()

