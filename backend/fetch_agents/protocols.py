"""Fetch.ai uagents protocols and message models for the 10-Agent Economic Ecosystem."""

from typing import Any, List, Optional
try:
    from uagents import Model, Protocol
except ImportError:
    from pydantic import BaseModel as Model  # type: ignore
    Protocol = object  # type: ignore


# ---------------------------------------------------------------------------
# 1. Central Bank Macro-Prudential Protocols & Models
# ---------------------------------------------------------------------------
class CrisisStressInquiry(Model):
    world_id: str
    target_bank_id: str
    loss_bps: int = 4000
    ticks: int = 12
    budget_cents: int = 1_000_000


class BranchMetricSummary(Model):
    strategy: str
    employed_households: int
    business_defaults: int
    insolvent_banks: int
    public_support_disbursed_cents: int


class PolicyRescueReport(Model):
    world_id: str
    target_bank_id: str
    recommended_strategy: str
    branches: List[BranchMetricSummary]
    rationale: str
    public_disbursement_cents: int
    funds_applied: bool = False


# ---------------------------------------------------------------------------
# 2. Commercial Bank Underwriting Protocols & Models
# ---------------------------------------------------------------------------
class CreditApplicationMessage(Model):
    world_id: str
    bank_id: str
    borrower_id: str
    requested_cents: int
    payroll_shortfall_cents: int
    stated_purpose: str = "payroll_financing"


class UnderwritingDecisionMessage(Model):
    world_id: str
    bank_id: str
    borrower_id: str
    approved: bool
    approved_cents: int
    counteroffer: bool = False
    capital_ratio_post_issuance: float
    rationale: str


# ---------------------------------------------------------------------------
# 3. Corporate Borrower Liquidity Protocols & Models
# ---------------------------------------------------------------------------
class PayrollAuditInquiry(Model):
    world_id: str
    business_id: str


class PayrollGapReport(Model):
    world_id: str
    business_id: str
    deposits_cents: int
    payroll_due_cents: int
    shortfall_cents: int
    needs_financing: bool
    status: str


class CreditAcceptanceNotification(Model):
    world_id: str
    business_id: str
    bank_id: str
    accepted_cents: int
    terms_accepted: bool
    rationale: str


# ---------------------------------------------------------------------------
# 4. Procurement Buyer Supply Chain Protocols & Models
# ---------------------------------------------------------------------------
class ProcurementInquiry(Model):
    world_id: str
    buyer_id: str
    target_units: int = 5
    max_budget_cents: int = 500_000


class ProcurementBiddingReport(Model):
    world_id: str
    buyer_id: str
    best_supplier_id: str
    unit_price_cents: int
    down_payment_cents: int
    total_cents: int
    selected: bool
    rationale: str


# ---------------------------------------------------------------------------
# 5. Supplier Quotation Protocols & Models
# ---------------------------------------------------------------------------
class QuoteRequestMessage(Model):
    world_id: str
    supplier_id: str
    buyer_id: str
    quantity: int = 5


class QuoteResponseMessage(Model):
    world_id: str
    supplier_id: str
    unit_price_cents: int
    down_payment_bps: int
    due_in_ticks: int
    fulfillable: bool
    total_cents: int


class CounterOfferReviewMessage(Model):
    world_id: str
    supplier_id: str
    buyer_id: str
    proposed_unit_price_cents: int
    proposed_down_payment_bps: int
    proposed_due_ticks: int
    accepted: bool
    final_unit_price_cents: int
    rationale: str


# ---------------------------------------------------------------------------
# 6. Treasury & Macro Yield Curve Protocols & Models
# ---------------------------------------------------------------------------
class TreasuryDataQuery(Model):
    include_history: bool = False


class TreasuryDataResponse(Model):
    latest_record_date: str
    total_debt_cents: int
    source_api: str
    retrieved_at: str


class DebtShockEstimateRequest(Model):
    world_id: str
    bank_id: str
    debt_increase_percent: float = 25.0
    yield_increase_bps: int = 200
    duration_years: float = 5.0
    exposure_percent: float = 50.0


class DebtShockEstimateResponse(Model):
    world_id: str
    bank_id: str
    estimated_loss_bps: int
    estimated_loss_cents: int
    duration_formula: str
    story_summary: str


# ---------------------------------------------------------------------------
# 7. Labour & Price Oracle Protocols & Models
# ---------------------------------------------------------------------------
class WageBenchmarkQuery(Model):
    category: str = "wages"


class WageBenchmarkResponse(Model):
    category: str
    statutory_min_wage_usd_hour: float
    daily_wage_cents: int
    source_url: str
    legal_effective_date: str


class MenuPriceBasketQuery(Model):
    category: str = "prices"


class MenuPriceBasketResponse(Model):
    category: str
    sample_count: int
    average_drink_cents: int
    min_cents: int
    max_cents: int
    source_url: str


# ---------------------------------------------------------------------------
# 8. Interbank Clearinghouse Protocols & Models
# ---------------------------------------------------------------------------
class InterbankExposureAuditRequest(Model):
    world_id: str


class InterbankExposureAuditResponse(Model):
    world_id: str
    total_interbank_debt_cents: int
    bilateral_pairs_count: int
    max_single_exposure_cents: int
    contagion_risk_score: str
    recommendation: str


class NettingSettlementProposal(Model):
    world_id: str
    total_gross_cents: int
    total_netted_cents: int
    netting_efficiency_percent: float
    liquidity_saved_cents: int


# ---------------------------------------------------------------------------
# 9. Household Welfare & Demand Protocols & Models
# ---------------------------------------------------------------------------
class WelfareAuditRequest(Model):
    world_id: str


class WelfareAuditResponse(Model):
    world_id: str
    total_households: int
    employed_count: int
    employment_rate_percent: float
    median_balance_cents: int
    min_balance_cents: int
    max_balance_cents: int
    gini_estimate: float
    welfare_status: str


class CashStimulusImpactQuery(Model):
    world_id: str
    stimulus_budget_cents: int = 1_000_000


class CashStimulusImpactReport(Model):
    world_id: str
    stimulus_budget_cents: int
    per_household_transfer_cents: int
    projected_employment_gain: int
    consumption_boost_estimate_cents: int
    velocity_multiplier_estimate: float


# ---------------------------------------------------------------------------
# 10. Systemic Balance Sheet Auditor Protocols & Models
# ---------------------------------------------------------------------------
class InvarianceAuditRequest(Model):
    world_id: str


class InvarianceAuditReport(Model):
    world_id: str
    is_balanced: bool
    total_assets_cents: int
    total_liabilities_cents: int
    total_equity_cents: int
    invariant_delta_cents: int
    transactions_count: int
    entities_audited: int
    audit_verdict: str


class FraudAuditRequest(Model):
    world_id: str


class FraudAuditReport(Model):
    world_id: str
    total_screenings: int
    blocked_count: int
    verified_count: int
    compliance_status: str


# ---------------------------------------------------------------------------
# Generic Agent Echo / Status Protocols
# ---------------------------------------------------------------------------
class EconomicAgentError(Model):
    world_id: str = ''
    message: str


class AgentIdentityInquiry(Model):
    query_id: str


class AgentIdentityStatement(Model):
    name: str
    address: str
    role: str
    supported_protocols: List[str]
    description: str
