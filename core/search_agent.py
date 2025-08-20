"""
Search Agent: A multi-step research assistant.
"""
import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional

from loguru import logger

from api.models import AgentSearchRequest, AgentSearchResponse, AgentStep, SearchResultAPI
from core.llm_enhancer import LLMEnhancer, BaseLLMProvider
from core.models import SearchRequest, SearchResult
from core.search_orchestrator import SearchOrchestrator


class SearchAgent:
    """
    Search Agent that can break down a complex query, run multiple searches,
    and synthesize the results into a comprehensive answer.
    """

    def __init__(self, orchestrator: SearchOrchestrator, llm_enhancer: LLMEnhancer):
        self.orchestrator = orchestrator
        self.llm_enhancer = llm_enhancer
        self.provider: Optional[BaseLLMProvider] = None
        logger.info("Search Agent initialized.")

    def _select_provider(self, provider_name: str = "auto") -> Optional[BaseLLMProvider]:
        """Selects an LLM provider."""
        # This logic is borrowed from LLMEnhancer
        if provider_name == "auto":
            priority_order = ["zhipuai", "openai", "azure", "baidu", "qwen"]
            for name in priority_order:
                if name in self.llm_enhancer.available_providers:
                    return self.llm_enhancer.available_providers[name]
            return None
        else:
            return self.llm_enhancer.available_providers.get(provider_name)

    async def run(self, request: AgentSearchRequest) -> AgentSearchResponse:
        """
        Runs the search agent workflow.
        """
        start_time = time.time()
        logger.info(f"Agent starting run for query: '{request.query}'")
        self.provider = self._select_provider(request.model_provider)

        if not self.provider or not self.provider.is_available():
            logger.error("No available LLM provider for Search Agent.")
            return AgentSearchResponse(
                success=False,
                final_answer="Agent could not run because no LLM provider is available.",
                intermediate_steps=[],
                query=request.query,
                execution_time=time.time() - start_time,
                error_message="No available LLM provider.",
            )

        intermediate_steps: List[AgentStep] = []
        try:
            # 1. Plan: Generate search queries
            planned_queries = await self._generate_plan(request.query, request.model_name)

            # 2. Execute: Run searches and gather evidence
            evidence = []
            for i, sub_query in enumerate(planned_queries):
                step_start_time = time.time()
                logger.info(f"Agent executing sub-query: '{sub_query}'")

                search_request = SearchRequest(
                    query=sub_query,
                    max_results=request.max_results_per_step,
                    sources=request.sources,
                )

                search_response = await self.orchestrator.search(search_request)

                # Convert core SearchResult to API SearchResultAPI for observation
                observation = [self._convert_to_api_result(r) for r in search_response.results]

                step = AgentStep(
                    step_index=i + 1,
                    thought=f"I need to investigate: '{sub_query}'.",
                    tool="search",
                    tool_input={"query": sub_query, "sources": request.sources},
                    observation=observation,
                )
                intermediate_steps.append(step)

                # Format evidence for the final synthesis step
                for result in search_response.results:
                    evidence.append(
                        f"Title: {result.title}\nURL: {result.url}\nSnippet: {result.snippet}\n"
                    )

            # 3. Synthesize: Generate the final answer
            final_answer = await self._synthesize_answer(request.query, evidence, request.model_name)

            execution_time = time.time() - start_time
            logger.info(f"Agent run finished in {execution_time:.2f}s.")

            return AgentSearchResponse(
                success=True,
                final_answer=final_answer,
                intermediate_steps=intermediate_steps,
                query=request.query,
                execution_time=execution_time,
            )
        except Exception as e:
            logger.error(f"Agent run failed: {e}", exc_info=True)
            execution_time = time.time() - start_time
            return AgentSearchResponse(
                success=False,
                final_answer="",
                intermediate_steps=intermediate_steps,
                query=request.query,
                execution_time=execution_time,
                error_message=str(e),
            )

    async def _generate_plan(self, query: str, model_name: str) -> List[str]:
        """
        Generates a research plan (a list of search queries).
        """
        prompt = f"""
As an expert research analyst, your task is to devise a step-by-step research plan for the given query.
Break down the main query into 2-4 specific, targeted search queries that will collectively gather the necessary information.
Return the result as a JSON object with a single key "queries" containing a list of strings.

Main Query: "{query}"

JSON Output:
"""
        messages = [{"role": "user", "content": prompt}]

        response_text = await self.provider.generate(messages, model=model_name)

        if not response_text:
            logger.warning("LLM failed to generate a plan. Using the original query as a fallback.")
            return [query]

        try:
            # Extract JSON from markdown code block if present
            match = re.search(r"```(?:json)?\n([\s\S]*?)\n```", response_text)
            if match:
                response_text = match.group(1)

            data = json.loads(response_text)
            queries = data.get("queries", [])
            if not queries or not isinstance(queries, list):
                logger.warning(f"LLM generated an invalid plan. Fallback to original query. Response: {response_text}")
                return [query]
            return queries
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode plan from LLM. Fallback to original query. Response: {response_text}")
            return [query]

    async def _synthesize_answer(self, query: str, evidence: List[str], model_name: str) -> str:
        """
        Synthesizes the final answer from the collected evidence.
        """
        evidence_str = "\n\n---\n\n".join(evidence)
        prompt = f"""
As a professional research analyst, your task is to provide a comprehensive and well-structured answer to the user's query.
Base your answer *strictly* on the provided research evidence. Do not use any external knowledge.
Cite the sources used in your answer by referencing the URL.

User's Query: "{query}"

Research Evidence:
{evidence_str}

Final Answer:
"""
        messages = [{"role": "user", "content": prompt}]

        final_answer = await self.provider.generate(messages, model=model_name, temperature=0.5)

        return final_answer or "Could not synthesize an answer based on the provided evidence."

    def _convert_to_api_result(self, core_result: SearchResult) -> SearchResultAPI:
        """Converts a core SearchResult to an API SearchResultAPI model."""
        return SearchResultAPI(
            title=core_result.title,
            url=core_result.url,
            snippet=core_result.snippet,
            source=core_result.source.value, # Convert enum to string
            score=core_result.score,
            publish_time=core_result.publish_time,
            author=core_result.author,
            content=core_result.content,
            images=core_result.images,
            metadata=core_result.metadata,
            llm_summary=core_result.llm_summary,
            labels=core_result.labels,
        )

    async def close(self):
        """Clean up resources."""
        logger.info("Closing Search Agent.")
        # The provider is managed by the enhancer, so no need to close it here.
        await asyncio.sleep(0.1)
