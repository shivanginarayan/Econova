"""Backend coordination of real bounded economic workflows.

This convenience coordinator calls saved-state tools directly. It is not proof
that typed peer messages were exchanged, and never settles credit or contracts.
"""
import asyncio
from uuid import uuid4
from backend.fetch_agents.service import EconomyAgentService
from backend.fetch_agents import protocols as p
from backend.models import CreditRunRequest, ProcurementRequest
from backend.credit_agents import run_credit
from backend.procurement import run_procurement


class MultiAgentWorkflowCoordinator:
    def __init__(self,bureau):
        self.bureau=bureau
        self.store=bureau.store_getter()

    async def run_credit_negotiation(self,world_id,business_id='business_1',bank_id='bank_1',requested_cents=100_000,mode='demo'):
        world=self.store.get(world_id)
        if world.customer(business_id)['bank_id']!=bank_id:
            raise ValueError('Bank does not match the business account')
        request=CreditRunRequest(request_id='ecosystem_'+uuid4().hex,mode=mode,max_amount_cents=requested_cents,auto_settle=False).model_dump()
        report=await asyncio.to_thread(run_credit,self.store,world_id,business_id,request)
        return {'workflow':'corporate_credit_negotiation','world_id':world_id,'provider_mode':mode,
            'report':report,'approved':report['status']=='approved','settled_principal_cents':0,
            'funds_applied':False,'trace':report['trace']}

    async def run_procurement_negotiation(self,world_id,buyer_id='business_1',supplier_id='business_2',quantity=5,max_budget_cents=250_000,mode='demo'):
        others=sorted(e['id'] for e in self.store.get(world_id).state['entities'].values() if e['kind']=='business' and e['id'] not in (buyer_id,supplier_id) and e['status']=='active')
        if not others:
            raise ValueError('Two distinct active suppliers required')
        request=ProcurementRequest(request_id='ecosystem_'+uuid4().hex,mode=mode,supplier_ids=[supplier_id,others[0]],quantity=quantity,max_total_cents=max_budget_cents,auto_settle=False).model_dump()
        report=await asyncio.to_thread(run_procurement,self.store,world_id,buyer_id,request)
        offer=report.get('selected_offer') or {}
        return {'workflow':'procurement_supply_negotiation','world_id':world_id,'provider_mode':mode,
            'report':report,'contract_executed':False,'funds_applied':False,
            'agreed_unit_price_cents':offer.get('unit_price_cents',0),'trace':report['trace']}

    async def run_systemic_crisis_orchestration(self,world_id,target_bank_id='bank_1',loss_bps=4000,budget_cents=1_000_000):
        service=EconomyAgentService(self.store)
        policy=await asyncio.to_thread(service.handle,p.CrisisStressInquiry(world_id=world_id,target_bank_id=target_bank_id,loss_bps=loss_bps,budget_cents=budget_cents))
        audit=await asyncio.to_thread(service.handle,p.InvarianceAuditRequest(world_id=world_id))
        welfare=await asyncio.to_thread(service.handle,p.WelfareAuditRequest(world_id=world_id))
        clearing=await asyncio.to_thread(service.handle,p.InterbankExposureAuditRequest(world_id=world_id))
        return {'workflow':'systemic_crisis_analysis','world_id':world_id,'funds_applied':False,
            'provider_mode':'deterministic_saved_state','recommended_strategy':policy.recommended_strategy,
            'ledger_verified':audit.is_balanced,'trace':[{'agent':name,'result':result.model_dump()} for name,result in
                [('central_bank',policy),('clearinghouse_settlement',clearing),('household_welfare',welfare),('auditor_inspector',audit)]]}
