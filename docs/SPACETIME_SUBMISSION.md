# SpacetimeDB: shared economy control room

The [official prize brief](https://hive.hackberkeley.org/prizes) asks for meaningful core real-time use, including shared simulations, live financial dashboards and coordination. SpacetimeDB is now the authoritative backend for collaborative proposals, independent-identity review, presence and execution receipts. Its real subscriptions distribute those records and committed financial events directly to clients. SQLite remains the accounting engine; this is not a complete ledger migration.

## Demonstrate

1. Start the local database, publish the module and start the API/UI using [the integration setup](./SPONSOR_INTEGRATIONS.md). Keep existing keys and use `--delete-data=never`.
2. Open a paused world. Expand **Data, fraud & shared events**, then **Open shared control room**. Enter a participant name and join.
3. Copy the room URL into another browser profile or private window. Join as another participant. Both views show presence through SpacetimeDB.
4. Propose a 40% hypothetical bank loss. The proposer cannot approve it. The second identity approves; no financial change occurs yet.
5. Execute the approved proposal. Both clients receive the receipt and real financial event. Replaying its execution cannot apply a second loss.
6. Propose again, approve, then advance the world before execution. The engine rejects the stale snapshot. Refresh the proposal snapshot and create a new proposal if desired.

The share URL selects an existing synthetic world; it does not clone one. The second browser needs network access to both the API/UI and the configured SpacetimeDB host. Localhost links are for a same-machine demo, not remote hosting.

## Verified evidence

`node scripts/qa-control-room.mjs` exercises two independent Chrome contexts against the real local module. It verifies presence, subscriptions, review without settlement, unauthorized/pending execution rejection, exactly-once execution, stale state rejection, balanced audit, persisted receipts after reload, server-side rejection of self-approval/forged context/forged receipts/invalid banks and no browser exceptions. Evidence and screenshots are ignored under `artifacts/control-room/`.

`tests/test_control_room.py` additionally exercises a lost SpacetimeDB acknowledgement after the financial commit: retry finds the existing ledger receipt, updates the shared status and cannot repeat the loss. Generated SDK bindings live in `apps/web/src/data/spacetime/`; regenerate them after module schema changes:

```powershell
.\data\spacetime-bin\spacetimedb-cli.exe generate --lang typescript --module-path spacetimedb --out-dir apps/web/src/data/spacetime --yes
```

## Submission text

Economy God Mode uses SpacetimeDB to coordinate a shared financial simulation. Participants watch live events, propose hypothetical bank shocks, and review each other's proposals in a persistent control room. Server-side reducers bind proposals to the published world snapshot, require a different identity for review, and reserve execution receipt updates to the publishing backend. Direct subscriptions synchronize presence, proposals, approvals and receipts across browsers. The accounting engine separately revalidates the snapshot under a transaction lock and applies an approved shock at most once. A two-browser demonstration shows approval without mutation, synchronized execution, safe replay and rejection when the world has changed.

## Limits

These are anonymous browser identities, not verified people or production authorization roles. Opening a second browser can create a second identity; do not claim a regulated two-person control. The local API remains unauthenticated. Real public reference observations, hypothetical shock assumptions and synthetic financial state remain separate. Public deployment and event submission have not been performed for this milestone.
