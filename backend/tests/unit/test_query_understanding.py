"""
VEDANTA Unit Tests — Query Understanding and Abbreviation Expansion
"""

import pytest
from app.intelligence.query_understanding.query_understander import (
    QueryUnderstander,
    expand_abbreviations,
    normalize_query,
)


def test_abbreviation_expansion():
    text = "Who is the HOD of CE at MITAOE?"
    expanded = expand_abbreviations(text)
    assert "Head of Department" in expanded
    assert "Computer Engineering" in expanded
    assert "MIT Academy of Engineering" in expanded


def test_intent_classification_statistical():
    understander = QueryUnderstander()
    ctx = understander.understand("What is the average placement package and highest salary in LPA?")
    assert ctx.intent == "statistical"
    assert ctx.is_statistical is True


def test_intent_classification_entity():
    understander = QueryUnderstander()
    ctx = understander.understand("Who is Dr. Sandip Gade?")
    assert ctx.intent == "entity_lookup"
    assert len(ctx.entities) > 0


def test_intent_classification_comparison():
    understander = QueryUnderstander()
    ctx = understander.understand("Compare Computer Engineering placements versus Mechanical Engineering")
    assert ctx.intent == "comparison"
    assert ctx.is_comparison is True


def test_query_decomposition():
    understander = QueryUnderstander()
    ctx = understander.understand("Who is the HOD of CE and what are the latest placement statistics?")
    assert len(ctx.sub_queries) == 2
    assert "CE" in ctx.sub_queries[0] or "HOD" in ctx.sub_queries[0]
