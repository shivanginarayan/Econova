"""Baseline unemployment and gradual, capped layoffs at stressed businesses.

A layoff only moves a worker off a payroll: the household stays active, no loan
is written off, no bank equity changes, and no ledger entry is posted.
"""

import random

# All labour-market limits live here.
BASELINE_UNEMPLOYMENT = 0.04        # share of households without a job when a world is created
LAYOFF_CHANCE = 0.35                # chance a stressed business sheds a worker on a given day
LAYOFFS_PER_BUSINESS_PER_TICK = 1   # rate cap per business
LAYOFF_SHARE_PER_TICK = 0.05        # rate cap across the economy, as a share of all households
LAYOFF_UNEMPLOYMENT_CEILING = 0.30  # gradual layoffs pause at this unemployment; defaults still apply
STRESS_MEMORY_TICKS = 5             # a business stays stressed this many days after its last stress signal

CREDIT_STRESS_EVENTS = {"credit_rejected"}
PAYROLL_STRESS_EVENTS = {"payment_rejected"}
SUPPLY_STRESS_EVENTS = {"supplier_contract_default"}


class LaborRules:
    def apply_baseline_unemployment(self):
        households = [e for e in self.state["entities"].values() if e["kind"] == "household"]
        count = round(len(households) * BASELINE_UNEMPLOYMENT)
        # A dedicated stream keeps every other seeded value of the world unchanged.
        rng = random.Random(f"{self.state['seed']}:baseline_unemployment")
        for household in sorted(rng.sample(households, count), key=lambda h: h["id"]):
            self.state["entities"][household["employer_id"]]["employees"].remove(household["id"])
            household["employer_id"] = None

    def layoff_budget(self):
        households = [e for e in self.state["entities"].values() if e["kind"] == "household"]
        unemployed = sum(h["employer_id"] is None for h in households)
        ceiling_room = int(len(households) * LAYOFF_UNEMPLOYMENT_CEILING) - unemployed
        return max(0, min(int(len(households) * LAYOFF_SHARE_PER_TICK), ceiling_room))

    def recent_events(self):
        oldest = self.state["tick"] - STRESS_MEMORY_TICKS + 1
        recent = []
        for event in reversed(self.state["events"]):
            if event["simulation_tick"] < oldest:
                break
            recent.append(event)
        return recent

    def stress_reasons(self, business, recent, failed_employers):
        reasons = set()
        if business["id"] in failed_employers or business.get("missed_payroll_ticks", 0):
            reasons.add("missed_payroll")
        if business.get("missed_debt_ticks", 0):
            reasons.add("refinancing_failure")
        for event in recent:
            if event["event_type"] in CREDIT_STRESS_EVENTS and event["agent_id"] == business["id"]:
                reasons.add("refinancing_failure" if event["details"].get("purpose") == "refinancing" else "credit_rejected")
            if (event["event_type"] in PAYROLL_STRESS_EVENTS and event["agent_id"] == business["id"]
                    and event["details"].get("purpose") == "salary"):
                reasons.add("missed_payroll")
            if event["event_type"] in SUPPLY_STRESS_EVENTS and business["id"] in (event["agent_id"], event["counterparty_id"]):
                reasons.add("supplier_contract_default")
        if self.finite_production() and business["materials_units"] < len(business["employees"]):
            reasons.add("low_materials")
        return sorted(reasons)

    def gradual_layoffs(self, businesses, failed_employers):
        budget = self.layoff_budget()
        recent = self.recent_events()
        # Seed and tick only, so snapshot branches draw identical numbers.
        rng = random.Random(f"{self.state['seed']}:{self.state['tick']}:layoffs")
        for business in businesses:
            roll = rng.random()
            if business["status"] != "active" or not business["employees"]:
                continue
            reasons = self.stress_reasons(business, recent, failed_employers)
            if not reasons or roll >= LAYOFF_CHANCE:
                continue
            for _ in range(LAYOFFS_PER_BUSINESS_PER_TICK):
                if budget <= 0 or not business["employees"]:
                    break
                worker_id = rng.choice(sorted(business["employees"]))
                business["employees"].remove(worker_id)
                self.state["entities"][worker_id]["employer_id"] = None
                self.emit("job_lost", worker_id, business["id"], details={"reason": "layoff", "stress": reasons})
                budget -= 1
