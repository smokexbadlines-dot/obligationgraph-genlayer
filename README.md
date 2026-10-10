# ObligationGraph

ObligationGraph is a standalone GenLayer Intelligent Contract that records two-party commitments and makes their fulfillment state reusable by other contracts. The contract combines deterministic lifecycle rules with GenLayer consensus for interpreting public evidence against written terms and a rubric.

## State model

1. A creator opens a `DRAFT` obligation naming an obligor, terms, a rubric, an HTTPS evidence source prefix, a deadline, and up to 16 existing obligations on which it depends. Dependencies can only point backward, so cycles cannot form.
2. The obligor accepts the draft. Version 1 is sealed as canonical JSON with a SHA-256 digest, and status becomes `ACTIVE`.
3. Either party can propose an amendment to terms, rubric, source prefix, or deadline. The other party must accept it. Every accepted version is stored permanently and links to the preceding version hash.
4. Either party can submit a public UTF-8 evidence URL under the agreed prefix. The leader fetches at most 32 KiB, hashes the body, and asks an LLM for one structured outcome. Validators independently fetch and classify the same evidence. They accept only when both the evidence hash and outcome agree.
5. A consensus-accepted review records its version, outcome, evidence URL, body hash, and transaction time. `INSUFFICIENT` leaves the stored status unchanged. `FULFILLED`, `BREACHED`, and `EXCUSED` are terminal; `PARTIAL` allows further review.

Stored statuses are `DRAFT`, `ACTIVE`, `PARTIAL`, `FULFILLED`, `BREACHED`, and `EXCUSED`. The `get_effective_status` view additionally returns `BLOCKED` when an active obligation depends on an unfulfilled obligation, or `OVERDUE` after the deadline. These two derived statuses do not overwrite an adjudicated result. Only `FULFILLED` satisfies a dependency.

## Contract API

| Method | Caller | Purpose |
| --- | --- | --- |
| `create_obligation(obligor, terms, rubric, evidence_prefix, deadline, dependencies)` | Anyone | Create a draft; returns an ID |
| `accept_obligation(id)` | Obligor | Activate version 1 |
| `propose_amendment(id, terms, rubric, evidence_prefix, deadline)` | Either party | Propose full replacement terms |
| `accept_amendment(id)` | Other party | Seal the next version |
| `reject_amendment(id)` | Either party | Close the pending proposal |
| `review_evidence(id, evidence_url)` | Either party | Run consensus review and record a result |
| `get_obligation(id)` | Anyone | Current record as JSON |
| `get_effective_status(id)` | Anyone | Current or derived status |
| `get_version(id, version)` | Anyone | Immutable version snapshot as JSON |
| `get_review(id, number)` | Anyone | Consensus review record as JSON |
| `get_pending_amendment(id)` | Anyone | Pending proposal as JSON |

For another Intelligent Contract, use `gl.get_contract_at(address).view().get_effective_status(id)` or define a typed interface. A consumer should act on a terminal status only after the review transaction has finalized. GenLayer internal write messages are asynchronous, so this registry intentionally exposes views rather than pushing actions into arbitrary consumer contracts.

## Example lifecycle

Suppose Alice commissions Bob to deliver a report. Alice calls `create_obligation` with Bob's address, a specific acceptance rubric, a stable HTTPS evidence prefix, a future Unix deadline, and `[]` for dependencies. Bob calls `accept_obligation`. Bob then publishes the report at a URL under the prefix and calls `review_evidence`. After consensus and finality, a grant or escrow contract can query `get_effective_status` to decide whether its own payout rules apply.

## Run locally

The contract is in `contracts/ObligationGraph.py`. With Python 3.12 or later:

```bash
pip install -r requirements.txt
python scripts/prepare_test_runner.py
pytest tests -q
genvm-lint check contracts/ObligationGraph.py
```

