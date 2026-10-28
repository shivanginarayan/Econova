"""Finite raw inputs, finished-goods inventory, and atomic retail sales."""

from backend.ledger import LedgerError


class ProductionRules:
    def finite_production(self):
        return self.state.get("production_model") == "finite_v1"

    def goods_cost(self, business_id):
        key = f"{business_id}:goods"
        return self.ledger.balance(key) if key in self.ledger.state["accounts"] else 0

    def produce_goods(self, business):
        transaction_id = f"tick:{self.state['tick']}:production:{business['id']}"
        if transaction_id in self.ledger._transactions:
            return
        business["last_produced_units"] = 0
        if business["status"] != "active":
            return
        stock = business["materials_units"]
        required = len(business["employees"])
        used = min(stock, required)
        if used:
            cost = self.material_cost(business["id"]) * used // stock
            quantity = used * 10
            self.ledger.post(transaction_id, [(f"{business['id']}:materials", -cost),
                                              (f"{business['id']}:goods", cost)],
                             {"type": "goods_produced", "tick": self.state["tick"],
                              "business_id": business["id"], "materials_used": used, "goods_produced": quantity})
            business["materials_units"] -= used
            business["goods_units"] += quantity
            business["last_produced_units"] = quantity
            self.state["goods_flow"]["produced_units"] += quantity
            self.emit("goods_produced", business["id"], amount_cents=cost, transaction_id=transaction_id,
                      details={"materials_used": used, "quantity": quantity, "carrying_cost_cents": cost})
        if used < required:
            self.emit("production_limited", business["id"],
                      details={"reason": "insufficient_materials", "materials_required": required,
                               "materials_used": used, "unproduced_units": (required - used) * 10})

    def purchase_goods(self, transaction_id, household_id, business_id, quantity):
        if type(quantity) is not int or quantity <= 0:
            raise LedgerError("Purchase quantity must be a positive integer")
        buyer, seller = self.customer(household_id), self.customer(business_id)
        if buyer["kind"] != "household" or seller["kind"] != "business":
            raise LedgerError("Retail purchases require a household and a business")
        amount = quantity * seller["price_cents"]
        request = {"type": "purchase", "payer_id": household_id, "receiver_id": business_id,
                   "amount_cents": amount, "quantity": quantity}
        previous = self.existing(transaction_id, request)
        if previous is not None:
            return previous
        if not self.finite_production():
            raise LedgerError("Finite retail purchases require a new production world")
        stock = seller["goods_units"]
        if quantity > stock:
            raise LedgerError("Seller has insufficient finished goods")
        cost = self.goods_cost(business_id) * quantity // stock
        lines = self.payment_lines(buyer, seller, amount)
        lines += [(f"{business_id}:goods", -cost), (seller["equity_account"], cost)]
        receipt = self.ledger.post(transaction_id, lines,
            {"type": "purchase", "tick": self.state["tick"], "request": request,
             "cost_of_goods_sold_cents": cost})
        seller["goods_units"] -= quantity
        self.state["goods_flow"]["sold_units"] += quantity
        self.emit("purchase", household_id, business_id, amount, transaction_id,
                  {"quantity": quantity, "unit_price_cents": seller["price_cents"], "cost_of_goods_sold_cents": cost})
        return receipt

    def record_stock_shortfall(self, household, seller, requested, fulfilled):
        if requested > fulfilled:
            unmet = requested - fulfilled
            self.state["goods_flow"]["unmet_demand_units"] += unmet
            self.emit("purchase_stock_limited", household["id"], seller["id"],
                      details={"requested_units": requested, "fulfilled_units": fulfilled,
                               "unmet_units": unmet, "reason": "insufficient_finished_goods"})

    def production_metrics(self):
        businesses = [e for e in self.state["entities"].values() if e["kind"] == "business"]
        flow = self.state.get("goods_flow", {})
        return {"finished_goods_units": sum(e.get("goods_units", 0) for e in businesses),
                "produced_units_this_tick": flow.get("produced_units", 0),
                "sold_units_this_tick": flow.get("sold_units", 0),
                "unmet_demand_units_this_tick": flow.get("unmet_demand_units", 0)}

    def audit_production(self):
        if not self.finite_production():
            return
        expected = {e["id"]: 0 for e in self.state["entities"].values() if e["kind"] == "business"}
        for entry in self.ledger.state["journal"]:
            metadata = entry["metadata"]
            if metadata.get("type") == "goods_produced":
                expected[metadata["business_id"]] += metadata["goods_produced"]
            elif metadata.get("type") == "purchase":
                request = metadata["request"]
                expected[request["receiver_id"]] -= request["quantity"]
        for business_id, units in expected.items():
            actual = self.customer(business_id).get("goods_units")
            if type(actual) is not int or actual < 0 or units != actual or (actual == 0 and self.goods_cost(business_id)):
                raise LedgerError("Finished goods units and journal disagree")
