"""Run and orchestrate the 10 typed Fetch economic services.

Usage:
    # List all 10 economic agents with their derived Fetch Bech32 addresses
    python -m scripts.run_fetch_ecosystem --list

    # Run all 10 agents concurrently within a Fetch.ai Bureau
    python -m scripts.run_fetch_ecosystem --bureau [--port 8100]

    # Run a specific agent standalone
    python -m scripts.run_fetch_ecosystem --agent central_bank

    # Execute a saved-state backend workflow (not peer-transport evidence)
    python -m scripts.run_fetch_ecosystem --workflow [credit|procurement|crisis]
"""

import argparse
import asyncio
import json
import sys

from scripts.run_backend import load_environment


def list_agents():
    from backend.fetch_agents.bureau import EconomyBureau
    bureau = EconomyBureau()
    print("=" * 70)
    print("ECONOMY GOD MODE — 10 TYPED FETCH ECONOMIC SERVICES")
    print("=" * 70)
    addresses = bureau.addresses()
    for idx, (name, addr) in enumerate(addresses.items(), start=1):
        agent = bureau.get_agent(name)
        desc = getattr(agent, "_description", "") or getattr(agent, "description", "")
        print(f"[{idx:2d}] {name:<26} -> {addr}")
        print(f"     Description: {desc}")
    print("=" * 70)


def run_standalone_agent(agent_name: str, port: int):
    from backend.fetch_agents.agents import AGENT_FACTORIES
    if agent_name not in AGENT_FACTORIES:
        print(f"Unknown agent: '{agent_name}'. Available: {list(AGENT_FACTORIES.keys())}")
        sys.exit(1)
    from backend.fetch_agents.bureau import EconomyBureau
    group = EconomyBureau(base_port=port-1, agent_names=[agent_name])
    agent = group.get_agent(agent_name)
    print(f"Starting standalone Fetch agent '{agent_name}' on port {port}...")
    print(f"Fetch address: {agent.address}")
    agent.run()


def run_bureau(port: int):
    from backend.fetch_agents.bureau import EconomyBureau
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bureau = EconomyBureau(base_port=port, loop=loop)
    print(f"Starting Fetch.ai Bureau with all 10 agents on base port {port}...")
    for name, addr in bureau.addresses().items():
        print(f" - {name:<26} @ {addr}")
    try:
        loop.run_until_complete(bureau.run_async())
    except KeyboardInterrupt:
        print("\nStopping Bureau...")
        bureau.stop()


def run_workflow(name: str, world_id: str, mode: str):
    from backend.fetch_agents.bureau import EconomyBureau
    from backend.fetch_agents.workflows import MultiAgentWorkflowCoordinator

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bureau = EconomyBureau(loop=loop)
    coordinator = MultiAgentWorkflowCoordinator(bureau)

    print(f"Running multi-agent workflow '{name}'...")
    if name == "credit":
        result = loop.run_until_complete(coordinator.run_credit_negotiation(world_id, mode=mode))
    elif name == "procurement":
        result = loop.run_until_complete(coordinator.run_procurement_negotiation(world_id, mode=mode))
    elif name == "crisis":
        result = loop.run_until_complete(coordinator.run_systemic_crisis_orchestration(world_id))
    else:
        print(f"Unknown workflow '{name}'. Choose from: credit, procurement, crisis")
        sys.exit(1)

    print(json.dumps(result, indent=2))


def main():
    load_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List all 10 agents and addresses")
    parser.add_argument("--bureau", action="store_true", help="Run all 10 agents in a Bureau")
    parser.add_argument("--agent", type=str, help="Run an individual agent standalone")
    parser.add_argument("--port", type=int, default=8100, help="Port or base port (default: 8100)")
    parser.add_argument("--workflow", type=str, choices=["credit", "procurement", "crisis"],
                        help="Run an end-to-end multi-agent workflow")
    parser.add_argument("--world-id", help="Existing saved economy world; required for a workflow")
    parser.add_argument("--mode", choices=["demo", "live"], default="demo", help="Explicit model mode for credit/procurement; never settles funds")
    args = parser.parse_args()

    if args.list:
        list_agents()
    elif args.agent:
        run_standalone_agent(args.agent, args.port)
    elif args.bureau:
        run_bureau(args.port)
    elif args.workflow:
        if not args.world_id:
            parser.error("--workflow requires --world-id for an existing saved world")
        run_workflow(args.workflow, args.world_id, args.mode)
    else:
        list_agents()


if __name__ == "__main__":
    main()
