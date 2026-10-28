"""Ten typed, deterministic Fetch services backed by the existing economy.

Live Nemotron roles remain separate. No financial execution is authorized by
these messages, and unavailable sources never produce fabricated observations.
"""
import asyncio
import hashlib
import os
from functools import partial
from backend.fetch_agents import protocols as p
from backend.fetch_agents.service import EconomyAgentService
from backend.provider import ProviderNotConfigured

ROLES = {
 'central_bank': [(p.CrisisStressInquiry,p.PolicyRescueReport)],
 'commercial_bank': [(p.CreditApplicationMessage,p.UnderwritingDecisionMessage)],
 'corporate_borrower': [(p.PayrollAuditInquiry,p.PayrollGapReport),(p.CreditAcceptanceNotification,p.CreditAcceptanceNotification)],
 'procurement_buyer': [(p.ProcurementInquiry,p.ProcurementBiddingReport)],
 'supplier_quotation': [(p.QuoteRequestMessage,p.QuoteResponseMessage),(p.CounterOfferReviewMessage,p.CounterOfferReviewMessage)],
 'treasury_macro': [(p.TreasuryDataQuery,p.TreasuryDataResponse),(p.DebtShockEstimateRequest,p.DebtShockEstimateResponse)],
 'apify_wage_oracle': [(p.WageBenchmarkQuery,p.WageBenchmarkResponse),(p.MenuPriceBasketQuery,p.MenuPriceBasketResponse)],
 'clearinghouse_settlement': [(p.InterbankExposureAuditRequest,p.InterbankExposureAuditResponse),(p.NettingSettlementProposal,p.NettingSettlementProposal)],
 'household_welfare': [(p.WelfareAuditRequest,p.WelfareAuditResponse),(p.CashStimulusImpactQuery,p.CashStimulusImpactReport)],
 'auditor_inspector': [(p.InvarianceAuditRequest,p.InvarianceAuditReport),(p.FraudAuditRequest,p.FraudAuditReport)],
}


def default_seed(name):
    secret=os.getenv('FETCH_AGENT_SEED')
    if not secret:
        raise ProviderNotConfigured('Set a private stable FETCH_AGENT_SEED before creating Fetch identities')
    return hashlib.sha256(f'{secret}:{name}'.encode()).hexdigest()


def create_agent(role, store_getter=None, seed=None, port=8101, loop=None):
    from uagents import Agent, Protocol, Context
    # Context must be resolvable in module globals by the SDK callback inspector.
    globals()['Context']=Context
    agent=Agent(name=role.replace('_','-')+'-service',seed=seed or default_seed(role),port=port,loop=loop,
        publish_agent_details=False,description='Deterministic saved-state economic service: '+role)
    proto=Protocol(name=role+'_protocol',version='1.1.0')

    def register(request,response):
        async def handler(ctx: Context,sender: str,msg):
            try:
                service=EconomyAgentService(store_getter() if store_getter else None)
                result=await asyncio.to_thread(service.handle,msg)
            except Exception:
                result=p.EconomicAgentError(world_id=getattr(msg,'world_id',''),
                    message='Economic request unavailable or invalid; no financial action executed. Check configured sources and workflow limits.')
            await ctx.send(sender,result)
        proto.on_message(request,replies={response,p.EconomicAgentError})(handler)
    for request,response in ROLES[role]:
        register(request,response)

    @proto.on_message(p.AgentIdentityInquiry,replies={p.AgentIdentityStatement})
    async def identity(ctx: Context,sender: str,msg: p.AgentIdentityInquiry):
        await ctx.send(sender,p.AgentIdentityStatement(name=role,address=agent.address,role=role,
            supported_protocols=[role+'_protocol'],description='Read-only deterministic service. No LLM inference or financial settlement claimed.'))
    agent.include(proto)
    return agent


AGENT_FACTORIES={role:partial(create_agent,role) for role in ROLES}
for _role,_factory in AGENT_FACTORIES.items():
    globals()['create_'+_role+'_agent']=_factory
