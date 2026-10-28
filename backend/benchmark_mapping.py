"""Explicit public-benchmark opening mappings; relationships remain synthetic."""
import random
from copy import deepcopy
from backend.benchmarks import digest
from backend.ledger import LedgerError


def prepare(snapshot):
    if not snapshot or not snapshot.get('profile',{}).get('fdic') or not snapshot['profile'].get('census_cbp'):
        raise LedgerError('Public benchmark requires valid FDIC and Census payroll observations; no synthetic substitution')
    banks=snapshot['profile']['fdic']
    if not 0 < banks['capital_bps'] < 10000 or not 0 <= banks['cash_bps'] < 10000:
        raise LedgerError('Invalid opening bank ratios')
    industries=snapshot['profile']['census_cbp']
    if not industries or any(min(i['employees'],i['establishments'],i['daily_wage_cents'])<=0 for i in industries):
        raise LedgerError('Invalid industry payroll observations')
    return deepcopy(snapshot)


def workforce(world,snapshot):
    rng=random.Random(world.state['seed'] ^ 0xEC0)
    industries=snapshot['profile']['census_cbp']
    businesses=[e for e in world.state['entities'].values() if e['kind']=='business']
    weights=[]
    for business in businesses:
        industry=rng.choices(industries,weights=[i['establishments'] for i in industries],k=1)[0]
        business['benchmark_industry']=deepcopy(industry)
        business['employees']=[]
        weights.append(industry['employees']/industry['establishments'])
    for household in world.state['entities'].values():
        if household['kind']!='household':continue
        business=rng.choices(businesses,weights=weights,k=1)[0]
        household['employer_id']=business['id']
        household['wage_cents']=business['benchmark_industry']['daily_wage_cents']
        business['employees'].append(household['id'])


def bank_ratios(world,snapshot):
    profile=snapshot['profile']['fdic'];capital=profile['capital_bps'];cash=profile['cash_bps']
    mappings=[]
    for bank in world.state['entities'].values():
        if bank['kind']!='bank':continue
        bank_id=bank['id'];sheet=world.ledger.sheet(bank_id)
        # Keep synthetic deposits, loans and interbank exposures, and solve A=L+E.
        liabilities=sheet['liabilities_cents']
        assets=(liabilities*10000+(10000-capital)//2)//(10000-capital)
        equity=assets-liabilities
        reserves=assets*cash//10000
        fixed=sum(v for k,v in sheet['assets'].items() if k not in ('reserves','risky_assets'))
        residual=assets-reserves-fixed
        if min(equity,reserves,residual)<0:
            raise LedgerError('Observed ratios incompatible with synthetic exposures; no clamping performed')
        lines=[(f'{bank_id}:reserves',reserves-sheet['assets']['reserves']),
               (f'{bank_id}:risky_assets',residual-sheet['assets'].get('risky_assets',0)),
               (bank['equity_account'],-(equity-sheet['equity_cents']))]
        world.ledger.post(f'genesis:benchmark:{bank_id}',lines,{'type':'public_benchmark_opening_mapping','tick':0})
        mappings.append(dict(bank_id=bank_id,capital_bps=capital,cash_bps=cash,
            achieved_capital_ratio=equity/assets if assets else 0,achieved_cash_ratio=reserves/assets if assets else 0,
            residual_asset_cents=residual,classification='derived',
            note='Synthetic scale and links. Cash proxy includes balances due from banks. Residual is a pooled shockable proxy, not observed risky holdings.'))
    world.state['public_benchmark']=deepcopy(snapshot)
    world.state['benchmark_mapping']={'version':'public_opening_v1','sha256':digest(snapshot),'banks':mappings}
    world.refresh_banks()
