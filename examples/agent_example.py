import json
import time

import requests


# API endpoint URL
AGENT_SEARCH_URL = "http://localhost:8000/agent_search"


def run_agent_search(query: str):
    """
    Runs the agent search and prints the results.
    """
    payload = {
        "query": query,
        "sources": ["zai", "bing"],
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
                f"✅ Agent search completed in {data.get('execution_time', end_time - start_time):.2f} seconds.\n"
            )

            print("=== Final Answer ===")
            print(data["final_answer"])
            print("\n" + "=" * 20 + "\n")

            print("=== Intermediate Steps ===")
            for step in data.get("intermediate_steps", []):
                print(f"--- Step {step['step_index']} ---")
                print(f"🤔 Thought: {step['thought']}")
                print(f"🛠️ Tool: {step['tool']}")
                print(f"📝 Tool Input: {json.dumps(step['tool_input'], indent=2)}")
                print("👀 Observation:")
                if step["observation"]:
                    for obs in step["observation"]:
                        print(f"  - [{obs['source']}] {obs['title']}")
                        print(f"    {obs['url']}")
                else:
                    print("  - No results found.")
                print("-" * 25)
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
    complex_query = "What were the key advancements in space exploration in 2023, and what are the main goals for major space agencies in 2024?"
    run_agent_search(complex_query)
