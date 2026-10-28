"""Read-only financial evidence captured at a lending decision."""
def decision_finances(source, business_id):
    business = source.customer(business_id)
    tick = source.state['tick']
    start = min(tick, max(1, tick - 4))
    purchases = [e for e in source.state['events'] if e['event_type'] == 'purchase'
                 and e['counterparty_id'] == business_id and start <= e['simulation_tick'] <= tick]
    sheet = source.ledger.sheet(business_id)
    return {'captured_tick': tick, 'net_worth_cents': sheet['equity_cents'],
            'deposit_cents': source.ledger.balance(business['deposit_account']),
            'debt_cents': source.ledger.balance(business['debt_account']),
            'sales_cents': sum(e['amount_cents'] or 0 for e in purchases),
            'sales_start_tick': start, 'sales_end_tick': tick}
