"""Versioned synthetic cash-flow assumptions, not estimated economic parameters."""
import random
from backend.ledger import LedgerError

OPERATING_MODEL = 'cashflow_v2'
LEGACY_MODEL = 'legacy_v1'
# Declared behavioral assumptions, held constant across matched branches.
INCOME_SPENDING_BPS = 9000
WEALTH_SPENDING_BPS = 500
CAPACITY_PAYROLL_BPS = 12500
LIQUIDITY_TARGET_BPS = 2000

class OperatingRules:
    def circular_flow(self):
        return self.state.get('operating_model') == OPERATING_MODEL and self.finite_production()

    def initialize_operations(self, supplied=None):
        if not self.circular_flow():
            return
        parameters = {'income_spending_bps': INCOME_SPENDING_BPS,
                      'wealth_spending_bps': WEALTH_SPENDING_BPS,
                      'capacity_payroll_bps': CAPACITY_PAYROLL_BPS,
                      'liquidity_target_bps': LIQUIDITY_TARGET_BPS}
        if supplied is not None:
            for key in parameters:
                value = supplied.get(key, parameters[key])
                upper = 100000 if key == 'capacity_payroll_bps' else 10000
                lower = 1 if key == 'capacity_payroll_bps' else 0
                if type(value) is not int or not lower <= value <= upper:
                    raise LedgerError('Invalid operating assumption: ' + key)
                parameters[key] = value
        self.state['operating_assumptions'] = {**parameters,
            'scope': 'Synthetic behavioral parameters. Public prices/wages do not measure productivity or spending preferences.'}
        for business in self.state['entities'].values():
            if business['kind'] != 'business':
                continue
            payroll = self.payroll(business)
            workers = len(business['employees'])
            denominator = workers * business['price_cents'] * 10000
            business['units_per_worker'] = max(1, (payroll * parameters['capacity_payroll_bps'] + denominator - 1) // denominator) if denominator else 10
            # Fixed opening market-size weight, never recomputed to fund losses.
            business['market_weight'] = max(1, payroll)

    def manage_operating_liquidity(self):
        if not self.circular_flow():
            return
        for bank in self.state['entities'].values():
            if bank['kind'] != 'bank':
                continue
            sheet = self.ledger.sheet(bank['id'])
            if sheet['equity_cents'] <= 0:
                continue  # Asset conversion cannot recapitalize an insolvent bank.
            deposits = sum(v for k,v in sheet['liabilities'].items() if k.startswith('deposit_'))
            target_bps = self.state.get('operating_assumptions', {}).get('liquidity_target_bps', LIQUIDITY_TARGET_BPS)
            target = (deposits * target_bps + 9999) // 10000
            amount = min(max(0, target - sheet['assets']['reserves']), sheet['assets'].get('risky_assets', 0))
            if amount:
                transaction_id = f"tick:{self.state['tick']}:portfolio_liquidity:{bank['id']}"
                self.ledger.post(transaction_id, [(f"{bank['id']}:risky_assets", -amount), (f"{bank['id']}:reserves", amount)], {'type':'portfolio_liquidity','tick':self.state['tick'],'assumption':'marketable assets convert at recorded value','amount_cents':amount})
                self.emit('liquidity_rebalanced', bank['id'], amount_cents=amount, transaction_id=transaction_id, details={'equity_injected_cents':0,'target_reserves_cents':target})

    def output_per_worker(self, business):
        return business.get('units_per_worker', 10) if self.circular_flow() else 10

    def household_spending_budget(self, household, received_wages):
        available = self.ledger.balance(household['deposit_account'])
        # Only wages actually paid enter income. Transfers/savings enter wealth.
        prior_wealth = max(0, available - received_wages)
        assumptions = self.state.get('operating_assumptions', {})
        income_bps = assumptions.get('income_spending_bps', INCOME_SPENDING_BPS)
        wealth_bps = assumptions.get('wealth_spending_bps', WEALTH_SPENDING_BPS)
        return min(available, received_wages * income_bps // 10000 + prior_wealth * wealth_bps // 10000)

    def consume_household(self, household, businesses, received_wages):
        budget = self.household_spending_budget(household, received_wages)
        household['last_received_wages_cents'] = received_wages
        household['last_consumption_budget_cents'] = budget
        self.emit('consumption_budget', household['id'], details={
            'received_wages_cents': received_wages, 'budget_cents': budget,
            'rule': OPERATING_MODEL})
        # Stable common random preferences across snapshot branches, including
        # closed/out-of-stock sellers. Eligibility does not redraw preferences.
        rng = random.Random(f"{self.state['seed']}:{self.state['tick']}:{household['id']}:basket")
        pool = list(businesses)
        order = []
        while pool:
            seller = rng.choices(pool, weights=[b.get('market_weight', 1) for b in pool], k=1)[0]
            order.append(seller)
            pool.remove(seller)
        remaining = budget
        for index, seller in enumerate([*order, *order[:2]]):
            if seller['status'] != 'active' or remaining <= 0:
                continue
            allocation = min(remaining, (budget + 1) // 2) if index < 2 else remaining
            requested = allocation // seller['price_cents']
            quantity = min(requested, seller['goods_units'])
            if quantity:
                try:
                    self.purchase_goods(f"tick:{self.state['tick']}:purchase:{household['id']}:{seller['id']}:{index}", household['id'], seller['id'], quantity)
                    remaining -= quantity * seller['price_cents']
                except LedgerError as error:
                    self.emit('payment_rejected', household['id'], seller['id'], quantity * seller['price_cents'], details={'purpose':'purchase','reason':str(error)})
                    # An invalid payer cannot be repaired by trying another shop.
                    break
            self.record_stock_shortfall(household, seller, requested, quantity)
