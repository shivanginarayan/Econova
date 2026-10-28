"""Reproduce matched stress tests across seeds; no model calls or external collection."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.calibration import load, checksum
from backend.engine import Economy
from backend.forks import build_comparison, snapshot_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calibration-id', required=True, help='Existing real collected calibration; never silently substituted')
    parser.add_argument('--output', default='artifacts/microsoft-technical-evaluation')
    args = parser.parse_args()
    calibration = load(args.calibration_id)
    seeds = [41, 42, 43, 44, 45]
    rows = []
    for input_mode in ('seeded_synthetic', 'collected_public_references'):
        for seed in seeds:
            sid = f'evaluation_{input_mode}_{seed}'
            world = Economy.create(sid, seed=seed, scenario='credit_crunch',
                **({'calibration_id': args.calibration_id, 'calibration': calibration} if input_mode == 'collected_public_references' else {}))
            world.shock('evaluation-shock', 'bank_1', loss_bps=4000)
            before = snapshot_hash(world.state)
            comparison, branches = build_comparison(world, f'comparison_{input_mode}_{seed}',
                {'request_id': 'evaluation', 'bank_id': 'bank_1', 'budget_cents': 1_000_000, 'ticks': 12})
            assert snapshot_hash(world.state) == before, 'Comparison mutated source'
            assert all(branch.audit()['balanced'] for branch in branches), 'Unbalanced branch'
            rows.append({'input_mode': input_mode, 'seed': seed, 'source_unchanged': True, 'comparison': comparison})
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = {'evaluated_at': datetime.now(timezone.utc).isoformat(), 'seeds': seeds,
        'scope': 'Synthetic experiments, not forecasts or measured customer savings. Selected public price/wage references do not calibrate other behavior.',
        'model_calls': 0, 'source_collection_calls': 0,
        'calibration': {'calibration_id': args.calibration_id, 'sha256': checksum(calibration),
            'collected_at': calibration['collected_at'], 'sources': calibration['sources']}, 'experiments': rows}
    (output/'evaluation.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    lines = ['# Reproducible stress-test evidence', '', payload['scope'], '',
        f"Evaluated {payload['evaluated_at']}. Five fixed seeds × two input modes × three branches = 30 branch runs. Each covers 12 simulated days after a hypothetical 40% loss on Bank 1 risky investments. Each intervention receives $10,000 gross support. No model calls, new crawls, external payments or existing-world mutations.", '',
        '| Inputs | Seed | Strategy | Final jobs | Business defaults | Jobs vs baseline | Defaults avoided | Gross support | Audit |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for row in rows:
        for branch in row['comparison']['branches']:
            m, d = branch['metrics'], branch['delta_vs_no_intervention']
            lines.append(f"| {row['input_mode']} | {row['seed']} | {branch['strategy']} | {m['employed_households']} | {m['business_defaults']} | {d['employed_households']:+d} | {-d['business_defaults']:+d} | ${m['public_support_disbursed_cents']/100:,.2f} | Balanced |")
    lines += ['', 'All 30 final branch audits balanced; all ten source snapshots remained unchanged. Rule-based rankings and model recommendations are separate. Gross support is not net fiscal loss. Negative defaults avoided means additional defaults.', '',
        f"Public-reference mode used frozen calibration `{args.calibration_id}`, collected {calibration['collected_at']}, checksum `{checksum(calibration)}`. Seeded mode deliberately uses synthetic prices and wages. Neither mode contains real household or bank balance sheets.", '',
        'Source observations are limited to one cafe menu and a general statutory minimum wage, converted with an assumed eight-hour workday. These experiments do not establish causality in the real economy or demonstrate validated customer demand. Do not select only favorable seeds or treat this small seed set as statistical validation.', '',
        'Full comparisons, per-branch outcomes, timelines, audits and provenance: [evaluation.json](./evaluation.json).']
    (output/'evaluation.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'experiments': len(rows), 'branch_runs': len(rows)*3, 'all_balanced': True,
        'all_sources_unchanged': True, 'report': str(output/'evaluation.md')}))


if __name__ == '__main__':
    main()
