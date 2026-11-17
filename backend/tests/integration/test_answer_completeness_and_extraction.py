"""
VEDANTA — Answer Completeness and Semantic Extraction Regression Test Suite
Validates relationship-aware entity extraction, semantic section isolation (Vision vs Mission),
clean markdown formatting without navigation noise, and strict completeness validation.
"""

import pytest
from app.intelligence.query_understanding.query_understander import QueryUnderstander
from app.retrieval.pipeline import get_retrieval_pipeline
from app.intelligence.answer_engine.evidence_validator import EvidenceValidator
from app.intelligence.answer_engine.answer_composer import AnswerComposer


@pytest.fixture(scope="module")
def components():
    return {
        "understander": QueryUnderstander(),
        "pipeline": get_retrieval_pipeline(),
        "validator": EvidenceValidator(),
        "composer": AnswerComposer(),
    }


def test_role_holder_chairman(components):
    """Verify Chairman role resolves with person name and Governing Body source."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("Who is the Chairman of the Governing Body?")
    assert qc.requested_intent_category == "role_holder"
    assert qc.target_role == "Chairman"
    assert "person_name" in qc.required_fields

    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)
    assert val.status == "verified"
    assert val.confidence >= 0.85

    ans = composer.compose(qc, val)
    assert ans.is_answerable is True
    assert "Dr. Sanjay Dhande" in ans.answer_text
    assert "Chairman" in ans.answer_text


def test_role_holder_registrar(components):
    """Verify Registrar role resolves with person name."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("Who is the Registrar of MITAOE?")
    assert qc.requested_intent_category == "role_holder"
    assert qc.target_role == "Registrar"

    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)
    assert val.status == "verified"

    ans = composer.compose(qc, val)
    assert "Bhagat" in ans.answer_text
    assert "Registrar" in ans.answer_text


def test_role_holder_civil_hod(components):
    """Verify Civil Engineering HOD resolves with person name."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("Who is the HOD of Civil Engineering?")
    assert qc.requested_intent_category == "role_holder"
    assert qc.target_role == "Head of Department"
    assert "Civil Engineering" in qc.departments

    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)
    assert val.status == "verified"

    ans = composer.compose(qc, val)
    assert "Dr. Nilesh. U. Mate" in ans.answer_text
    assert "Civil Engineering" in ans.answer_text


def test_nonexistent_role_fails_completeness(components):
    """Verify unanswerable/non-existent role returns INSUFFICIENT_EVIDENCE with 0.0 confidence."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("Who is the Vice Chancellor of MITAOE?")
    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)

    assert val.status == "insufficient_evidence"
    assert val.confidence == 0.0

    ans = composer.compose(qc, val)
    assert ans.is_answerable is False
    assert ans.verification_status == "insufficient_evidence"


def test_nonexistent_dean_domain_fails_completeness(components):
    """Verify Dean in non-existent domain returns INSUFFICIENT_EVIDENCE without assigning random Dean."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("Who is the Dean of Aeronautics?")
    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)

    assert val.status == "insufficient_evidence"
    assert val.confidence == 0.0


def test_vision_statement_isolated(components):
    """Verify Vision query returns official Vision statement without Mission conflation."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("What is the Vision of MITAOE?")
    assert qc.requested_intent_category == "institutional_vision"

    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)
    assert val.status == "verified"

    ans = composer.compose(qc, val)
    assert "new age learning center" in ans.answer_text.lower()
    assert "holistic development" in ans.answer_text.lower()
    # Ensure navigation text is not present
    assert "About Us\nMIT Pune" not in ans.answer_text


def test_mission_statement_isolated(components):
    """Verify Mission query returns official Mission statement."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("What is the Mission of MITAOE?")
    assert qc.requested_intent_category == "institutional_mission"

    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)
    assert val.status == "verified"

    ans = composer.compose(qc, val)
    assert "infrastructural facilities" in ans.answer_text.lower()
    assert "lifelong learning" in ans.answer_text.lower()


def test_vision_and_mission_structured(components):
    """Verify combined Vision and Mission query preserves distinct section headers."""
    qu = components["understander"]
    pipeline = components["pipeline"]
    validator = components["validator"]
    composer = components["composer"]

    qc = qu.understand("What are the Vision and Mission of MITAOE?")
    assert qc.requested_intent_category == "vision_and_mission"

    results = pipeline.search(qc.normalized_query, top_k=5)
    val = validator.validate(qc, results)
    assert val.status == "verified"

    ans = composer.compose(qc, val)
    assert "### Institutional Vision" in ans.answer_text
    assert "### Institutional Mission" in ans.answer_text


def test_navigation_boilerplate_stripped(components):
    """Verify that cleaner strips menu boilerplate from text."""
    composer = components["composer"]
    dirty = (
        "About Us\n"
        "MIT Pune\n"
        "MIT Academy of Engineering\n"
        "Leadership\n"
        "Strategic Plan\n"
        "Organizational Chart\n"
        "Dr. Sunil Karad is the Executive President.\n"
        "Visit the serenity of the campus of MIT Academy Of Engineering...\n"
        "admissions@mitaoe.ac.in\n"
        "*Official Source: [MITAOE](https://mitaoe.ac.in)*"
    )
    cleaned = composer._clean_markdown_text(dirty)
    assert "About Us" not in cleaned
    assert "Strategic Plan" not in cleaned
    assert "Visit the serenity" not in cleaned
    assert "Dr. Sunil Karad is the Executive President." in cleaned
