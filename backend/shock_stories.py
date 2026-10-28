"""Dated public context plus explicitly hypothetical, reproducible stress assumptions."""
import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import httpx
from pydantic import Field

from backend.forks import snapshot_hash
from backend.ledger import LedgerError
from backend.models import Request
from backend.provider import ProviderError

DEBT_API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
DEBT_PAGE = "https://fiscaldata.treasury.gov/datasets/debt-to-the-penny/debt-to-the-penny"


class DebtStress(Request):
    bank_id: str = Field(default="bank_1", min_length=1, max_length=128)
    debt_increase_percent: int = Field(default=25, ge=0, le=100)
    yield_increase_bps: int = Field(default=200, ge=0, le=500)
    modified_duration_years: int = Field(default=5, ge=1, le=10)
    portfolio_exposure_percent: int = Field(default=50, ge=0, le=100)


class ApplyStory(Request):
    report_id: str = Field(min_length=1, max_length=128)


def debt_baseline():
    try:
        with httpx.Client(timeout=20, trust_env=False, follow_redirects=False) as client:
            response = client.get(DEBT_API, params={"sort": "-record_date", "page[size]": 1,
                                                   "fields": "record_date,tot_pub_debt_out_amt"})
            response.raise_for_status()
            row = response.json()["data"][0]
        amount = Decimal(row["tot_pub_debt_out_amt"])
        observed = date.fromisoformat(row["record_date"])
        today = datetime.now(timezone.utc).date()
        if not amount.is_finite() or amount <= 0 or observed > today:
            raise ValueError("Invalid debt observation")
        return {"provider": "US Treasury Fiscal Data", "series": "Total public debt outstanding",
                "value_usd": str(amount), "observation_date": observed.isoformat(),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "age_days": (today - observed).days, "stale": (today - observed).days > 7,
                "source_url": DEBT_PAGE, "api_url": str(response.url), "unit": "USD"}
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, InvalidOperation):
        raise ProviderError("Treasury debt data is unavailable or invalid. No substitute baseline was used; try again later.") from None


def preview(store, simulation_id, request):
    baseline = debt_baseline()
    world = store.get(simulation_id)
    bank = world.state["entities"].get(request.bank_id)
    if not bank or bank["kind"] != "bank":
        raise LedgerError("Choose a commercial bank")
    portfolio = world.ledger.balance(f"{request.bank_id}:risky_assets")
    # First-order bond-price approximation: -D_modified * change in yield.
    # Weight by the assumed share of the simulated risky portfolio in bonds.
    loss_bps = int((Decimal(request.modified_duration_years * request.yield_increase_bps)
                    * request.portfolio_exposure_percent / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    amount = Decimal(baseline["value_usd"])
    hypothetical = (amount * (100 + request.debt_increase_percent) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return store.save_sponsor_report(simulation_id, "shock_story", {
        "title": f"What if US public debt increased by {request.debt_increase_percent}%?",
        "scenario": "debt_bond_stress_v1", "source_tick": world.state["tick"],
        "snapshot_sha256": snapshot_hash(world.state), "baseline": baseline,
        "hypothetical_debt_usd": str(hypothetical), "assumptions": request.model_dump(),
        "transmission": "Hypothetical debt growth -> assumed bond-yield rise -> estimated bond repricing -> bank equity loss -> lending, payroll and spending effects calculated by the economy engine.",
        "limitations": [
            "Debt growth alone does not determine yields, default risk or bank losses. The yield change is a separate user assumption, not estimated from the debt increase.",
            "US gross public debt is national context, not this city's debt or the simulation government's opening balance sheet.",
            "Bond exposure and modified duration are illustrative assumptions, not observed holdings of a real bank.",
            "Duration is a first-order approximation; convexity, hedging, maturity structure and held-to-maturity accounting are not modeled. Larger yield moves make this approximation less accurate.",
            "This stress test assumes immediate recognition of the estimated loss in the simulated risky portfolio. It is not a causal forecast of a policy change or war."
        ],
        "formula": "portfolio loss (%) = exposure (%) / 100 × modified duration × yield increase (bps) / 100",
        "loss_bps": loss_bps, "portfolio_cents": portfolio,
        "estimated_loss_cents": portfolio * loss_bps // 10000,
        "status": "preview", "interpretation": "Real dated baseline; hypothetical increase and transmission assumptions; synthetic bank and economy. Preview moves no money."})


def apply(store, simulation_id, report_id):
    with store.connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT report FROM sponsor_reports WHERE id=? AND source_id=? AND kind='shock_story'",
                                 (report_id, simulation_id)).fetchone()
        if not row:
            raise KeyError(report_id)
        report = json.loads(row[0])
        world = store.load(connection, simulation_id)
        transaction_id = "story:" + report_id
        previous = world.ledger._transactions.get(transaction_id)
        if previous:
            return {"status": "applied", "report": report, "transaction": previous}
        if store.playback_row(connection, simulation_id)["status"] != "paused":
            raise LedgerError("Pause the world before applying a story shock")
        if snapshot_hash(world.state) != report["snapshot_sha256"]:
            raise LedgerError("World changed since preview. Load a new preview before applying.")
        if report["loss_bps"] == 0 or report["estimated_loss_cents"] == 0:
            raise LedgerError("These assumptions imply no bank loss; change the assumptions to apply a shock")
        transaction = world.shock(transaction_id, report["assumptions"]["bank_id"], report["loss_bps"])
        transaction["metadata"]["shock_story_id"] = report_id
        world.emit("sourced_debt_stress_applied", report["assumptions"]["bank_id"],
                   amount_cents=report["estimated_loss_cents"], transaction_id=transaction_id,
                   details={"report_id": report_id, "title": report["title"], "assumptions": report["assumptions"],
                            "baseline_date": report["baseline"]["observation_date"],
                            "baseline_debt_usd": report["baseline"]["value_usd"],
                            "hypothetical_debt_usd": report["hypothetical_debt_usd"],
                            "interpretation": "Debt growth and the yield change are separate hypothetical inputs; no causal relationship is estimated.",
                            "source_url": report["baseline"]["source_url"], "loss_bps": report["loss_bps"]})
        world.audit()
        connection.execute("UPDATE worlds SET state=? WHERE id=?", (json.dumps(world.state), simulation_id))
        return {"status": "applied", "report": report, "transaction": transaction}


def history(store, simulation_id):
    reports = store.sponsor_reports(simulation_id, "shock_story")
    world = store.get(simulation_id)
    return [{**report, "status": "applied" if "story:" + report["report_id"] in world.ledger._transactions else "preview"}
            for report in reports]
