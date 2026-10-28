"""Read-only economic protocol adapters. All figures come from saved state.

These are deterministic Fetch services; live Nemotron decision roles remain in
agents.py, credit_agents.py and procurement.py outside this package.
"""
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
from uuid import uuid4

from backend.engine import Economy
from backend.forks import build_comparison
from backend.ledger import LedgerError
from backend.credit_policy import business_facts, assess_credit
from backend.models import ForkRequest, ProcurementRequest, QuoteTerms
from backend.supply_policy import supplier_facts, validate_terms
from backend.provider import ProviderNotConfigured
from backend.fetch_agents import protocols as p


class EconomyAgentService:
    def __init__(self, store):
        self.store = store

    def handle(self, msg):
        if self.store is None:
            raise ProviderNotConfigured('A configured economy store is required; no sample substitution')
        if isinstance(msg, p.TreasuryDataQuery):
            from backend.shock_stories import debt_baseline
            data = debt_baseline()
            return p.TreasuryDataResponse(latest_record_date=data['observation_date'],
                total_debt_cents=int(Decimal(data['value_usd']) * 100), source_api=data['source_url'], retrieved_at=data['retrieved_at'])
        if isinstance(msg, (p.WageBenchmarkQuery, p.MenuPriceBasketQuery)):
            from backend import apify_collection
            data, _ = apify_collection.latest_data()
            if not data:
                raise ProviderNotConfigured('Completed Apify observations required; no assumed market values')
            category = 'wages' if isinstance(msg, p.WageBenchmarkQuery) else 'prices'
            if msg.category != category:
                raise LedgerError('Unsupported source category')
            source = next(s for s in data['sources'] if s.get('category') == category)
            if category == 'prices':
                prices = data['price_cents']
                return p.MenuPriceBasketResponse(category=category, sample_count=len(prices),
                    average_drink_cents=sum(prices)//len(prices), min_cents=min(prices), max_cents=max(prices), source_url=source['source_url'])
            wages = data['daily_wage_cents']
            observations=source.get('observations',[])
            if len(set(wages)) != 1 or not observations or any(r.get('unit')!='usd_hour' or r.get('kind')!='statutory_wage_floor_not_average_pay' for r in observations):
                raise LedgerError('This protocol requires one statutory wage reference')
            # The collector's hourly-to-day conversion explicitly assumes 8 hours.
            return p.WageBenchmarkResponse(category=category, daily_wage_cents=wages[0],
                statutory_min_wage_usd_hour=wages[0]/800, source_url=source['source_url'],
                legal_effective_date=next((r['effective_date'] for r in source.get('observations',[]) if r.get('effective_date')), 'Effective date unavailable in saved source'))
        world = self.store.get(msg.world_id)
        if isinstance(msg, p.CrisisStressInquiry):
            ForkRequest(request_id='validate', bank_id=msg.target_bank_id, budget_cents=msg.budget_cents, ticks=msg.ticks)
            if not 0 <= msg.loss_bps <= 10000:
                raise LedgerError('Invalid hypothetical loss')
            source = Economy(world.state)
            if msg.loss_bps:
                source.shock('fetch_preview_'+uuid4().hex, msg.target_bank_id, msg.loss_bps)
            result, _ = build_comparison(source, 'fetch_preview_'+uuid4().hex, {
                'request_id':uuid4().hex, 'bank_id':msg.target_bank_id, 'budget_cents':msg.budget_cents, 'ticks':msg.ticks})
            branches = [p.BranchMetricSummary(strategy=b['strategy'], **{k:b['metrics'][k] for k in (
                'employed_households','business_defaults','insolvent_banks','public_support_disbursed_cents')}) for b in result['branches']]
            strategy = result['recommended_strategy']
            return p.PolicyRescueReport(world_id=msg.world_id,target_bank_id=msg.target_bank_id,
                recommended_strategy=strategy,branches=branches,rationale=result['recommendation_basis'],
                public_disbursement_cents=0 if strategy=='no_intervention' else msg.budget_cents, funds_applied=False)
        if isinstance(msg, p.PayrollAuditInquiry):
            facts=business_facts(world,msg.business_id)
            return p.PayrollGapReport(world_id=msg.world_id,business_id=msg.business_id,
                deposits_cents=facts['deposit_cents'],payroll_due_cents=facts['payroll_cents'],
                shortfall_cents=facts['payroll_shortfall_cents'],needs_financing=facts['payroll_shortfall_cents']>0,status=facts['status'])
        if isinstance(msg, p.CreditApplicationMessage):
            facts=business_facts(world,msg.borrower_id)
            if facts['bank_id'] != msg.bank_id:
                raise LedgerError('Bank does not match the business account')
            result=assess_credit(world,msg.borrower_id,msg.requested_cents)
            health=result.get('projected_bank_health') or facts['bank']
            return p.UnderwritingDecisionMessage(world_id=msg.world_id,bank_id=msg.bank_id,borrower_id=msg.borrower_id,
                approved=result['eligible'],approved_cents=msg.requested_cents if result['eligible'] else 0,
                capital_ratio_post_issuance=health['capital_ratio'],
                rationale='; '.join(result['reasons']) or 'Eligible under recorded financial policy; settlement and human safeguards are separate')
        if isinstance(msg, p.CreditAcceptanceNotification):
            # A caller's acceptance message is not an authenticated settlement grant.
            raise LedgerError('Use the existing credit-run acceptance, human approval and settlement endpoints')
        if isinstance(msg, (p.QuoteRequestMessage,p.CounterOfferReviewMessage)):
            quantity=msg.quantity if isinstance(msg,p.QuoteRequestMessage) else 1
            if not 1 <= quantity <= 1000:
                raise LedgerError('Quantity must be 1 to 1000')
            facts=supplier_facts(world,msg.buyer_id,msg.supplier_id,quantity)
            if isinstance(msg,p.QuoteRequestMessage):
                price=max(facts['minimum_unit_price_cents'],facts['reference_unit_price_cents'])
                return p.QuoteResponseMessage(world_id=msg.world_id,supplier_id=msg.supplier_id,
                    unit_price_cents=price,down_payment_bps=facts['minimum_down_payment_bps'],
                    due_in_ticks=facts['maximum_due_in_ticks'],fulfillable=facts['can_supply'],total_cents=quantity*price)
            terms=QuoteTerms(unit_price_cents=msg.proposed_unit_price_cents,down_payment_bps=msg.proposed_down_payment_bps,
                due_in_ticks=msg.proposed_due_ticks,rationale='Read-only counteroffer assessment').model_dump()
            try:
                validate_terms(facts,terms); accepted=facts['can_supply']
            except LedgerError:
                accepted=False
            return msg.model_copy(update={'accepted':accepted,'final_unit_price_cents':msg.proposed_unit_price_cents if accepted else 0,
                'rationale':'Read-only policy check; use procurement-run selection and separate settlement'})
        if isinstance(msg,p.ProcurementInquiry):
            from backend.procurement import run_procurement
            request=ProcurementRequest(request_id='fetch_'+uuid4().hex,mode='demo',quantity=msg.target_units,max_total_cents=msg.max_budget_cents).model_dump()
            report=run_procurement(self.store,msg.world_id,msg.buyer_id,request)
            offer=report.get('selected_offer') or {}
            return p.ProcurementBiddingReport(world_id=msg.world_id,buyer_id=msg.buyer_id,
                best_supplier_id=offer.get('supplier_id',''),unit_price_cents=offer.get('unit_price_cents',0),
                down_payment_cents=offer.get('down_payment_cents',0),total_cents=offer.get('total_cents',0),
                selected=bool(offer),rationale='Deterministic procurement rehearsal on saved state; no contract settled')
        if isinstance(msg,p.DebtShockEstimateRequest):
            if not (0<=msg.exposure_percent<=100 and 0<=msg.yield_increase_bps<=500 and 1<=msg.duration_years<=10 and 0<=msg.debt_increase_percent<=100):
                raise LedgerError('Assumptions outside supported bounds')
            bps=int((Decimal(str(msg.exposure_percent))/100*Decimal(str(msg.duration_years))*msg.yield_increase_bps).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
            bps=min(10000,bps)
            portfolio=world.ledger.balance(f'{msg.bank_id}:risky_assets')
            return p.DebtShockEstimateResponse(world_id=msg.world_id,bank_id=msg.bank_id,estimated_loss_bps=bps,
                estimated_loss_cents=portfolio*bps//10000,duration_formula='exposure fraction * assumed duration * assumed yield change',
                story_summary='Hypothetical assumptions on a synthetic portfolio. Debt growth does not determine yields. Preview only.')
        if isinstance(msg,(p.InterbankExposureAuditRequest,p.NettingSettlementProposal)):
            rows=[r for r in world.state.get('interbank_obligations',[]) if r['amount_cents']>0]
            total=sum(r['amount_cents'] for r in rows)
            if isinstance(msg,p.InterbankExposureAuditRequest):
                return p.InterbankExposureAuditResponse(world_id=msg.world_id,total_interbank_debt_cents=total,
                    bilateral_pairs_count=len({(r['borrower_id'],r['lender_id']) for r in rows}),
                    max_single_exposure_cents=max((r['amount_cents'] for r in rows),default=0),contagion_risk_score='NOT_CALIBRATED',
                    recommendation='Observed outstanding obligations only; no netting or settlement executed')
            raise LedgerError('Network messages cannot execute reserve settlement; use the audited tick engine')
        if isinstance(msg,p.WelfareAuditRequest):
            people=[e for e in world.state['entities'].values() if e['kind']=='household']
            balances=sorted(world.ledger.balance(e['deposit_account']) for e in people)
            n=len(balances);total=sum(balances);employed=sum(e['employer_id'] is not None for e in people)
            gini=sum((2*i-n-1)*x for i,x in enumerate(balances,1))/(n*total) if n and total else 0
            return p.WelfareAuditResponse(world_id=msg.world_id,total_households=n,employed_count=employed,
                employment_rate_percent=100*employed/n if n else 0,median_balance_cents=int(median(balances)) if n else 0,
                min_balance_cents=min(balances,default=0),max_balance_cents=max(balances,default=0),gini_estimate=gini,welfare_status='SYNTHETIC_OBSERVATIONS')
        if isinstance(msg,p.CashStimulusImpactQuery):
            raise LedgerError('No calibrated velocity multiplier exists; compare actual household_cash branches')
        if isinstance(msg,p.InvarianceAuditRequest):
            audit=world.audit();sheets=[world.ledger.sheet(e) for e in world.state['entities']]
            totals={k:sum(s[k] for s in sheets) for k in ('assets_cents','liabilities_cents','equity_cents')}
            return p.InvarianceAuditReport(world_id=msg.world_id,is_balanced=audit['balanced'],
                total_assets_cents=totals['assets_cents'],total_liabilities_cents=totals['liabilities_cents'],total_equity_cents=totals['equity_cents'],
                invariant_delta_cents=totals['assets_cents']-totals['liabilities_cents']-totals['equity_cents'],
                transactions_count=audit['transaction_count'],entities_audited=len(sheets),audit_verdict='SYNTHETIC_LEDGER_AUDIT_PASSED')
        if isinstance(msg,p.FraudAuditRequest):
            reports=self.store.sponsor_reports(msg.world_id,'fraud')
            return p.FraudAuditReport(world_id=msg.world_id,total_screenings=len(reports),
                blocked_count=sum(r.get('decision')=='blocked' for r in reports),
                verified_count=sum(r.get('provider')=='crs' and r.get('decision')=='clear' for r in reports),
                compliance_status='Recorded screens only; not a compliance certification')
        raise LedgerError('Unsupported economic protocol message')
