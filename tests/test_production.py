from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend.engine import Economy
from backend.forks import build_comparison
from backend.ledger import LedgerError
from backend.main import create_app
from backend.procurement import run_procurement
from backend.store import Store


def stocked_world():
    world = Economy.create("goods", scenario="supply_crunch")
    world.create_contract("inputs", "invoice", "business_1", "business_2", 20, 501, 2000, 5)
    world.state["tick"] = 1
    world.produce_goods(world.customer("business_1"))
    return world


def test_production_transfers_material_cost_without_creating_profit_or_money():
    world = Economy.create("goods", scenario="supply_crunch")
    world.create_contract("inputs", "invoice", "business_1", "business_2", 20, 501, 2000, 5)
    business = world.customer("business_1")
    cash, equity = world.ledger.balance("business_1:deposit"), world.ledger.sheet("business_1")["equity_cents"]
    world.state["tick"] = 1
    world.produce_goods(business)
    assert business["materials_units"] == 15 and business["goods_units"] == 50
    assert world.material_cost("business_1") == 7515
    assert world.goods_cost("business_1") == 2505
    assert world.ledger.balance("business_1:deposit") == cash
    assert world.ledger.sheet("business_1")["equity_cents"] == equity
    before = deepcopy(world.state)
    world.produce_goods(business)
    assert world.state == before
    world.audit()


def test_retail_sale_cost_basis_rounding_and_replay():
    world = stocked_world()
    price = world.customer("business_1")["price_cents"]
    equity = world.ledger.sheet("business_1")["equity_cents"]
    before = world.metrics()
    receipt = world.purchase_goods("sale", "household_1", "business_1", 3)
    assert receipt["metadata"]["cost_of_goods_sold_cents"] == 150
    assert world.goods_cost("business_1") == 2355
    assert world.customer("business_1")["goods_units"] == 47
    assert world.ledger.sheet("business_1")["equity_cents"] == equity + price * 3 - 150
    assert world.metrics()["total_deposits_cents"] == before["total_deposits_cents"]
    assert world.metrics()["total_bank_reserves_cents"] == before["total_bank_reserves_cents"]
    saved = deepcopy(world.state)
    assert world.purchase_goods("sale", "household_1", "business_1", 3) == receipt
    assert world.state == saved
    with pytest.raises(LedgerError, match="different contents"):
        world.purchase_goods("sale", "household_1", "business_1", 4)
    # Give another household enough cash to buy all remaining units.
    world.pay("fund-buyer", "business_2", "household_2", price * 47)
    world.purchase_goods("sell-out", "household_2", "business_1", 47)
    assert world.goods_cost("business_1") == 0
    assert world.customer("business_1")["goods_units"] == 0
    world.audit()


def test_failed_retail_sale_changes_neither_stock_nor_money():
    world = stocked_world()
    before = deepcopy(world.state)
    with pytest.raises(LedgerError, match="finished goods"):
        world.purchase_goods("too-many", "household_1", "business_1", 51)
    assert world.state == before
    world.pay("drain", "household_1", "business_2", world.ledger.balance("household_1:deposit"))
    before = deepcopy(world.state)
    with pytest.raises(LedgerError, match="Insufficient"):
        world.purchase_goods("poor", "household_1", "business_1", 1)
    assert world.state == before
    for quantity in (True, 1.2, 0, -1):
        with pytest.raises(LedgerError, match="quantity"):
            world.purchase_goods("bad", "household_1", "business_1", quantity)
    with pytest.raises(LedgerError, match="Retail"):
        world.pay("bypass", "household_2", "business_1", 100, "purchase")


def test_tick_caps_sales_and_reports_stock_shortfall():
    world = Economy.create("goods", households=1, businesses=1, banks=1)
    seller = world.customer("business_1")
    world.customer("household_1")["consumption_budget_cents"] = seller["price_cents"] * 20
    world.step()
    metrics = world.metrics()
    assert metrics["produced_units_this_tick"] == 10
    assert metrics["sold_units_this_tick"] == 10
    assert metrics["unmet_demand_units_this_tick"] == 10
    assert metrics["finished_goods_units"] == 0
    event = next(e for e in world.state["events"] if e["event_type"] == "purchase_stock_limited")
    assert event["details"]["fulfilled_units"] == event["details"]["unmet_units"] == 10
    world.audit()


