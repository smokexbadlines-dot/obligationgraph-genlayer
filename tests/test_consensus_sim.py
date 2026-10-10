"""Five-validator GLSim smoke test for the published contract source.

GLSim runs the Python simulator, so this complements the GenVM direct tests.
"""

from pathlib import Path

from glsim.consensus import run_consensus
from glsim.engine import SimEngine
from glsim.state import StateStore


CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "ObligationGraph.py"
ALICE = "0x" + "11" * 20
BOB = "0x" + "22" * 20
EVIDENCE_URL = "https://evidence.example.org/records/report.txt"


def test_five_validators_accept_the_same_evidence_assessment():
    engine = SimEngine(StateStore(seed="obligationgraph-consensus"))
    engine.activate()
    try:
        address, _ = engine.deploy(str(CONTRACT), [], {}, ALICE)
        obligation_id = engine.call_method(
            address,
            "create_obligation",
            [
                BOB,
                "Deliver a report covering milestones one, two, and three.",
                "A dated report confirms all three milestones complete.",
                "https://evidence.example.org/records/",
                4102444800,
                [],
            ],
            sender=ALICE,
        )
        engine.call_method(address, "accept_obligation", [obligation_id], sender=BOB)
        engine.vm.mock_web(
            r"evidence\.example\.org/records/report\.txt",
            {"status": 200, "body": "Dated report: milestones one, two, and three complete."},
        )
        engine.vm.mock_llm(
            r"You are assessing a GenLayer obligation", '{"outcome":"FULFILLED"}'
        )

        def execute():
            outcome = engine.call_method(
                address, "review_evidence", [obligation_id, EVIDENCE_URL], sender=BOB
            )
            return outcome, b""

        consensus = run_consensus(engine, execute, 5, 3)
        assert consensus.error is None
        assert consensus.result == "FULFILLED"
        assert consensus.votes == ["agree"] * 5
        assert engine.call_method(address, "get_effective_status", [obligation_id]) == "FULFILLED"
    finally:
        engine.deactivate()
