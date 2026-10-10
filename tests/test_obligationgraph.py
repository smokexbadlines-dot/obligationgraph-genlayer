import json

CONTRACT = "contracts/ObligationGraph.py"
EVIDENCE_PREFIX = "https://evidence.example.org/records/"
DEADLINE = 4102444800  # 2100-01-01 UTC


def create(contract, vm, creator, obligor, dependencies=None):
    vm.sender = creator
    return contract.create_obligation(
        obligor,
        "Deliver a published report covering all three milestones.",
        "A dated report must identify milestones 1, 2, and 3 as complete.",
        EVIDENCE_PREFIX,
        DEADLINE,
        dependencies or [],
    )


def test_integer_address_input_is_normalized(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    oid = create(contract, direct_vm, direct_alice, int.from_bytes(direct_bob, "big"))
    direct_vm.sender = direct_bob
    contract.accept_obligation(oid)
    assert json.loads(contract.get_obligation(oid))["obligor"].lower() == "0x" + direct_bob.hex()


def test_acceptance_and_immutable_versions(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.check_pickling = True
    contract = direct_deploy(CONTRACT)
    oid = create(contract, direct_vm, direct_alice, direct_bob)
    assert json.loads(contract.get_obligation(oid))["status"] == "DRAFT"

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Only the obligor"):
        contract.accept_obligation(oid)
    direct_vm.sender = direct_bob
    contract.accept_obligation(oid)
    original = json.loads(contract.get_version(oid, 1))
    assert original["version"] == 1
    original_hash = json.loads(contract.get_obligation(oid))["version_hash"]
    assert len(original_hash) == 64

    direct_vm.sender = direct_alice
    contract.propose_amendment(
        oid, "Deliver a published report covering four milestones.",
        "A dated report identifies milestones 1 through 4 as complete.",
        EVIDENCE_PREFIX, DEADLINE,
    )
    with direct_vm.expect_revert("other party"):
        contract.accept_amendment(oid)
    direct_vm.sender = direct_bob
    contract.accept_amendment(oid)
    amended = json.loads(contract.get_version(oid, 2))
    assert amended["previous_hash"] == original_hash
    assert json.loads(contract.get_obligation(oid))["previous_hash"] == original_hash
    assert json.loads(contract.get_version(oid, 1)) == original
    assert amended["terms"].endswith("four milestones.")


def test_dependencies_and_consensus_review(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    first = create(contract, direct_vm, direct_alice, direct_bob)
    second = create(contract, direct_vm, direct_alice, direct_bob, [first])
    direct_vm.sender = direct_bob
    contract.accept_obligation(first)
    contract.accept_obligation(second)
    assert contract.get_effective_status(second) == "BLOCKED"
    with direct_vm.expect_revert("Dependencies"):
        contract.review_evidence(second, EVIDENCE_PREFIX + "two.txt")

    direct_vm.mock_web(
        r"evidence\.example\.org/records/one\.txt",
        {"status": 200, "body": "Dated report: milestones 1, 2, and 3 complete."},
    )
    direct_vm.mock_llm(r"You are assessing a GenLayer obligation", '{"outcome":"FULFILLED"}')
    assert contract.review_evidence(first, EVIDENCE_PREFIX + "one.txt") == "FULFILLED"
    assert contract.get_effective_status(second) == "ACTIVE"
    review = json.loads(contract.get_review(first, 1))
    assert review["outcome"] == "FULFILLED"
    assert len(review["evidence_hash"]) == 64
    assert direct_vm.run_validator() is True


def test_validator_rejects_different_semantic_outcome(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT)
    oid = create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    contract.accept_obligation(oid)
    direct_vm.mock_web(
        r"evidence\.example\.org/records/one\.txt",
        {"status": 200, "body": "Dated report: milestones 1, 2, and 3 complete."},
    )
    direct_vm.mock_llm(r"You are assessing a GenLayer obligation", '{"outcome":"FULFILLED"}')
    contract.review_evidence(oid, EVIDENCE_PREFIX + "one.txt")
    direct_vm.clear_mocks()
    direct_vm.mock_web(
        r"evidence\.example\.org/records/one\.txt",
        {"status": 200, "body": "Dated report: milestones 1, 2, and 3 complete."},
    )
    direct_vm.mock_llm(r"You are assessing a GenLayer obligation", '{"outcome":"PARTIAL"}')
    assert direct_vm.run_validator() is False


def test_untrusted_evidence_url_is_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    oid = create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    contract.accept_obligation(oid)
    with direct_vm.expect_revert("outside the agreed source prefix"):
        contract.review_evidence(oid, "https://elsewhere.example.org/report.txt")


def test_insufficient_review_preserves_state_and_changed_evidence_is_rejected(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT)
    oid = create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    contract.accept_obligation(oid)
    direct_vm.mock_web(
        r"evidence\.example\.org/records/one\.txt",
        {"status": 200, "body": "Report is pending."},
    )
    direct_vm.mock_llm(r"You are assessing a GenLayer obligation", '{"outcome":"INSUFFICIENT"}')
    assert contract.review_evidence(oid, EVIDENCE_PREFIX + "one.txt") == "INSUFFICIENT"
    assert contract.get_effective_status(oid) == "ACTIVE"
    assert json.loads(contract.get_obligation(oid))["review_count"] == 1

    direct_vm.clear_mocks()
    direct_vm.mock_web(
        r"evidence\.example\.org/records/one\.txt",
        {"status": 200, "body": "Report was edited after submission."},
    )
    direct_vm.mock_llm(r"You are assessing a GenLayer obligation", '{"outcome":"INSUFFICIENT"}')
    assert direct_vm.run_validator() is False