def test_no_materials_means_no_production_and_restocking_restores_sales(tmp_path):
    store = Store(tmp_path / "supply.sqlite3")
    store.create(Economy.create("supply", scenario="supply_crunch"))
    store.step_paused("supply", 1)
    shortage = store.get("supply")
    assert shortage.customer("business_1")["last_produced_units"] == 0
    assert any(e["event_type"] == "production_limited" and e["agent_id"] == "business_1" for e in shortage.state["events"])
    report = run_procurement(store, "supply", "business_1", {
        "request_id": "restock", "mode": "demo", "supplier_ids": None,
        "quantity": 20, "max_total_cents": 100000, "auto_settle": True})
    assert report["status"] == "contracted"
    store.step_paused("supply", 1)
    recovered = store.get("supply")
    assert recovered.customer("business_1")["last_produced_units"] == 50
    assert any(e["event_type"] == "purchase" and e["counterparty_id"] == "business_1" and e["simulation_tick"] == 2
               for e in recovered.state["events"])
    assert recovered.audit()["balanced"]


def test_inventory_carries_forward_and_closed_or_unstaffed_businesses_do_not_produce():
    world = Economy.create("goods", households=1, businesses=2, banks=1)
    world.customer("household_1")["consumption_budget_cents"] = 0
    world.step(2)
    assert world.customer("business_1")["goods_units"] == 20
    assert world.customer("business_2")["goods_units"] == 0
    world.default_business(world.customer("business_1"), "test closure")
    world.step()
    assert world.customer("business_1")["goods_units"] == 20
    assert world.customer("business_1")["last_produced_units"] == 0
    assert world.entity_view("business_1")["production_capacity_units"] == 0
    world.audit()


def test_audit_detects_finished_goods_tampering():
    world = stocked_world()
    world.customer("business_1")["goods_units"] += 1
    with pytest.raises(LedgerError, match="Finished goods"):
        world.audit()


def test_legacy_worlds_keep_unlimited_consumption_without_new_inventory():
    state = Economy.create("legacy", households=8, businesses=2, banks=2).state
    state.pop("production_model")
    state.pop("goods_flow")
    for business in state["entities"].values():
        if business["kind"] == "business":
            for key in ("goods_units", "last_produced_units", "materials_units"):
                business.pop(key)
            del state["ledger"]["accounts"][f"{business['id']}:goods"]
            del state["ledger"]["accounts"][f"{business['id']}:materials"]
    world = Economy(state)
    world.step()
    assert world.view()["production_model"] == "legacy_unlimited"
    assert any(e["event_type"] == "purchase" for e in world.state["events"])
    assert not any(e["event_type"] == "goods_produced" for e in world.state["events"])
    assert "goods_units" not in world.customer("business_1")
    world.audit()


def test_forks_preserve_goods_and_isolate_production():
    source = stocked_world()
    before = deepcopy(source.state)
    comparison, branches = build_comparison(source, "inventory_fork", {
        "request_id": "fork", "bank_id": "bank_1", "budget_cents": 1000, "ticks": 2})
    assert source.state == before
    assert all(branch.audit()["balanced"] for branch in branches)
    assert all("finished_goods_units" in branch["metrics"] for branch in comparison["branches"])


def test_supply_scenario_and_inventory_fields_in_api(tmp_path):
    with TestClient(create_app(tmp_path / "api.sqlite3")) as client:
        response = client.post("/api/worlds", json={"scenario": "supply_crunch"})
        assert response.status_code == 201
        world = response.json()
        assert world["production_model"] == "finite_v1"
        base = f"/api/worlds/{world['simulation_id']}"
        client.post(base + "/step", json={"ticks": 1})
        business = client.get(base + "/entities/business_1").json()
        assert business["last_produced_units"] == 0 and business["goods_units"] == 0
        assert business["production_capacity_units"] == 50
        assert "goods" in business["balance_sheet"]["assets"]
