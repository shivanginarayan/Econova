"""Dated public benchmarks, with explicit provenance and no inferred missing data."""
import csv
import hashlib
import io
import json
import math
import os
import re
import statistics
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

FDIC = 'https://api.fdic.gov/banks/financials'
CBP = 'https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23us.zip'
SERIES = {
    'FEDFUNDS': ('Federal Reserve', 'Effective federal funds rate', 'percent, monthly, not seasonally adjusted', 'Interest context only; loans currently track principal, not interest.'),
    'DRTSCIS': ('Federal Reserve', 'Net banks tightening small-firm lending standards', 'net percent, quarterly, not seasonally adjusted', 'Survey balance, not a loan rejection probability.'),
    'LES1252881500Q': ('BLS via FRED', 'Median full-time worker weekly nominal earnings', 'USD/week, quarterly, seasonally adjusted', 'Worker earnings, not household income or a wage distribution.'),
    'LEU0252911300Q': ('BLS via FRED', '25th percentile full-time worker weekly nominal earnings', 'USD/week, quarterly, not seasonally adjusted', 'Distribution benchmark only; not household income or an industry-specific wage distribution.'),
    'LEU0252911400Q': ('BLS via FRED', '75th percentile full-time worker weekly nominal earnings', 'USD/week, quarterly, not seasonally adjusted', 'Distribution benchmark only; do not combine with seasonally adjusted median as a fitted distribution.'),
    'PCE': ('BEA via FRED', 'Personal consumption expenditures', 'USD billions, monthly, seasonally adjusted annual rate', 'National spending benchmark; includes categories absent from this toy economy.'),
    'DSPI': ('BEA via FRED', 'Disposable personal income', 'USD billions, monthly, seasonally adjusted annual rate', 'After-tax national income; model wages currently have no tax deductions.'),
    'PSAVERT': ('BEA via FRED', 'Personal saving rate', 'percent, monthly, seasonally adjusted annual rate', 'Aggregate saving/disposable income; not the model household income-spending coefficient.'),
}
SECTORS = {'31----': 'Manufacturing (31–33)', '44----': 'Retail trade (44–45)', '72----': 'Accommodation and food services (72)'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def record(key, value, unit, source, url, period, conversion='Identity; no conversion', classification='observed', usage='validation_context', **extra):
    if isinstance(value, (int, float)) and (isinstance(value, bool) or not math.isfinite(value)):
        raise ValueError('Invalid observation')
    return dict(parameter=key, value=value, unit=unit, source=source, source_url=url,
                observation_date=period, classification=classification, conversion=conversion,
                usage=usage, retrieved_at=datetime.now(timezone.utc).isoformat(), **extra)


def fdic(client):
    # Discover the latest published quarter, rather than assuming the current one exists.
    latest = client.get(FDIC, params={'fields': 'REPDTE', 'limit': 1, 'sort_by': 'REPDTE', 'sort_order': 'DESC', 'format': 'json'})
    latest.raise_for_status()
    period = str(latest.json()['data'][0]['data']['REPDTE'])
    if not re.fullmatch(r'\d{8}', period):
        raise ValueError('Invalid FDIC period')
    response = client.get(FDIC, params={'filters': f'REPDTE:{period} AND ASSET:[100000 TO 10000000]',
        'fields': 'CERT,REPDTE,ASSET,EQ,DEP,CHBAL', 'limit': 10000, 'sort_by': 'CERT', 'sort_order': 'ASC', 'format': 'json'})
    response.raise_for_status()
    payload = response.json()
    rows = [r['data'] for r in payload['data']]
    if len(rows) != int(payload['meta']['total']) or not rows:
        raise ValueError('FDIC cohort incomplete')
    if len({r['CERT'] for r in rows}) != len(rows) or any(str(r['REPDTE']) != period for r in rows):
        raise ValueError('Mixed or duplicate FDIC observations')
    valid = [r for r in rows if all(type(r.get(k)) in (int, float) and math.isfinite(r[k]) for k in ['ASSET','EQ','DEP','CHBAL'])
             and r['ASSET'] > 0 and 0 < r['EQ'] < r['ASSET'] and 0 <= r['CHBAL'] < r['ASSET'] and 0 <= r['DEP'] <= r['ASSET']]
    if not valid:
        raise ValueError('No usable FDIC ratios')
    date = datetime.strptime(period, '%Y%m%d').date().isoformat()
    common = dict(source='FDIC BankFind financials', url=str(response.url), period=date,
                  geography='United States; reporting banks with assets USD100 million–10 billion',
                  cohort_count=len(rows), usable_count=len(valid), excluded_count=len(rows)-len(valid))
    observations = []
    for field in ['ASSET','EQ','DEP','CHBAL']:
        observations.append(record('fdic_sum_'+field, sum(r[field] for r in valid), 'USD thousands', **common,
            conversion=f'Sum of {field} across usable institution records; FDIC dollar fields are in thousands.', classification='derived'))
    profile = {}
    for field, key in [('EQ','capital_bps'), ('CHBAL','cash_bps'), ('DEP','deposit_bps')]:
        value = round(statistics.median(r[field]/r['ASSET'] for r in valid)*10000)
        profile[key] = value
        observations.append(record('fdic_'+key, value, 'basis points of assets', **common,
            conversion=f'Median of institution {field}/ASSET, multiplied by 10000 and rounded. Equal institution weights.',
            classification='derived', usage='opening_bank_ratio' if field != 'DEP' else 'validation_context'))
    return observations, profile


def cbp(client):
    response = client.get(CBP)
    response.raise_for_status()
    if len(response.content) > 10_000_000:
        raise ValueError('Unexpected CBP archive size')
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = [n for n in archive.namelist() if n.endswith('.txt') or n.endswith('.csv')]
        if len(names) != 1 or archive.getinfo(names[0]).file_size > 30_000_000:
            raise ValueError('Unexpected CBP archive')
        rows = list(csv.DictReader(io.TextIOWrapper(archive.open(names[0]), encoding='utf-8-sig')))
    observations, industries = [], []
    for code, label in SECTORS.items():
        matched = [r for r in rows if r['naics'] == code and r['lfo'] == '-']
        if len(matched) != 1:
            raise ValueError('CBP industry missing or duplicated')
        row = matched[0]
        # Published national totals include disclosure noise; never interpret suppressed/missing as zero.
        values = {k: int(row[k]) for k in ['emp','ap','est'] if row[k].isdigit()}
        if len(values) != 3 or min(values.values()) <= 0:
            raise ValueError('CBP total suppressed or missing')
        common = dict(source='Census County Business Patterns 2023 national bulk file', url=CBP,
            period='2023', geography='United States', industry=label, industry_code=code,
            note='Paid-employee establishments; employment is March reference-week count, payroll is annual. Disclosure noise retained.',
            disclosure_flags={k:row.get(k+'_nf') for k in ['emp','ap']})
        for field, unit in [('emp','employees in March reference week'), ('ap','USD thousands/year'), ('est','establishments')]:
            observations.append(record('cbp_'+code+'_'+field, values[field], unit, **common))
        daily = round(values['ap']*100000 / values['emp'] / 260)
        observations.append(record('cbp_'+code+'_daily_wage_cents', daily, 'USD cents/simulated workday', **common,
            classification='derived', conversion='Annual payroll thousands ×100000 / March employment / assumed260 paid workdays; rounded to cents. Not a longitudinal mean salary.', usage='opening_worker_wage'))
        observations.append(record('cbp_'+code+'_workers_per_establishment', values['emp']/values['est'], 'employees/establishment', **common,
            classification='derived', conversion='March employment / establishments', usage='relative_business_size'))
        industries.append(dict(code=code, label=label, establishments=values['est'], employees=values['emp'], daily_wage_cents=daily))
    return observations, industries


def fred(client, series, as_of):
    source, label, unit, note = SERIES[series]
    response = client.get('https://fred.stlouisfed.org/graph/fredgraph.csv', params={'id':series, 'cosd':'2023-01-01', 'coed':as_of})
    response.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(response.text)))
    usable = [r for r in rows if r.get(series) not in (None, '', '.') and r.get('observation_date', '') <= as_of]
    row = max(usable, key=lambda r:r['observation_date'])
    value = float(row[series])
    return record(series, value, unit, source, 'https://fred.stlouisfed.org/series/'+series,
        row['observation_date'], geography='United States', label=label, note=note,
        download_url=str(response.url), vintage='Latest revised values at retrieval, not a historical real-time vintage')


