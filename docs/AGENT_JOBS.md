# Background agent jobs

Milestone 8 adds asynchronous execution for central-bank analysis, business/bank credit, and supplier procurement. These endpoints accept the same typed request bodies as the existing synchronous workflow endpoints and return **HTTP 202 with a job ID**. The existing synchronous endpoints still work.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/worlds/{id}/agent-jobs` | Queue central-bank analysis; accepts `AgentRunRequest`. |
| POST | `/api/worlds/{id}/businesses/{business_id}/credit-jobs` | Queue credit negotiation; accepts `CreditRunRequest`. |
| POST | `/api/worlds/{id}/businesses/{buyer_id}/procurement-jobs` | Queue supplier negotiation; accepts `ProcurementRequest`. |
| GET | `/api/worlds/{id}/agent-jobs?limit=50` | Most recent jobs across all three workflows; limit 1–100. |
| GET | `/api/agent-jobs/{job_id}` | Job lifecycle and the linked workflow report. |
| POST | `/api/agent-jobs/{job_id}/cancel` | Cancel a queued job; repeating cancellation is safe. |

The job has `job_id`, `simulation_id`, `kind`, optional `actor_id`, the validated request, `status`, Unix-second `created_at`/`updated_at`, optional `error`, `run_id`, `report_url`, and `report_status`. Status transitions are `queued → running → completed/failed`, or `queued → cancelled`. Report fields can be null until execution creates the workflow report. Provider setup failures can fail before a report exists.

**Job completion means the workflow returned successfully.** A completed credit job may have a declined or not-requested report. A completed procurement job may have declined or ready terms. Always inspect `report_status` and the report's decision/settlement fields. HTTP 202 only acknowledges the job; it does not mean an offer or settlement succeeded.

## Frontend flow

Pause the selected world before starting a workflow that must later settle against that snapshot. A queued job observes the world **when execution starts**, rather than when the request is accepted. It does not pause the world automatically. Existing snapshot validation still rejects settlement if the world subsequently changes.

```js
const base = 'http://127.0.0.1:8000';
const response = await fetch(`${base}/api/worlds/${id}/agent-jobs`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    request_id: crypto.randomUUID(), mode: 'demo',
    budget_cap_cents: 1000000, ticks: 12, max_experiments: 2
  })
});
if (!response.ok) throw new Error(`Job submission failed: ${response.status}`);
const accepted = await response.json();
// Save accepted.job_id so a reload/reconnect can recover progress.
const job = await fetch(`${base}/api/agent-jobs/${accepted.job_id}`).then(r => r.json());
if (job.report_url) {
  const report = await fetch(`${base}${job.report_url}`).then(r => r.json());
  renderAgentTrace(report.trace);
}
```

Poll the job and its report about once per second while queued/running, then stop polling the job on a terminal status. Keep a queued indicator separate from the workflow's public tool trace. `report_url` points to the existing report endpoint, so its inspector and apply/settle actions stay the same. Financial settlement events still appear on [the economic SSE stream](./PLAYBACK.md); job status and model traces use polling.

Default mode remains `live`. Use `mode: "demo"` explicitly for offline demos. Check `/api/agents/status` before live submission; missing credentials cause a failed job rather than a successful live run. No fallback substitutes demo output for live inference.

## Retries, settlement, and cancellation

Reuse the same request ID and identical payload after an uncertain submission: the server returns the same job without enqueuing another copy. Uniqueness is scoped to world, workflow kind, and business/buyer where applicable. Different payloads under the same key return 409. Terminal jobs are not restarted by resubmission; use a new request ID for a new attempt after inspecting any existing result.

The job passes that request ID to the existing workflow, so synchronous and asynchronous callers share the workflow's retry behavior. Avoid starting both forms with the same key concurrently: the existing claim can reject the duplicate while its report is still running. The linked report remains inspectable.

Credit and procurement default to `auto_settle: false`. Explicitly setting it true authorizes the existing guarded automatic settlement. The queue adds no new spending authority. Central-bank recommendations still require a separate `/api/agent-runs/{run_id}/apply` call. Completed offers use the existing credit/procurement settle endpoints and financial transaction IDs.

Cancellation is supported **only before execution claims a job**. If a worker wins the claim race, cancellation returns 409. Running, completed, or failed work cannot be cancelled through this endpoint because financial actions may already have committed. Closing a browser tab does not cancel a job. Cancelled jobs retain their request keys and history.

## Workers, restart, and limits

Normal [backend startup](../README.md) starts two job workers alongside playback. SQLite limits healthy workers to two running jobs across API processes, and the shared queue permits at most 32 queued/running jobs. Saturation returns 429 with `Retry-After: 5`; retry the same request after capacity becomes available. There are no new dependencies or environment variables.

Claims are atomic and FIFO. Workers renew a 60-second lease every five seconds while inference runs outside the event loop. Queued jobs survive restart. An expired running lease becomes a failed job during a worker's next claim pass; its work is **never automatically replayed**. Existing snapshots, traces, comparisons, and receipts remain accessible. Shutdown stops claiming new work and waits for already-running workflows to finish; bounded model calls can make this take time.

A heartbeat timeout is an interruption signal, not cancellation of an external call. A severely stalled worker can still return later. Inspect the linked workflow and any settlement before making a new request; the queue does not promise that a failed job means no funds moved. A report may remain marked running after a process crash. Existing exactly-once financial receipts and snapshot checks remain the source of truth.

The queue schedules explicitly requested workflows. Continuous autonomous agent activity, live-provider verification, and external settlement remain future work. This is a local development service without authentication; the job ID does not provide authorization.
