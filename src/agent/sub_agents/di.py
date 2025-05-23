"""DI module for the sub-agents."""

from injector import Module, Binder, singleton, provider, multiprovider


class SubAgentModule(Module):
    """Wiring."""
