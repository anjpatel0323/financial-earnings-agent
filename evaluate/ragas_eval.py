"""
RAGAS Evaluation
----------------
Measures the quality of your RAG pipeline on 4 metrics:

1. Faithfulness      — does the answer stick to the retrieved context? (no hallucination)
2. Answer relevancy  — does the answer actually address the question?
3. Context precision — are the retrieved chunks relevant to the question?
4. Context recall    — did we retrieve all the information needed?

Run with:
    python -m evaluate.ragas_eval
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from ingestion.vector_store import load_hybrid_retriever
from agent.tools import set_retriever, retrieve_filings

load_dotenv()

# ── Test questions ────────────────────────────────────────────────────────────
# These are question + ground truth pairs.
# Ground truth = what the correct answer SHOULD contain.
# RAGAS compares the agent's answer against these.

TEST_CASES = [
    {
        "question": "What were Apple's main revenue drivers in their latest 10-K?",
        "ground_truth": "Apple's main revenue drivers include iPhone sales, Services revenue including App Store and advertising, Mac computers, and Wearables. Services has been a growing segment contributing significantly to overall revenue.",
    },
    {
        "question": "What risk factors did Apple highlight related to competition?",
        "ground_truth": "Apple faces intense competition in all its product categories. The company competes with companies that have significant resources and brand recognition. Competition in the smartphone market is particularly intense.",
    },
    {
        "question": "How did Apple describe its gross margin performance?",
        "ground_truth": "Apple's gross margin improved due to favorable product mix shift toward higher-margin Services segment and operational efficiencies. The company reported improved gross margins compared to prior year.",
    },
    {
        "question": "What did Apple say about its Services segment growth?",
        "ground_truth": "Apple's Services segment showed strong growth driven by higher revenue from advertising, App Store, cloud services, and Apple Care. Services has become an increasingly important part of Apple's business.",
    },
    {
        "question": "What geographic markets did Apple identify as key revenue sources?",
        "ground_truth": "Apple generates revenue from Americas, Europe, Greater China, Japan, and Rest of Asia Pacific. The Americas and Europe are the largest markets, while Greater China represents a significant portion of revenue.",
    },
]


def run_evaluation():
    print("Loading retriever...")
    index_path = os.getenv("FAISS_INDEX_PATH", "data/index/faiss_index")
    retriever  = load_hybrid_retriever(index_path)
    set_retriever(retriever)

    print(f"Running {len(TEST_CASES)} test cases...\n")

    questions      = []
    answers        = []
    contexts       = []
    ground_truths  = []

    for i, case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] {case['question'][:60]}...")

        # Get retrieved context
        raw_context = retrieve_filings.invoke(case["question"])
        context_chunks = [raw_context]

        # Get answer from OpenAI directly (faster than full agent for eval)
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst. Answer based only on the provided context. Be concise.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{raw_context}\n\nQuestion: {case['question']}",
                },
            ],
            max_tokens=512,
        )
        answer = response.choices[0].message.content

        questions.append(case["question"])
        answers.append(answer)
        contexts.append(context_chunks)
        ground_truths.append(case["ground_truth"])

        print(f"   Answer: {answer[:100]}...")
        print()

    # ── Build RAGAS dataset ───────────────────────────────────────────────────
    dataset = Dataset.from_dict({
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths,
    })

    # ── Run RAGAS evaluation ──────────────────────────────────────────────────
    print("Running RAGAS evaluation...")

    llm        = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))

    results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=llm,
        embeddings=embeddings,
    )

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n" + "="*55)
    print("RAGAS EVALUATION RESULTS")
    print("="*55)
    df = results.to_pandas()
    print(f"\n{'Metric':<25} {'Score':<10} {'Rating'}")
    print("-"*55)

    metrics = {
        "faithfulness":      df["faithfulness"].mean(),
        "answer_relevancy":  df["answer_relevancy"].mean(),
        "context_precision": df["context_precision"].mean(),
        "context_recall":    df["context_recall"].mean(),
    }

    for metric, score in metrics.items():
        if score >= 0.8:
            rating = "EXCELLENT"
        elif score >= 0.6:
            rating = "GOOD"
        elif score >= 0.4:
            rating = "FAIR"
        else:
            rating = "NEEDS WORK"
        print(f"{metric:<25} {score:.3f}      {rating}")

    overall = sum(metrics.values()) / len(metrics)
    print("-"*55)
    print(f"{'Overall score':<25} {overall:.3f}")
    print("="*55)

    # ── Save results to JSON ──────────────────────────────────────────────────
    output = {
        "timestamp":   datetime.now().isoformat(),
        "num_tests":   len(TEST_CASES),
        "metrics":     {k: round(v, 4) for k, v in metrics.items()},
        "overall":     round(overall, 4),
        "per_question": json.loads(df.to_json(orient="records")),
    }

    os.makedirs("evaluate/results", exist_ok=True)
    out_path = f"evaluate/results/eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved → {out_path}")
    return output


if __name__ == "__main__":
    run_evaluation()