"""Versioned working-capital conventions for Census-scaled worker payrolls."""
from backend.ledger import LedgerError

MODEL='working_capital_v2'
LEGACY='fixed_limits_v1'
DEFAULTS={'opening_payroll_days':5,'credit_payroll_days':20,'loan_review_days':20}

class FinancingRules:
    def scaled_financing(self):
        return self.state.get('financial_model')==MODEL

    def initialize_financing(self, supplied=None):
        if not self.scaled_financing():return
        rates={**DEFAULTS,**(supplied or {})}
        for name in DEFAULTS:
            if type(rates[name]) is not int or not 1<=rates[name]<=260:
                raise LedgerError('Invalid financing assumption: '+name)
        self.state['financial_assumptions']={name:rates[name] for name in DEFAULTS}
        self.state['financial_assumptions']['scope']='Assumed workday conventions, not observed cash reserves or credit limits. Payroll is Census-derived; rent, tax, interest and nonpayroll overhead remain unmodeled.'
        for business in self.state['entities'].values():
            if business['kind']!='business':continue
            payroll=self.payroll(business)
            business['opening_payroll_cents']=payroll
            business['credit_limit_cents']=payroll*rates['credit_payroll_days']
            target=payroll*rates['opening_payroll_days']
            current=self.ledger.balance(business['deposit_account']);change=target-current
            bank=business['bank_id']
            self.ledger.post('genesis:working_capital:'+business['id'],[
                (business['deposit_account'],change),(business['equity_account'],-change),
                (bank+':reserves',change),(bank+':deposit_'+business['id'],-change)],
                {'type':'opening_working_capital','tick':0,'payroll_cents':payroll,'assumed_payroll_days':rates['opening_payroll_days']})

    def borrower_limit(self,business):
        return business.get('credit_limit_cents',500_000) if self.scaled_financing() else 500_000

    def loan_review_days(self):
        return self.state.get('financial_assumptions',{}).get('loan_review_days',20) if self.scaled_financing() else 5

    def settlement_liquidity_lines(self,bank_id,amount):
        if not self.scaled_financing():return []
        reserves=self.ledger.balance(bank_id+':reserves')
        shortfall=max(0,amount-reserves)
        if not shortfall:return []
        sheet=self.ledger.sheet(bank_id)
        if sheet['equity_cents']<=0 or sheet['assets'].get('risky_assets',0)<shortfall:
            return [] # The original transfer fails atomically, without partial liquidation.
        return [(bank_id+':risky_assets',-shortfall),(bank_id+':reserves',shortfall)]
