"""
FastAPI Backend
---------------
Exposes the agent via REST API.
Visit http://localhost:8000/docs to test it visually.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import build_agent, extract_citations

agent_executor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_executor
    print("Loading agent...")
    agent_executor = build_agent()
    print("Agent ready.")
    yield

app = FastAPI(
    title="Financial Earnings Intelligence Agent",
    description="RAG-powered agent for SEC filing analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]

@app.get("/health")
def health():
    return {"status": "ok", "agent_loaded": agent_executor is not None}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not agent_executor:
        raise HTTPException(status_code=503, detail="Agent not ready")
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: agent_executor.invoke({"input": request.question}),
        )
        citations = extract_citations(result.get("intermediate_steps", []))
        return QueryResponse(
            answer=result["output"],
            citations=citations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)