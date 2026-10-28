import pytest

from backend.engine import Economy
from backend.store import Store
from backend.forks import snapshot_hash
from backend.ledger import LedgerError
from backend.provider import ProviderNotConfigured
from backend.fetch_agents.service import EconomyAgentService
from backend.fetch_agents import protocols as p


@pytest.fixture
def saved(tmp_path):
    store=Store(tmp_path/'integration.sqlite3')
    store.create(Economy.create('saved',seed=42,scenario='credit_crunch'))
    return store


def test_real_crisis_metrics_are_computed_and_source_is_unchanged(saved):
    before=snapshot_hash(saved.get('saved').state)
    result=EconomyAgentService(saved).handle(p.CrisisStressInquiry(world_id='saved',target_bank_id='bank_1'))
    assert len(result.branches)==3 and result.funds_applied is False
    # Independently advance matching engine branches rather than freezing an
    # employment number from the previous settlement model.
    for summary in result.branches:
        branch=Economy(saved.get('saved').state)
        branch.shock('expected-loss','bank_1',4000)
        if summary.strategy!='no_intervention':
            branch.intervene('expected-support',summary.strategy,1_000_000,
                             'bank_1' if summary.strategy=='bank_lending' else None)
        branch.step(12)
        metrics=branch.metrics()
        assert summary.employed_households==metrics['employed_households']
        assert summary.business_defaults==metrics['business_defaults']
        assert summary.insolvent_banks==metrics['insolvent_banks']
        assert summary.public_support_disbursed_cents==metrics['public_support_disbursed_cents']
        assert branch.audit()['balanced']
    assert snapshot_hash(saved.get('saved').state)==before


def test_payroll_and_bank_ignore_caller_asserted_shortfall(saved):
    service=EconomyAgentService(saved)
    facts=service.handle(p.PayrollAuditInquiry(world_id='saved',business_id='business_1'))
    assert facts.shortfall_cents==0
    result=service.handle(p.CreditApplicationMessage(world_id='saved',bank_id='bank_1',borrower_id='business_1',requested_cents=100000,payroll_shortfall_cents=100000))
    assert result.approved is False and result.approved_cents==0


def test_zero_duration_loss_stays_zero_and_does_not_touch_portfolio(saved):
    before=snapshot_hash(saved.get('saved').state)
    result=EconomyAgentService(saved).handle(p.DebtShockEstimateRequest(world_id='saved',bank_id='bank_1',yield_increase_bps=0))
    assert result.estimated_loss_bps==result.estimated_loss_cents==0
    assert snapshot_hash(saved.get('saved').state)==before


def test_missing_store_and_sources_do_not_fabricate_observations(saved,monkeypatch):
    with pytest.raises(ProviderNotConfigured):
        EconomyAgentService(None).handle(p.WelfareAuditRequest(world_id='saved'))
    from backend import apify_collection
    monkeypatch.setattr(apify_collection,'latest_data',lambda:(None,None))
    with pytest.raises(ProviderNotConfigured):
        EconomyAgentService(saved).handle(p.WageBenchmarkQuery())
    monkeypatch.setattr(apify_collection,'latest_data',lambda:({'daily_wage_cents':[10000],
        'sources':[{'category':'wages','source_url':'https://example.test','observations':[{'unit':'usd_year','kind':'salary'}]}]},0))
    with pytest.raises(LedgerError,match='statutory'):
        EconomyAgentService(saved).handle(p.WageBenchmarkQuery())


def test_no_assumed_demand_multiplier_or_network_settlement(saved):
    service=EconomyAgentService(saved)
    with pytest.raises(LedgerError):
        service.handle(p.CashStimulusImpactQuery(world_id='saved'))
    with pytest.raises(LedgerError):
        service.handle(p.CreditAcceptanceNotification(world_id='saved',business_id='business_1',bank_id='bank_1',accepted_cents=100000,terms_accepted=True,rationale='caller claims approval'))


def test_nested_reader_cannot_commit_an_outer_transaction(saved):
    with saved.connection() as conn:
        conn.execute('CREATE TABLE rollback_probe (value INTEGER)')
    with pytest.raises(RuntimeError):
        with saved.connection() as conn:
            conn.execute('INSERT INTO rollback_probe VALUES (1)')
            saved.get('saved')
            raise RuntimeError('Abort the financial operation')
    with saved.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM rollback_probe').fetchone()[0]==0


def test_play_race_cannot_bypass_paused_step(saved,monkeypatch):
    original=saved.mutate
    def interleaved(sid,operation):
        saved.control_playback(sid,'running',now=0)
        return original(sid,operation)
    monkeypatch.setattr(saved,'mutate',interleaved)
    with pytest.raises(LedgerError,match='Pause'):
        saved.step_paused('saved',1)
    assert saved.get('saved').state['tick']==0


def test_audit_uses_saved_entity_count_and_balances(saved):
    report=EconomyAgentService(saved).handle(p.InvarianceAuditRequest(world_id='saved'))
    assert report.is_balanced and report.invariant_delta_cents==0
    assert report.entities_audited==len(saved.get('saved').state['entities'])
