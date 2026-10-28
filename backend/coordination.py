"""Persisted public handoffs and a bounded independent reviewer. No settlement tools."""
import json
import time
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from backend.provider import NebiusModel, ProviderError
from backend.ledger import LedgerError


def activity(report, save, actor, message, *, tool=None, trace_sequence=None, target=None, persist=True):
    if not report['request'].get('agent_review'):
        return
    events = report.setdefault('activity', [])
    events.append({'sequence': len(events) + 1, 'at': time.time(), 'actor': actor,
                   'target': target, 'message': message, 'tool': tool, 'trace_sequence': trace_sequence})
    report['active_agent'] = actor
    if persist:
        save(report)


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    passed: StrictBool
    rationale: str = Field(min_length=1, max_length=1200)


REVIEW_TOOL = [{'type': 'function', 'function': {
    'name': 'submit_review', 'description': 'Return an independent evidence-based review. This cannot move funds.',
    'parameters': ReviewDecision.model_json_schema()}}]


def review_checks(report, source, kind):
    source.audit()  # raises on unbalanced books or mismatched counterparties
    checks = [{'name': 'Ledger and counterparties reconcile', 'passed': True},
              {'name': 'Every tool response has a recorded sequence', 'passed':
               [t['sequence'] for t in report['trace']] == list(range(1, len(report['trace']) + 1))}]
    accepted = [t for t in report['trace'] if t['status'] == 'accepted']
    if kind == 'central_bank':
        recommendation = report.get('recommendation')
        comparisons = [t['result'] for t in accepted if t['tool'] == 'compare_interventions']
        match = next((c for c in comparisons if recommendation and c['fork_id'] == recommendation['fork_id']), None)
        branch = next((b for b in match['branches'] if b['strategy'] == recommendation['strategy']), None) if match else None
        checks.append({'name': 'Recommendation matches a tested policy and its outcome', 'passed': bool(
            branch and branch['metrics'] == recommendation['metrics'] and
            recommendation['amount_cents'] == (0 if recommendation['strategy'] == 'no_intervention' else match['request']['budget_cents']))})
    elif kind == 'credit':
        proposal, decision = report.get('proposal'), report.get('decision')
        assessments = [t['result'] for t in accepted if t['tool'] == 'assess_credit']
        valid = not proposal or bool(decision and (not decision['approved'] or any(
            a.get('eligible') and a.get('amount_cents') == decision['amount_cents'] for a in assessments)))
        checks.append({'name': 'Bank decision uses assessed principal within the business request', 'passed': bool(
            valid and (not decision or not decision['approved'] or decision['amount_cents'] <= proposal['amount_cents']))})
        if report.get('business_accepted'):
            checks.append({'name': 'Business explicitly accepted the recorded bank offer', 'passed': any(
                t['tool'] == 'accept_offer' and t['result'].get('amount_cents') == decision['amount_cents'] for t in accepted)})
    else:
        selected = report.get('selected_offer')
        checks.append({'name': 'Buyer selection matches an actual supplier offer and spending cap', 'passed':
                       not selected or (selected in report['offers'] and selected['total_cents'] <= report['request']['max_total_cents'])})
    return checks


def review_report(store, report, source, kind, save):
    if not report['request'].get('agent_review'):
        return report
    previous = report.get('active_agent')
    if previous:
        activity(report, save, previous, 'Sent the recorded exchanges and proposed result for independent review.', target='supervisor', trace_sequence=len(report['trace']))
    activity(report, save, 'supervisor', 'Received the recorded handoffs and proposed result. Checking evidence and financial constraints.')
    report['supervision'] = {'status': 'running', 'checks': [], 'rationale': '', 'provider': None, 'model': None}
    save(report)
    try:
        checks = review_checks(report, source, kind)
        report['supervision']['checks'] = checks
        evidence = {'workflow': kind, 'checks': checks, 'source_tick': report['source_tick'],
                    'trace': report['trace'], 'proposal': report.get('proposal'), 'decision': report.get('decision'),
                    'recommendation': report.get('recommendation'), 'selected_offer': report.get('selected_offer'),
                    'business_accepted': report.get('business_accepted'), 'approval_reasons': report.get('approval_reasons', [])}
        if report['request']['mode'] == 'demo':
            passed = all(c['passed'] for c in checks)
            rationale = 'Deterministic review: checked the recorded exchanges and financial constraints. Human approval and settlement remain separate.'
            provider, model_name = 'deterministic_demo', 'demo-supervisor-v1'
        else:
            model = NebiusModel()
            report['supervision'].update(provider=model.provider, model=model.model)
            save(report)
            response = model.complete([
                {'role': 'system', 'content': 'You are an independent financial workflow supervisor. Review the other agents public tool records for unsupported claims, mismatched handoffs and inconsistent decisions. Do not repeat their conclusion without checking it. A corrected rejected tool call is allowed. Human approval requirements are not review failures and cannot be waived. You have no settlement or modification tools. Return submit_review once, with a concise public explanation. Use simple language in at most three short sentences (70 words). Public support is gross disbursement; it does not estimate national debt or net fiscal loss. Never claim to guarantee correctness. A failed deterministic check must produce passed=false.'},
                {'role': 'user', 'content': json.dumps(evidence)}], REVIEW_TOOL)
            calls = response.get('tool_calls', [])
            if not isinstance(calls, list) or len(calls) != 1 or not isinstance(calls[0], dict) or not isinstance(calls[0].get('function'), dict) or calls[0]['function'].get('name') != 'submit_review':
                raise ProviderError('Supervisor returned an invalid review tool call')
            verdict = ReviewDecision.model_validate_json(calls[0]['function']['arguments'])
            passed = verdict.passed and all(c['passed'] for c in checks)
            rationale, provider, model_name = verdict.rationale, model.provider, model.model
        report['supervision'].update(status='passed' if passed else 'blocked', checks=checks,
                                     rationale=rationale, provider=provider, model=model_name)
        activity(report, save, 'supervisor', rationale, target='human', persist=False)
    except (ProviderError, LedgerError, ValueError, KeyError, TypeError) as error:
        report['supervision'].update(status='failed', rationale=str(error) if isinstance(error, (ProviderError, LedgerError)) else 'Supervisor could not validate its evidence or response.')
        activity(report, save, 'supervisor', report['supervision']['rationale'], target='human', persist=False)
    # Publish the passed gate once, after the final activity record. No later
    # save may overwrite a concurrent human approval or settlement.
    report['active_agent'] = None
    save(report)
    return report


def require_review(report):
    if report['request'].get('agent_review') and (report.get('supervision') or {}).get('status') != 'passed':
        raise LedgerError('Independent supervisor review has not passed. Start a new review before applying or settling.')
