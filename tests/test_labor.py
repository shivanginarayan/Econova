from collections import Counter

import pytest

import backend.labor as labor
from backend.engine import Economy
from backend.forks import STRATEGIES, build_comparison


def unemployment(world):
    return 1 - world.metrics()["employment_rate"]


def path(world, days):
    rates = [unemployment(world)]
    for _ in range(days):
        world.step(1)
        rates.append(unemployment(world))
    return rates


def layoffs(world):
    return [e for e in world.state["events"] if e["event_type"] == "job_lost" and e["details"].get("reason") == "layoff"]


@pytest.mark.parametrize("scenario", ["standard", "credit_crunch", "supply_crunch"])
def test_baseline_unemployment_is_about_four_percent_at_tick_zero(scenario):
    world = Economy.create("baseline", scenario=scenario)
    assert world.state["tick"] == 0
    assert 0.025 <= unemployment(world) <= 0.055
    for household in (e for e in world.state["entities"].values() if e["kind"] == "household"):
        employer = household["employer_id"]
        assert household["status"] == "active"
        assert employer is None or household["id"] in world.state["entities"][employer]["employees"]
    world.audit()


def test_credit_crunch_raises_unemployment_gradually_without_trigger_crisis():
    world = Economy.create("crunch", scenario="credit_crunch")
    rates = path(world, 30)
    assert rates[-1] > rates[0]
    assert len({round(r, 4) for r in rates}) >= 3, "rise should happen over several ticks, not one cliff"
    assert layoffs(world)
    assert not any(e["event_type"] == "bank_asset_loss" for e in world.state["events"])


def test_supply_stress_raises_unemployment_gradually_without_trigger_crisis():
    world = Economy.create("supply", scenario="supply_crunch")
    rates = path(world, 30)
    assert rates[-1] > rates[0]
    assert len({round(r, 4) for r in rates}) >= 3
    assert all("low_materials" in e["details"]["stress"] for e in layoffs(world))


def test_healthy_businesses_do_not_lay_off():
    world = Economy.create("healthy", scenario="standard")
    rates = path(world, 30)
    assert layoffs(world) == []
    assert rates == [rates[0]] * len(rates)


@pytest.mark.parametrize("scenario", ["credit_crunch", "supply_crunch"])
@pytest.mark.parametrize("seed", [42, 7, 99])
def test_per_tick_layoffs_stay_within_the_rate_cap(scenario, seed):
    world = Economy.create("cap", seed=seed, scenario=scenario)
    households = world.state["config"]["households"]
    path(world, 30)
    per_tick = Counter(e["simulation_tick"] for e in layoffs(world))
    per_business = Counter((e["simulation_tick"], e["counterparty_id"]) for e in layoffs(world))
    assert max(per_business.values(), default=0) <= labor.LAYOFFS_PER_BUSINESS_PER_TICK
    assert max(per_tick.values(), default=0) <= int(households * labor.LAYOFF_SHARE_PER_TICK)


@pytest.mark.parametrize("days", [12, 30])
def test_crunch_only_run_peaks_at_a_plausible_level(days):
    world = Economy.create("peak", scenario="credit_crunch")
    rates = path(world, days)
    assert max(rates) < 0.35
    assert world.metrics()["business_defaults"] == 0


def test_gradual_layoffs_make_crunch_defaults_rarer(monkeypatch):
    def defaults(seed):
        world = Economy.create("defaults", seed=seed, scenario="credit_crunch")
        world.step(30)
        return world.metrics()["business_defaults"]
    seeds = range(1, 11)
    with_layoffs = sum(defaults(seed) for seed in seeds)
    monkeypatch.setattr(labor, "LAYOFF_CHANCE", 0)
    without_layoffs = sum(defaults(seed) for seed in seeds)
    assert with_layoffs < without_layoffs


def test_layoff_leaves_household_active_and_ledger_untouched():
    world = Economy.create("ledger", scenario="supply_crunch")
    while not layoffs(world):
        world.step(1)
    event = layoffs(world)[0]
    household = world.state["entities"][event["agent_id"]]
    business = world.state["entities"][event["counterparty_id"]]
    assert event["transaction_id"] is None and event["amount_cents"] is None
    assert household["status"] == "active" and household["employer_id"] is None
    assert household["id"] not in business["employees"] and business["status"] == "active"
    assert not any(e["event_type"] in ("loan_default", "business_default") for e in world.state["events"])
    world.audit()


@pytest.mark.parametrize("scenario", ["credit_crunch", "supply_crunch"])
def test_same_seed_reruns_give_the_same_employment_path(scenario):
    first = Economy.create("rerun", seed=42, scenario=scenario)
    second = Economy.create("rerun", seed=42, scenario=scenario)
    assert path(first, 30) == path(second, 30)
    assert first.state == second.state


def test_fork_reality_starts_near_96_percent_and_keeps_its_structure():
    source = Economy.create("fork", scenario="credit_crunch")
    result, worlds = build_comparison(source, "fork_labor", {"request_id": "labor-1", "bank_id": "bank_1",
                                                             "budget_cents": 1_000_000, "ticks": 12})
    assert [b["strategy"] for b in result["branches"]] == list(STRATEGIES)
    for branch, world in zip(result["branches"], worlds):
        assert 0.94 <= branch["timeline"][0]["employment_rate"] <= 0.975
        assert len(branch["timeline"]) == 13
        world.audit()
    rank = lambda b: (-b["metrics"]["employed_households"], b["metrics"]["business_defaults"],
                      b["metrics"]["insolvent_banks"], b["metrics"]["stressed_banks"],
                      b["metrics"]["public_support_disbursed_cents"])
    assert result["recommended_strategy"] == min(result["branches"], key=rank)["strategy"]


def test_ledger_audits_after_intervention_and_layoffs():
    world = Economy.create("intervene", scenario="credit_crunch")
    world.step(10)
    world.intervene("labor-intervention", "household_cash", 100_000, None)
    world.audit()
    world.step(10)
    world.audit()
