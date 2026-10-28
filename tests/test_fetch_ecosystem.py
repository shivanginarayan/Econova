"""Unit and integration tests for the 10-Agent Fetch.ai Economic Ecosystem."""

import pytest
from backend.fetch_agents.protocols import (
    BranchMetricSummary,
    CashStimulusImpactQuery,
    CashStimulusImpactReport,
    CounterOfferReviewMessage,
    CreditApplicationMessage,
    CrisisStressInquiry,
    DebtShockEstimateRequest,
    DebtShockEstimateResponse,
    FraudAuditReport,
    InterbankExposureAuditResponse,
    InvarianceAuditReport,
    MenuPriceBasketResponse,
    NettingSettlementProposal,
    PayrollAuditInquiry,
    PayrollGapReport,
    PolicyRescueReport,
    ProcurementBiddingReport,
    ProcurementInquiry,
    QuoteRequestMessage,
    QuoteResponseMessage,
    TreasuryDataResponse,
    UnderwritingDecisionMessage,
    WageBenchmarkResponse,
    WelfareAuditResponse,
)
from backend.fetch_agents.agents import AGENT_FACTORIES, default_seed


def test_agent_factories_registry():
    assert len(AGENT_FACTORIES) == 10
    expected_agents = {
        "central_bank",
        "commercial_bank",
        "corporate_borrower",
        "procurement_buyer",
        "supplier_quotation",
        "treasury_macro",
        "apify_wage_oracle",
        "clearinghouse_settlement",
        "household_welfare",
        "auditor_inspector",
    }
    assert set(AGENT_FACTORIES.keys()) == expected_agents


def test_stable_seeds(monkeypatch):
    monkeypatch.setenv('FETCH_AGENT_SEED', 'unit-test-only-private-seed')
    seed1 = default_seed("central_bank")
    seed2 = default_seed("central_bank")
    seed3 = default_seed("commercial_bank")
    assert seed1 == seed2
    assert seed1 != seed3
    assert len(seed1) == 64


def test_central_bank_models():
    inquiry = CrisisStressInquiry(world_id="w1", target_bank_id="bank_1", loss_bps=4000)
    assert inquiry.world_id == "w1"
    assert inquiry.loss_bps == 4000

    report = PolicyRescueReport(
        world_id="w1",
        target_bank_id="bank_1",
        recommended_strategy="bank_lending",
        branches=[
            BranchMetricSummary(
                strategy="bank_lending",
                employed_households=38,
                business_defaults=1,
                insolvent_banks=0,
                public_support_disbursed_cents=1_000_000,
            )
        ],
        rationale="Preserves employment and liquidity",
        public_disbursement_cents=1_000_000,
    )
    assert report.recommended_strategy == "bank_lending"
    assert report.branches[0].employed_households == 38


def test_commercial_bank_models():
    msg = CreditApplicationMessage(
        world_id="w1",
        bank_id="bank_1",
        borrower_id="business_1",
        requested_cents=100_000,
        payroll_shortfall_cents=100_000,
    )
    decision = UnderwritingDecisionMessage(
        world_id="w1",
        bank_id="bank_1",
        borrower_id="business_1",
        approved=True,
        approved_cents=100_000,
        capital_ratio_post_issuance=0.12,
        rationale="Approved within capital buffer",
    )
    assert decision.approved is True
    assert decision.approved_cents == 100_000


def test_corporate_borrower_models():
    inquiry = PayrollAuditInquiry(world_id="w1", business_id="business_1")
    report = PayrollGapReport(
        world_id="w1",
        business_id="business_1",
        deposits_cents=50_000,
        payroll_due_cents=150_000,
        shortfall_cents=100_000,
        needs_financing=True,
        status="active",
    )
    assert report.shortfall_cents == 100_000
    assert report.needs_financing is True


