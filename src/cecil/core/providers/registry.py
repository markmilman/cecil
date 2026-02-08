"""Provider discovery and registration.

Maintains a registry mapping string identifiers to concrete
``BaseDataProvider`` subclasses, enabling dynamic provider lookup
by the CLI and API layers.
"""

from __future__ import annotations

import logging
from typing import Any

from cecil.core.providers.base import BaseDataProvider
from cecil.core.providers.mock import MockDataProvider


logger = logging.getLogger(__name__)

PROVIDER_REGISTRY: dict[str, type[BaseDataProvider]] = {
    "mock": MockDataProvider,
}


def register_provider(provider_id: str, cls: type[BaseDataProvider]) -> None:
    """Register a provider class under the given identifier.

    Args:
        provider_id: Short string key (e.g. ``"local_file"``).
        cls: A concrete ``BaseDataProvider`` subclass.

    Raises:
        ValueError: If *provider_id* is already registered.
    """
    if provider_id in PROVIDER_REGISTRY:
        raise ValueError(f"Provider already registered: {provider_id}")
    PROVIDER_REGISTRY[provider_id] = cls
    logger.info("Provider registered", extra={"provider_id": provider_id})


def get_provider(provider_id: str, **kwargs: Any) -> BaseDataProvider:
    """Instantiate a provider by its registered identifier.

    Args:
        provider_id: The key used when registering the provider.
        **kwargs: Arguments forwarded to the provider constructor.

    Returns:
        An instance of the requested provider.

    Raises:
        ValueError: If *provider_id* is not found in the registry.
    """
    cls = PROVIDER_REGISTRY.get(provider_id)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider_id}")
    return cls(**kwargs)


def list_providers() -> list[str]:
    """Return the identifiers of all registered providers.

    Returns:
        A sorted list of provider identifier strings.
    """
    return sorted(PROVIDER_REGISTRY)
