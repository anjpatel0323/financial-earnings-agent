"""
ReAct Agent
-----------
Wires together Claude on Bedrock + tools + memory.
"""

import os
import re
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

from agent.tools import ALL_TOOLS, set_retriever
from ingestion.vector_store import load_hybrid_retriever

load_dotenv()

SYSTEM_PROMPT = """You are a senior financial analyst assistant with expertise in SEC filings and earnings analysis.

You have access to a database of SEC filings. When answering:
1. Always search filings first
2. Cite sources explicitly — ticker, filing type, date, section
3. Use the calculator for any financial math
4. If data is unavailable, say so clearly

You have these tools:
{tools}

Use this exact format:

Question: the input question
Thought: what do I need to find and which tool to use
Action: tool name (one of [{tool_names}])
Action Input: input to the tool
Observation: tool result
... (repeat Thought/Action/Observation as needed)
Thought: I have enough to answer
Final Answer: complete answer with citations

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


def build_agent(index_path: str = None) -> AgentExecutor:
    index_path = index_path or os.getenv("FAISS_INDEX_PATH", "data/index/faiss_index")

    retriever = load_hybrid_retriever(index_path)
    set_retriever(retriever)

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=2048,
    )
    prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
    agent  = create_react_agent(llm=llm, tools=ALL_TOOLS, prompt=prompt)
    memory = ConversationBufferWindowMemory(k=6, return_messages=True)

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        memory=memory,
        verbose=True,
        max_iterations=8,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


def extract_citations(intermediate_steps: list) -> list[dict]:
    citations = []
    seen = set()
    for action, observation in intermediate_steps:
        if action.tool != "retrieve_filings":
            continue
        matches = re.findall(
            r"\[Source \d+: (\w+) ([\w-]+) ([\d-]+) — ([^\]]+)\]",
            observation,
        )
        for ticker, form_type, date, section in matches:
            key = (ticker, form_type, date, section)
            if key not in seen:
                seen.add(key)
                citations.append({
                    "ticker":      ticker,
                    "form_type":   form_type,
                    "filing_date": date,
                    "section":     section,
                })
    return citations


if __name__ == "__main__":
    agent_executor = build_agent()
    result = agent_executor.invoke({
        "input": "What were Apple's key revenue drivers in their most recent 10-K?"
    })
    print("\n" + "="*60)
    print("FINAL ANSWER:")
    print(result["output"])
    print("\nCITATIONS:")
    for c in extract_citations(result.get("intermediate_steps", [])):
        print(f"  - {c['ticker']} {c['form_type']} {c['filing_date']} [{c['section']}]")