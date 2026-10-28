"""Comparable shock alternatives from one immutable saved economy."""
import json
from uuid import uuid4
from backend.engine import Economy
from backend.forks import snapshot_hash
from backend.ledger import LedgerError
from backend import __version__

class ScenarioStore:
    @staticmethod
    def init_scenario_tables(connection):
        connection.execute('CREATE TABLE IF NOT EXISTS scenario_starts (source_id TEXT PRIMARY KEY, snapshot TEXT NOT NULL, origin TEXT NOT NULL)')
        connection.execute('''CREATE TABLE IF NOT EXISTS scenario_comparisons (
            id TEXT PRIMARY KEY, source_id TEXT NOT NULL, request_id TEXT NOT NULL,
            request TEXT NOT NULL, result TEXT NOT NULL, UNIQUE(source_id, request_id))''')

    def compare_scenarios(self, simulation_id, request):
        with self.connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            current = self.load(connection, simulation_id)
            if request['bank_id'] not in current.state['entities'] or current.state['entities'][request['bank_id']]['kind'] != 'bank':
                raise LedgerError('Scenario target must be a bank in this economy')
            previous = connection.execute('SELECT request, result FROM scenario_comparisons WHERE source_id=? AND request_id=?', (simulation_id,request['request_id'])).fetchone()
            if previous:
                if json.loads(previous[0]) != request:
                    raise LedgerError('Scenario comparison request ID already used with different contents')
                return json.loads(previous[1])
            anchor = connection.execute('SELECT snapshot, origin FROM scenario_starts WHERE source_id=?',(simulation_id,)).fetchone()
            if anchor is None:
                current.audit()
                anchor = (json.dumps(current.state), 'captured_current')
                connection.execute('INSERT INTO scenario_starts VALUES (?, ?, ?)',(simulation_id,*anchor))
            source, origin = Economy(json.loads(anchor[0])), anchor[1]
        source.audit()
        comparison_id = 'scenarios_'+uuid4().hex
        digest = snapshot_hash(source.state)
        branches, worlds = [], []
        for key, loss in [('no_additional_loss',0),('chosen_loss',request['loss_bps']),('alternative_loss',request['alternative_loss_bps'])]:
            branch=Economy(source.state)
            branch_id=comparison_id+'_'+key
            branch.state['simulation_id']=branch_id
            for event in branch.state['events']:
                event['simulation_id']=branch_id
            branch.state['lineage']={'scenario_comparison_id':comparison_id,'parent_simulation_id':simulation_id,'snapshot_sha256':digest,'loss_bps':loss,'source_tick':source.state['tick']}
            branch.emit('scenario_forked',details=branch.state['lineage'].copy())
            if loss:
                branch.shock('scenario:'+comparison_id+':'+key,request['bank_id'],loss_bps=loss)
            timeline=[branch.metrics()]
            history_length=len(branch.state['history'])
            branch.step(request['ticks'])
            timeline.extend(branch.state['history'][history_length:])
            branches.append({'scenario':key,'loss_bps':loss,'simulation_id':branch_id,'metrics':branch.metrics(),
                             'timeline':timeline,'entities':[branch.entity_view(e['id']) for e in branch.state['entities'].values() if e['kind'] in ('bank','business')], 'audit':branch.audit()})
            worlds.append(branch)
        baseline=branches[0]['metrics']
        for branch in branches:
            branch['employment_delta_pp_vs_no_additional_loss']=(branch['metrics']['employment_rate']-baseline['employment_rate'])*100
        result={'comparison_id':comparison_id,'source_simulation_id':simulation_id,'source_tick':source.state['tick'],
                'end_tick':source.state['tick']+request['ticks'],'snapshot_sha256':digest,'source_origin':origin,
                'source_event_sequence':len(source.state['events']),'seed':source.state['seed'],'engine_version':__version__,
                'request':request,'initial_metrics':source.metrics(),'branches':branches,
                'scope':'Same starting snapshot, bank, frozen inputs and horizon. Only the additional investment loss differs. No new rescue policy is applied.'}
        with self.connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            previous=connection.execute('SELECT request, result FROM scenario_comparisons WHERE source_id=? AND request_id=?',(simulation_id,request['request_id'])).fetchone()
            if previous:
                if json.loads(previous[0]) != request:
                    raise LedgerError('Scenario comparison request ID already used with different contents')
                return json.loads(previous[1])
            for world in worlds:
                connection.execute('INSERT INTO worlds VALUES (?, ?)',(world.state['simulation_id'],json.dumps(world.state)))
            connection.execute('INSERT INTO scenario_comparisons VALUES (?, ?, ?, ?, ?)',(comparison_id,simulation_id,request['request_id'],json.dumps(request),json.dumps(result)))
        return result

    def latest_scenarios(self, simulation_id):
        with self.connection() as connection:
            self.load(connection,simulation_id)
            row=connection.execute('SELECT result FROM scenario_comparisons WHERE source_id=? ORDER BY rowid DESC LIMIT 1',(simulation_id,)).fetchone()
            return json.loads(row[0]) if row else None
