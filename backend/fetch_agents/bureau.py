"""Local Bureau for ten typed saved-state economic services.

External registration and chat discoverability require separate verification.
"""

import asyncio
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    from uagents import Agent, Bureau
except ImportError:
    Agent = object  # type: ignore
    Bureau = object  # type: ignore

from backend.fetch_agents.agents import AGENT_FACTORIES, default_seed


class EconomyBureau:
    """Orchestrates all 10 Fetch.ai economic agents."""

    def __init__(
        self,
        store_getter: Optional[Callable] = None,
        base_port: int = 8100,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        agent_names: Optional[List[str]] = None,
    ):
        if store_getter is None:
            from backend.store import Store
            store = Store(os.getenv('ECONOMY_DB_PATH', str(Path(__file__).resolve().parents[2]/'data'/'economy.sqlite3')))
            store_getter = lambda: store
        self.store_getter = store_getter
        self.base_port = base_port
        self.loop = loop or asyncio.new_event_loop()
        self.agents: Dict[str, Agent] = {}
        target_names = agent_names or list(AGENT_FACTORIES.keys())

        # Instantiate each requested agent
        for idx, name in enumerate(target_names, start=1):
            factory = AGENT_FACTORIES[name]
            port = base_port + idx
            seed = default_seed(name)
            agent = factory(store_getter=store_getter, seed=seed, port=port, loop=self.loop)
            self.agents[name] = agent

        # Create Bureau container
        self.bureau = Bureau(port=base_port, loop=self.loop)
        for agent in self.agents.values():
            self.bureau.add(agent)

    def addresses(self) -> Dict[str, str]:
        """Return the Bech32 address for each of the 10 agents."""
        return {name: agent.address for name, agent in self.agents.items()}

    def get_agent(self, name: str) -> Optional[Agent]:
        """Retrieve a specific agent by economic role name."""
        return self.agents.get(name)

    async def run_async(self):
        """Run the Bureau asynchronously."""
        return await self.bureau.run_async()

    def stop(self):
        """Gracefully stop the Bureau server."""
        if hasattr(self.bureau, "_server") and hasattr(self.bureau._server, "server") and self.bureau._server.server:
            self.bureau._server.server.should_exit = True
