import os

from gohumanloop import APIProvider, DefaultHumanLoopManager
from gohumanloop.adapters.langgraph_adapter import HumanloopAdapter
from gohumanloop.providers.terminal_provider import TerminalProvider

api_key = os.environ.get("GOHUMANLOOP_API_KEY", "").strip()
api_base_url = os.environ.get(
    "GOHUMANLOOP_API_BASE_URL", "http://127.0.0.1:9800/api"
)

if api_key:
    humanloop_manager = DefaultHumanLoopManager(
        APIProvider(
            name="ApiProvider",
            api_base_url=api_base_url,
            api_key=api_key,
            default_platform="feishu",
        )
    )
else:
    humanloop_manager = DefaultHumanLoopManager(
        initial_providers=TerminalProvider(name="TerminalProvider")
    )

humanloop_adapter = HumanloopAdapter(
    manager=humanloop_manager,
    default_timeout=300,
)
