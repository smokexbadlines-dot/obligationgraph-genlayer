# GenLayer Portal submission copy

Category: [Intelligent Contracts](https://portal.genlayer.foundation/contribution-type/52/)

Title: **ObligationGraph — consensus-reviewed obligations with immutable amendment lineage**

Notes / Description (under 1,000 characters):

> ObligationGraph is a standalone GenLayer primitive for two-party commitments. A creator opens a draft; the obligor accepts it, sealing a SHA-256 version. Both parties must approve amendments, preserving immutable lineage. Backward-only dependencies form an acyclic graph and derive BLOCKED or OVERDUE without overwriting adjudicated state. For evidence review, leader and validators independently fetch bounded public HTTPS text, hash the bytes, and classify fulfillment against agreed terms and rubric. Consensus requires the same evidence hash and outcome; only the agreed result updates status. Other contracts can query effective status, versions, and review receipts. The package includes source, seven tests (including five-validator GLSim), documentation, and security assumptions. StudioNet deployment, two-party acceptance, and evidence review finalized with GenVM SUCCESS; the final view returned FULFILLED. The public evidence is a test fixture, not proof of authorship.

Suggested evidence URLs:

1. **GenLayer Explorer Contract** — https://explorer-studio.genlayer.com/address/0x62CFb9c324BEDFBeb3B26A397F9A379f10540b8A — public source under Contract → Code and five finalized transactions.
2. **GenLayer Explorer Contract** — https://explorer-studio.genlayer.com/tx/0x95f4c77e42c140fd349d9c1f4f2bbd16e7cd1246bc60d7be8785ede2322bc94e — finalized evidence review, GenVM SUCCESS.
3. **GitHub Repository** — https://github.com/smokexbadlines-dot/obligationgraph-genlayer — README, tests, setup script, source, and proof images.

General submission checklist:

- [x] Standalone reusable Intelligent Contract with a contract-consumable API.
- [x] State model, authorization, version lineage, and dependency behavior documented.
- [x] GenLayer nondeterministic review and independent validator check present.
- [x] Direct tests and five-validator consensus simulation pass.
- [x] Hosted StudioNet full-consensus deployment and two-party review finalized successfully.
- [x] Public Explorer source and transaction receipts available.
- [x] Publish the documentation and tests at a durable public URL.
- [ ] Paste the prepared copy and evidence URLs into the Portal, complete its CAPTCHA, and submit.

The local package, public repository, and onchain contract have been verified. No Portal contribution has been sent.