def acs(client, key):
    if not key:
        return [], 'needs_CENSUS_API_KEY'
    base='https://api.census.gov/data/2023/acs/acs5'
    fields=[f'B19001_{n:03}{suffix}' for n in range(1,18) for suffix in ['E','M']]
    response=client.get(base, params={'get':','.join(fields), 'for':'us:*', 'key':key})
    response.raise_for_status()
    data=response.json()
    if len(data)!=2:
        raise ValueError('Unexpected ACS geography')
    row=dict(zip(*data))
    records=[]
    for field in fields:
        value=int(row[field])
        if value<0:
            raise ValueError('ACS suppressed value')
        records.append(record(field,value,'households' if field.endswith('E') else 'households, 90% margin of error',
            'Census ACS 2019–2023 five-year B19001',base,'2019–2023',geography='United States',
            note='Income bins in2023 inflation-adjusted dollars. Household income is not individual wages. Estimates and margins retained.'))
    return records, 'available'


def collect():
    now=datetime.now(timezone.utc)
    result=dict(schema_version=1,collected_at=now.isoformat(),as_of=now.date().isoformat(),observations=[],status={},profile={},
        scope='US bank-size cohort and a three-industry US slice; not a real city or a representative national microeconomy.')
    with httpx.Client(timeout=35,follow_redirects=True,trust_env=False) as client:
        for name, function in [('fdic',lambda:fdic(client)), ('census_cbp',lambda:cbp(client))]:
            try:
                observations, profile=function()
                result['observations'].extend(observations)
                result['profile'][name]=profile
                result['status'][name]='available'
            except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError,zipfile.BadZipFile,StopIteration):
                result['status'][name]='unavailable_or_invalid'
        for series in SERIES:
            try:
                result['observations'].append(fred(client,series,result['as_of']))
                result['status'][series]='available'
            except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError):
                result['status'][series]='unavailable_or_invalid'
        try:
            observations,status=acs(client,os.getenv('CENSUS_API_KEY'))
            result['observations'].extend(observations);result['status']['acs_distribution']=status
        except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError):
            result['status']['acs_distribution']='unavailable_or_invalid'
    result['status']['bea_input_output']='not_implemented; supplier coefficients and contracts remain assumed'
    result['status']['bls_wage_distribution']='quartile_context_only; no fitted household distribution'
    matched={r['parameter']:r for r in result['observations'] if r['parameter'] in ('PCE','DSPI')}
    if len(matched)==2 and matched['PCE']['observation_date']==matched['DSPI']['observation_date'] and matched['DSPI']['value']>0:
        result['observations'].append(record('consumption_to_disposable_income',matched['PCE']['value']/matched['DSPI']['value']*100,
            'percent','BEA via FRED','https://fred.stlouisfed.org/series/PCE',matched['PCE']['observation_date'],
            classification='derived',conversion='100 × PCE / DSPI at the same monthly observation period; common SAAR dollar units cancel.',
            note='Aggregate average propensity, not marginal propensity or individual spending rule.',denominator_source_url='https://fred.stlouisfed.org/series/DSPI'))
    result['assumptions']=[record(k,v,u,'Econova model design','https://github.com/shivanginarayan/Econova', 'model_v1', c,'assumed','model_mapping') for k,v,u,c in [
        ('paid_workdays',260,'days/year','52weeks ×5days; model ticks interpreted as paid workdays for this conversion'),
        ('bank_mapping','median ratio; synthetic liabilities and links','mapping','Scale total assets to liabilities/(1-capital ratio); use cash/assets for reserves. Residual noncash assets pooled as shockable proxy, not reported risky securities.'),
        ('industry_mapping','three-sector slice','mapping','Sample industry by establishments; assign workers by relative employees/establishment; each household is one worker proxy. No household-income calibration.'),
    ]]
    result['benchmark_id']='bench_'+digest(result)[:24]
    return result


