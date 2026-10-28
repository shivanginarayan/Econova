"""Verify real saved-state adapters; no registration, model calls or payments.

This verifies local calculations and SDK construction, not Agentverse/ACP chat
registration of ten agents or peer-message transport. Those are separate checks.
"""
import asyncio
import json
import tempfile
from pathlib import Path
from backend.engine import Economy
from backend.store import Store
from backend.forks import snapshot_hash
from backend.fetch_agents.bureau import EconomyBureau
from backend.fetch_agents.workflows import MultiAgentWorkflowCoordinator
from backend.fetch_agents.service import EconomyAgentService
from backend.fetch_agents import protocols as p
from scripts.run_backend import load_environment

async def main():
    load_environment()
    Path('artifacts').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir='artifacts') as scratch:
        store=Store(Path(scratch)/'verify.sqlite3')
        world=Economy.create('ecosystem_verification',seed=42,scenario='credit_crunch')
        store.create(world)
        before=snapshot_hash(world.state)
        bureau=EconomyBureau(store_getter=lambda:store,loop=asyncio.get_running_loop())
        coordinator=MultiAgentWorkflowCoordinator(bureau)
        reports={
            'credit':await coordinator.run_credit_negotiation(world.state['simulation_id']),
            'procurement':await coordinator.run_procurement_negotiation(world.state['simulation_id']),
            'crisis':await coordinator.run_systemic_crisis_orchestration(world.state['simulation_id']),
        }
        service=EconomyAgentService(store)
        reports['payroll']=service.handle(p.PayrollAuditInquiry(world_id=world.state['simulation_id'],business_id='business_1')).model_dump()
        reports['quote']=service.handle(p.QuoteRequestMessage(world_id=world.state['simulation_id'],supplier_id='business_2',buyer_id='business_1')).model_dump()
        reports['debt_preview']=service.handle(p.DebtShockEstimateRequest(world_id=world.state['simulation_id'],bank_id='bank_1',yield_increase_bps=0)).model_dump()
        # Exercise the actual handler registered in the SDK, without publishing
        # agents or representing a direct callback test as peer transport.
        from uagents import Model
        agent=bureau.get_agent('corporate_borrower')
        digest=Model.build_schema_digest(p.PayrollAuditInquiry)
        handler=next(proto.signed_message_handlers[digest] for proto in agent.protocols.values() if digest in proto.signed_message_handlers)
        class ReplyCollector:
            def __init__(self):self.messages=[]
            async def send(self,sender,message):self.messages.append(message)
        collector=ReplyCollector()
        await handler(collector,agent.address,p.PayrollAuditInquiry(world_id=world.state['simulation_id'],business_id='business_1'))
        await handler(collector,agent.address,p.PayrollAuditInquiry(world_id='missing',business_id='business_1'))
        assert isinstance(collector.messages[0],p.PayrollGapReport)
        assert isinstance(collector.messages[1],p.EconomicAgentError)
        assert reports['debt_preview']['estimated_loss_cents']==0
        assert reports['crisis']['ledger_verified']
        assert not reports['credit']['funds_applied'] and not reports['procurement']['contract_executed']
        assert snapshot_hash(store.get(world.state['simulation_id']).state)==before
        evidence={'passed':True,'service_identities':len(bureau.addresses()),'scope':'local SDK construction and saved-state calculations; not external registration or peer transport',
            'source_unchanged':True,'sdk_handler_and_error_reply_verified':True,'reports':reports}
        Path('artifacts/fetch-ecosystem-verification.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in evidence.items() if k!='reports'}))

if __name__=='__main__':
    asyncio.run(main())