The seven tests cover authorization, amendment lineage, dependency gating, evidence review, validator disagreement, integer address normalization, storage serialization, and a five-validator GLSim consensus run. The evidence source and LLM are mocked in tests so results are repeatable. `prepare_test_runner.py` downloads the official pinned GenVM bundle and verifies its SHA-256 digest. It is needed because `genlayer-test` 0.29.x requests an asset name that the release does not publish. Deploy through [GenLayer Studio](https://studio.genlayer.com/) or the [GenLayer CLI](https://docs.genlayer.com/developers/intelligent-contracts/deploying/cli-deployment) after testing against the intended network.

## Verified deployment

On 2026-10-09 the packaged source was deployed in hosted GenLayer Studio with **Normal (Full Consensus)** as [contract `0x62CFb9c324BEDFBeb3B26A397F9A379f10540b8A`](https://explorer-studio.genlayer.com/address/0x62CFb9c324BEDFBeb3B26A397F9A379f10540b8A). The deployment transaction was `0xac6c188cc81363c24cc39fa8dd4ed2f28fb52c0694ef89b58e7a2cf81a88b43f`. `create_obligation` transaction `0x0d6de19d9d66c4b75d4deae637e2b5c84c1fb396843391db3d0a775a10d4676f` finalized, and `get_obligation(1)` returned a `DRAFT` record when Studio read from the finalized state. The Studio upload was named `ObligationGraphV2.py` to distinguish it from earlier verification attempts; its contents are the packaged `contracts/ObligationGraph.py`.

The full two-party lifecycle was also tested with a second disposable Studio account. [`create_obligation(2)`](https://explorer-studio.genlayer.com/tx/0x977ae225dfa94c14c166f124c8bad5da5472c38ad77f2a43b05ceb6e726f0430), [`accept_obligation(2)`](https://explorer-studio.genlayer.com/tx/0x21ec1f7c835bc837504a522b05249a2a1930235836c723ec356efd52655a6010), and [`review_evidence(2)`](https://explorer-studio.genlayer.com/tx/0x95f4c77e42c140fd349d9c1f4f2bbd16e7cd1246bc60d7be8785ede2322bc94e) each finalized with GenVM `SUCCESS`. The review used the immutable [GenVM v0.3.0-rc7 license](https://raw.githubusercontent.com/genlayerlabs/genvm/v0.3.0-rc7/LICENSE) as a public test fixture. `get_review(2, 1)` returned `FULFILLED` with evidence hash `9db8336874ca896ae3e88efca8efaf6d058f32730ef0c9fc912de43ef27aed89`, and finalized `get_effective_status(2)` returned `FULFILLED`. This demonstrates consensus classification, not authorship or original publication of the third-party license. See `SUBMISSION.md` for the verification ledger.

On Windows, `genlayer-test` 0.29.2 can raise `PermissionError` while deleting a temporary file whose descriptor remains open. Run direct tests in WSL/Linux, or apply a local test-runner workaround. This is a test tooling issue, not a contract error.

## Security and operating assumptions

- Evidence must be public, stable UTF-8 text accessible to every validator. The source prefix is agreed by both parties; it limits where evidence may be submitted but is not an attestation that the publisher is honest.
- The contract compares an independently fetched SHA-256 body hash and the decision-bearing outcome. If content changes between validator requests, consensus should reject the proposal. Pin evidence at immutable URLs where possible.
- Evidence may contain prompt injection. The prompt marks it as data, bounds its length, and restricts outputs to five labels. The independent validator repeats the actual assessment; it does not merely check JSON shape.
- A semantic result can still be contested through GenLayer's consensus and appeal process. Consumers must wait for finality and decide how they handle rejected or undetermined reviews.
- This registry does not hold escrow, transfer value, or grant legal enforceability. Those effects belong in a consuming contract and the parties' agreement.

The design follows GenLayer's documentation for [storage](https://docs.genlayer.com/developers/intelligent-contracts/features/storage), [non-deterministic equivalence](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle), [web access](https://docs.genlayer.com/developers/intelligent-contracts/features/web-access), and [direct-mode testing](https://docs.genlayer.com/developers/intelligent-contracts/testing).