def root():
    return Path(os.getenv('ECONOMY_BENCHMARK_DIR','data/benchmarks'))


def save(snapshot):
    directory=root();directory.mkdir(parents=True,exist_ok=True)
    target=directory/(snapshot['benchmark_id']+'.json')
    # IDs include retrieval metadata, so refresh never overwrites an earlier vintage.
    if target.exists() and json.loads(target.read_text(encoding='utf-8'))!=snapshot:
        raise ValueError('Immutable benchmark collision')
    target.write_text(json.dumps(snapshot,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (directory/'latest.json').write_text(json.dumps({'benchmark_id':snapshot['benchmark_id']}),encoding='utf-8')
    return snapshot


def load(benchmark_id):
    if not re.fullmatch(r'bench_[a-f0-9]{24}',benchmark_id):
        raise ValueError('Invalid benchmark ID')
    data=json.loads((root()/(benchmark_id+'.json')).read_text(encoding='utf-8'))
    content={k:v for k,v in data.items() if k!='benchmark_id'}
    if data['benchmark_id']!=benchmark_id or 'bench_'+digest(content)[:24]!=benchmark_id:
        raise ValueError('Benchmark integrity check failed')
    return data


def latest():
    try:
        return load(json.loads((root()/'latest.json').read_text(encoding='utf-8'))['benchmark_id'])
    except (OSError,ValueError,KeyError,TypeError):
        return None
