"""Opt-in hosted judging access: signed visitors, world ownership and bounded jobs."""
import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

from fastapi import HTTPException,Request
from starlette.responses import JSONResponse


class HostedAccess:
    def __init__(self,store):
        self.store=store;self.enabled=os.getenv('ECONOMY_PUBLIC_MODE')=='1'
        self.secret=os.getenv('ECONOMY_SESSION_SECRET','')
        if not self.enabled:return
        if len(self.secret)<32:
            raise ValueError('Hosted mode requires ECONOMY_SESSION_SECRET (32+characters)')
        with store.connection() as c:
            c.execute('CREATE TABLE IF NOT EXISTS hosted_worlds (world_id TEXT PRIMARY KEY,visitor TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS hosted_usage (visitor TEXT NOT NULL,bucket INTEGER NOT NULL,kind TEXT NOT NULL,count INTEGER NOT NULL,PRIMARY KEY(visitor,bucket,kind))')

    def signature(self,visitor):
        return hmac.new(self.secret.encode(),visitor.encode(),hashlib.sha256).hexdigest()

    def cookie(self,value):
        visitor,sep,signature=(value or '').partition('.')
        return visitor if sep and len(visitor)==32 and hmac.compare_digest(signature,self.signature(visitor)) else None

    def claim(self,visitor,world_id):
        if not self.enabled:return
        with self.store.connection() as c:
            c.execute('INSERT OR IGNORE INTO hosted_worlds VALUES (?,?)',(world_id,visitor))

    def owns(self,visitor,world_id):
        # Forks inherit their parent's capability, never another visitor's world.
        with self.store.connection() as c:
            for _ in range(20):
                row=c.execute('SELECT visitor FROM hosted_worlds WHERE world_id=?',(world_id,)).fetchone()
                if row:return hmac.compare_digest(row[0],visitor)
                row=c.execute('SELECT state FROM worlds WHERE id=?',(world_id,)).fetchone()
                if not row:return False
                world_id=(json.loads(row[0]).get('lineage') or {}).get('parent_simulation_id')
                if not world_id:return False
        return False

    def usage(self,visitor,kind,limit,global_limit):
        bucket=int(time.time()//3600)
        with self.store.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            for owner,maximum in [(visitor,limit),('*',global_limit)]:
                row=c.execute('SELECT count FROM hosted_usage WHERE visitor=? AND bucket=? AND kind=?',(owner,bucket,kind)).fetchone()
                if row and row[0]>=maximum:raise HTTPException(429,'Hosted usage limit reached. Please try again later.',headers={'Retry-After':'3600'})
            for owner in [visitor,'*']:
                c.execute('INSERT INTO hosted_usage VALUES (?,?,?,1) ON CONFLICT(visitor,bucket,kind) DO UPDATE SET count=count+1',(owner,bucket,kind))
            c.execute('DELETE FROM hosted_usage WHERE bucket<?',(bucket-48,))

    async def authorize(self,request):
        if not self.enabled or request.url.path=='/health':return
        visitor=request.state.visitor;path=request.url.path
        forbidden=('/control-room','/fraud/','/spacetime','/data-context/research','/data-context/sources')
        if any(fragment in path for fragment in forbidden) or path in ('/api/fraud/profiles','/api/credit/profiles','/api/calibrations/collect'):
            raise HTTPException(403,'This optional integration is disabled on the hosted build.')
        world=request.path_params.get('simulation_id')
        for parameter,table in [('job_id','agent_jobs'),('run_id',{'agent-runs':'agent_runs','credit-runs':'credit_runs','procurement-runs':'procurement_runs'}.get(path.split('/')[2] if len(path.split('/'))>2 else '')),('fork_id','forks')]:
            resource=request.path_params.get(parameter)
            if resource and table:
                with self.store.connection() as c:row=c.execute(f'SELECT source_id FROM {table} WHERE id=?',(resource,)).fetchone()
                if not row:raise HTTPException(404,'Resource not found')
                world=row[0]
        if world and not self.owns(visitor,world):raise HTTPException(404,'Resource not found')
        if request.method!='POST':return
        if len(await request.body())>64000:raise HTTPException(413,'Request too large')
        body=await request.json()
        if not isinstance(body,dict):raise HTTPException(422,'Request must be an object')
        if body.get('allow_paid_research') or body.get('require_crs') or body.get('crs_profile_id'):
            raise HTTPException(403,'Paid research and private credit integrations are disabled on the hosted build.')
        if path=='/api/worlds':
            if any(type(body.get(k,v)) is not int for k,v in [('households',40),('businesses',8)]) or body.get('households',40)>200 or body.get('businesses',8)>40:raise HTTPException(422,'Hosted experiments support up to200households and40businesses.')
            self.usage(visitor,'world',20,200)
        if path.endswith(('/step','/forks','/scenario-comparisons')):
            if type(body.get('ticks',12)) is not int or body.get('ticks',12)>30:raise HTTPException(422,'Hosted requests support up to30steps at a time.')
            if not path.endswith('/step'):self.usage(visitor,'comparison',30,150)
        if path.endswith(('/agent-runs','/credit-runs','/procurement-runs')):
            raise HTTPException(403,'Use background agent jobs on the hosted build.')
        if path.endswith(('/agent-jobs','/credit-jobs','/procurement-jobs')):
            if body.get('auto_settle') or not body.get('agent_review'):raise HTTPException(422,'Hosted agent jobs require supervisor review and explicit settlement.')
            if any(type(body.get(k,v)) is not int for k,v in [('ticks',12),('max_experiments',2)]) or body.get('ticks',12)>30 or body.get('max_experiments',2)>2:raise HTTPException(422,'Hosted investigations support up to30steps and2comparisons.')
            self.usage(visitor,'inference',int(os.getenv('ECONOMY_JOBS_PER_HOUR','2')),int(os.getenv('ECONOMY_GLOBAL_JOBS_PER_HOUR','10')))


async def authorize_hosted(request:Request):
    await request.app.state.hosted_access.authorize(request)


class HostedMiddleware:
    def __init__(self,app,access):self.app=app;self.access=access
    async def __call__(self,scope,receive,send):
        if not self.access.enabled or scope['type']!='http' or scope['path']=='/health':
            return await self.app(scope,receive,send)
        request=Request(scope)
        visitor=self.access.cookie(request.cookies.get('econova-visitor'));fresh=not visitor;visitor=visitor or uuid4().hex
        scope.setdefault('state',{})['visitor']=visitor
        # Keep browser-origin checks for writes using signed visitor cookies.
        origin=request.headers.get('origin')
        if request.method=='POST' and origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):
            return await JSONResponse({'detail':'Cross-origin writes are disabled.'},403)(scope,receive,send)
        async def guarded_send(message):
            if message['type']=='http.response.start':
                headers=list(message.get('headers',[]));headers.extend([(b'cache-control',b'private, no-store'),(b'x-content-type-options',b'nosniff')])
                if fresh:
                    secure='; Secure' if os.getenv('ECONOMY_COOKIE_SECURE','1')=='1' else ''
                    cookie=f'econova-visitor={visitor}.{self.access.signature(visitor)}; Path=/; HttpOnly; SameSite=Strict; Max-Age=5184000{secure}'
                    headers.append((b'set-cookie',cookie.encode()))
                message={**message,'headers':headers}
            await send(message)
        await self.app(scope,receive,guarded_send)
