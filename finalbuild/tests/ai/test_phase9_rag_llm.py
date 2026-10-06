from pathlib import Path
from ai.embeddings.providers import HashEmbeddingProvider
from ai.rag.reranker import LexicalReranker
from ai.rag.store import HybridKnowledgeStore, KnowledgeDocument
from ai.evaluation.grounding import GroundingEvaluator
from ai.evaluation.golden import GoldenCase, GoldenCaseEvaluator

import asyncio


def test_hash_embeddings_are_normalized_and_deterministic():
    provider = HashEmbeddingProvider(64)
    a = asyncio.run(provider.embed(["P0302 cylinder misfire"]))[0]
    b = asyncio.run(provider.embed(["P0302 cylinder misfire"]))[0]
    assert a == b
    assert abs(sum(x*x for x in a) - 1.0) < 1e-8


def test_reranker_prioritizes_exact_phrase():
    store = HybridKnowledgeStore([
        KnowledgeDocument("a", "P0302", "Cylinder 2 misfire diagnostic information"),
        KnowledgeDocument("b", "Generic", "Misfire information"),
    ])
    hits = store.search("P0302 cylinder 2 misfire")
    reranked = LexicalReranker().rerank("P0302 cylinder 2 misfire", hits)
    assert reranked[0].hit.document_id == "a"


def test_grounding_gate_flags_missing_terms():
    result = GroundingEvaluator().evaluate("The issue may be related to LPG calibration.", ["LPG calibration"], {"uncertainty", "LPG"})
    assert not result.grounded
    assert result.unsupported_claims == 0


def test_golden_case_evaluator_blocks_forbidden_claim():
    case = GoldenCase.load(Path("datasets/golden-cases/LPG_MISFIRE_001.yaml"))
    result = GoldenCaseEvaluator().evaluate({"ignition", "intake", "LPG_calibration"}, "confirmed_coil_failure", case)
    assert result.forbidden_claims_present
    assert not result.passed