def test_procurement_and_supplier_models():
    inq = ProcurementInquiry(world_id="w1", buyer_id="business_1", target_units=5)
    quote = QuoteResponseMessage(
        world_id="w1",
        supplier_id="business_2",
        unit_price_cents=1200,
        down_payment_bps=5000,
        due_in_ticks=3,
        fulfillable=True,
        total_cents=6000,
    )
    counter = CounterOfferReviewMessage(
        world_id="w1",
        supplier_id="business_2",
        buyer_id="business_1",
        proposed_unit_price_cents=1080,
        proposed_down_payment_bps=3000,
        proposed_due_ticks=5,
        accepted=True,
        final_unit_price_cents=1080,
        rationale="Accepted",
    )
    bidding = ProcurementBiddingReport(
        world_id="w1",
        buyer_id="business_1",
        best_supplier_id="business_2",
        unit_price_cents=1080,
        down_payment_cents=1620,
        total_cents=5400,
        selected=True,
        rationale="Budget compliant",
    )
    assert quote.fulfillable is True
    assert counter.accepted is True
    assert bidding.selected is True


def test_treasury_macro_models():
    data = TreasuryDataResponse(
        latest_record_date="2026-10-24",
        total_debt_cents=35_000_000_000_000_00,
        source_api="US Treasury Debt to the Penny",
        retrieved_at="2026-10-25T00:00:00Z",
    )
    shock = DebtShockEstimateResponse(
        world_id="w1",
        bank_id="bank_1",
        estimated_loss_bps=500,
        estimated_loss_cents=500_000,
        duration_formula="0.5 * 5.0y * 200 bps = 500 bps",
        story_summary="Debt shock bond write-down",
    )
    assert data.total_debt_cents > 0
    assert shock.estimated_loss_bps == 500


def test_apify_wage_oracle_models():
    wage = WageBenchmarkResponse(
        category="wages",
        statutory_min_wage_usd_hour=19.61,
        daily_wage_cents=15688,
        source_url="https://www.sf.gov",
        legal_effective_date="2026-07-01",
    )
    menu = MenuPriceBasketResponse(
        category="prices",
        sample_count=29,
        average_drink_cents=588,
        min_cents=375,
        max_cents=850,
        source_url="https://www.cafeseventy8.com/",
    )
    assert wage.statutory_min_wage_usd_hour == 19.61
    assert menu.sample_count == 29


def test_clearinghouse_settlement_models():
    exp = InterbankExposureAuditResponse(
        world_id="w1",
        total_interbank_debt_cents=4_500_000,
        bilateral_pairs_count=4,
        max_single_exposure_cents=1_800_000,
        contagion_risk_score="MODERATE",
        recommendation="Normal reserve coverage",
    )
    netting = NettingSettlementProposal(
        world_id="w1",
        total_gross_cents=1_000_000,
        total_netted_cents=450_000,
        netting_efficiency_percent=55.0,
        liquidity_saved_cents=550_000,
    )
    assert exp.contagion_risk_score == "MODERATE"
    assert netting.netting_efficiency_percent == 55.0


def test_household_welfare_models():
    welfare = WelfareAuditResponse(
        world_id="w1",
        total_households=40,
        employed_count=35,
        employment_rate_percent=87.5,
        median_balance_cents=125_000,
        min_balance_cents=45_000,
        max_balance_cents=380_000,
        gini_estimate=0.28,
        welfare_status="HEALTHY",
    )
    stim = CashStimulusImpactReport(
        world_id="w1",
        stimulus_budget_cents=1_000_000,
        per_household_transfer_cents=25_000,
        projected_employment_gain=4,
        consumption_boost_estimate_cents=1_380_000,
        velocity_multiplier_estimate=1.38,
    )
    assert welfare.employment_rate_percent == 87.5
    assert stim.consumption_boost_estimate_cents == 1_380_000


def test_auditor_inspector_models():
    audit = InvarianceAuditReport(
        world_id="w1",
        is_balanced=True,
        total_assets_cents=150_000_000,
        total_liabilities_cents=110_000_000,
        total_equity_cents=40_000_000,
        invariant_delta_cents=0,
        transactions_count=142,
        entities_audited=55,
        audit_verdict="PASSED_INVARIANCE_CONFIRMED",
    )
    fraud = FraudAuditReport(
        world_id="w1",
        total_screenings=1,
        blocked_count=1,
        verified_count=0,
        compliance_status="COMPLIANT_ZERO_TOLERANCE",
    )
    assert audit.is_balanced is True
    assert audit.invariant_delta_cents == 0
    assert fraud.blocked_count == 1
