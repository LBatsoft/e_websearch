import json
import time

import requests


# API endpoint URL
AGENT_SEARCH_URL = "http://127.0.0.1:8000/agent/multi-search"


def run_agent_search(query: str):
    """
    Runs the agent search and prints the results.
    """
    payload = {
        "query": query,
        "sources": ["zai", "wechat", "zhihu"],
        "max_iterations": 3,
        "max_results_per_step": 4,
        "model_provider": "zhipuai",  # Or "openai", etc., depending on your setup
    }

    print(f"🚀 Starting agent search for: '{query}'")
    print("-" * 50)

    try:
        start_time = time.time()
        # Agent can take a long time, so set a generous timeout
        response = requests.post(AGENT_SEARCH_URL, json=payload, timeout=300)
        response.raise_for_status()  # Raise an exception for bad status codes
        end_time = time.time()

        data = response.json()

        if data.get("success"):
            print(
                f"✅ Agent search completed in {data.get('total_execution_time', end_time - start_time):.2f} seconds.\n"
            )

            print("=== Multi-Agent Search Results ===")
            print(f"📝 Message: {data.get('message', 'N/A')}")
            print(f"🔍 Session ID: {data.get('session_id', 'N/A')}")
            print(f"📊 Total Results: {data.get('total_count', 0)}")
            print(f"⏱️ Total Execution Time: {data.get('total_execution_time', 0):.2f}s")
            print()

            print("=== Search Results ===")
            for i, result in enumerate(data.get("results", []), 1):
                print(f"--- Result {i} ---")
                print(f"📄 Title: {result.get('title', 'N/A')}")
                print(f"🔗 URL: {result.get('url', 'N/A')}")
                print(f"📝 Summary: {result.get('summary', 'N/A')[:200]}...")
                print(f"⭐ Confidence: {result.get('confidence_score', 0):.2f}")
                print(f"🎯 Relevance: {result.get('relevance_score', 0):.2f}")
                print()

            print("=== Multi-Agent System Analysis ===")
            metadata = data.get('metadata', {})
            if metadata.get('multi_agent'):
                print(f"🤖 Agents Used: {', '.join(metadata.get('agents_used', []))}")
                print(f"📋 Total Tasks: {metadata.get('task_count', 0)}")
                
                execution_summary = metadata.get('execution_summary', {})
                print(f"🔍 Search Tasks: {execution_summary.get('search_tasks', 0)}")
                print(f"🔬 Analysis Tasks: {execution_summary.get('analyze_tasks', 0)}")
                print(f"🔗 Synthesis Tasks: {execution_summary.get('synthesize_tasks', 0)}")
                print(f"✅ Task Success Rate: {execution_summary.get('task_success_rate', 0):.2%}")
                print(f"⚡ Parallel Efficiency: {execution_summary.get('parallel_efficiency', 0):.2f}")
                
                # 显示智能体思考过程
                thought_process = metadata.get('thought_process', {})
                agent_thoughts = thought_process.get('agent_thoughts', [])
                
                print("\n=== Agent Thought Process ===")
                for agent_thought in agent_thoughts:
                    if agent_thought.get('decisions'):
                        print(f"🤖 Agent: {agent_thought.get('agent_id', 'Unknown')} ({agent_thought.get('agent_type', 'Unknown')})")
                        print(f"   📊 Decisions Made: {len(agent_thought.get('decisions', []))}")
                        print(f"   📈 Evaluations: {len(agent_thought.get('evaluations', []))}")
                        
                        # 显示最新的决策
                        decisions = agent_thought.get('decisions', [])
                        if decisions:
                            latest_decision = decisions[-1]
                            print(f"   🧠 Latest Decision: {latest_decision.get('type', 'N/A')}")
                            print(f"   📝 Outcome: {latest_decision.get('outcome', 'N/A')}")
                        print()

            print("=== Execution Summary ===")
            print(f"🔍 Total Searches: {data.get('total_searches', 0)}")
            print(f"🔄 Total Iterations: {data.get('total_iterations', 0)}")
            print(f"💾 Cache Hits: {data.get('cache_hits', 0)}")
            print(f"📚 Sources Used: {', '.join(data.get('sources_used', []))}")
        else:
            print(
                f"❌ Agent search failed: {data.get('error_message', 'Unknown error')}"
            )

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred while calling the API: {e}")
    except json.JSONDecodeError:
        print("❌ Failed to decode JSON response from the server.")


if __name__ == "__main__":
    # Example query for the agent
    complex_query = "2023年中国航天有哪些重要成就？2024年中国航天有哪些主要目标？"
    run_agent_search(complex_query)
