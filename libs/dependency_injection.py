"""Dependency injection container for billing system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from .constants import DEFAULT_RETRY_COUNT, DEFAULT_TIMEOUT
from .http_client import BillingAPIClient

if TYPE_CHECKING:
    from collections.abc import Callable

    from .Batch import BatchManager
    from .Contract import ContractManager
    from .Credit import CreditManager
    from .Metering import MeteringManager
    from .Payments import PaymentManager

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[type, Callable[[], Any]] = {}
        self._singletons: dict[type, Any] = {}

    def register(
        self, service_type: type[T], factory: Callable[[], T], singleton: bool = False
    ) -> None:
        """Register a service with its factory function.

        Args:
            service_type: The type/interface to register
            factory: Factory function that creates the service
            singleton: If True, only one instance will be created
        """
        self._services[service_type] = factory
        if singleton:
            # Mark as singleton but don't create yet (lazy loading)
            self._singletons[service_type] = None

    def get(self, service_type: type[T]) -> T:
        """Get a service instance.

        Args:
            service_type: The type/interface to retrieve

        Returns:
            Instance of the requested service

        Raises:
            ValueError: If service is not registered
        """
        if service_type not in self._services:
            msg = f"Service {service_type} not registered"
            raise ValueError(msg)

        # Check if it's a singleton
        if service_type in self._singletons:
            if self._singletons[service_type] is None:
                # Create singleton instance
                self._singletons[service_type] = self._services[service_type]()
            return self._singletons[service_type]  # type: ignore[no-any-return]

        # Create new instance
        return self._services[service_type]()  # type: ignore[no-any-return]

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()


# Global container instance
_container = DIContainer()


def get_container() -> DIContainer:
    """Get the global DI container."""
    return _container


# Service factories
def create_http_client(
    base_url: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retry_count: int = DEFAULT_RETRY_COUNT,
) -> BillingAPIClient:
    """Factory for creating HTTP client."""
    from config import url

    if base_url is None:
        # Get from config
        base_url = getattr(url, "BASE_URL", "http://localhost:5000")

    from .http_client import RetryConfig

    retry_config = RetryConfig(total=retry_count) if retry_count else None
    return BillingAPIClient(base_url, timeout=timeout, retry_config=retry_config)


def create_payment_manager(month: str, uuid: str) -> PaymentManager:
    """Factory for creating PaymentManager with injected dependencies."""
    from .Payments import PaymentManager as PM

    class DIPaymentManager(PM):
        """PaymentManager with dependency injection."""

        def __init__(self, month: str, uuid: str) -> None:
            # PaymentAPIClient will get injected directly from container
            super().__init__(month, uuid)

    return DIPaymentManager(month, uuid)


def create_metering_manager(month: str) -> MeteringManager:
    """Factory for creating MeteringManager with injected dependencies."""
    from .Metering import MeteringManager as MM

    class DIMeteringManager(MM):
        """MeteringManager with dependency injection."""

        def __init__(self, month: str) -> None:
            super().__init__(month)
            # Inject HTTP client from container
            self._client = get_container().get(BillingAPIClient)

    return DIMeteringManager(month)


def create_batch_manager(month: str) -> BatchManager:
    """Factory for creating BatchManager with injected dependencies."""
    from .Batch import BatchManager as BM

    class DIBatchManager(BM):
        """BatchManager with dependency injection."""

        def __init__(self, month: str) -> None:
            super().__init__(month)
            # Inject HTTP client from container
            self._client = get_container().get(BillingAPIClient)

    return DIBatchManager(month)


def create_credit_manager(uuid: str) -> CreditManager:
    """Factory for creating CreditManager with injected dependencies."""
    from .Credit import CreditManager as CM

    class DICreditManager(CM):
        """CreditManager with dependency injection."""

        def __init__(self, uuid: str) -> None:
            super().__init__(uuid)
            # Inject HTTP client from container
            self._client = get_container().get(BillingAPIClient)

    return DICreditManager(uuid)


def create_contract_manager(month: str, billing_group_id: str) -> ContractManager:
    """Factory for creating ContractManager with injected dependencies."""
    from .Contract import ContractManager as CM

    class DIContractManager(CM):
        """ContractManager with dependency injection."""

        def __init__(self, month: str, billing_group_id: str) -> None:
            super().__init__(month, billing_group_id)
            # Inject HTTP client from container
            self._client = get_container().get(BillingAPIClient)

    return DIContractManager(month, billing_group_id)


# Configuration function
def configure_dependencies(
    base_url: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retry_count: int = DEFAULT_RETRY_COUNT,
    use_mock: bool = False,
) -> None:
    """Configure the dependency injection container.

    Args:
        base_url: Base URL for API
        timeout: Request timeout
        retry_count: Number of retries
        use_mock: If True, use mock implementations
    """
    container = get_container()
    container.clear()

    if use_mock:
        # Register mock implementations
        from unittest.mock import Mock

        def create_mock_client() -> BillingAPIClient:
            mock = Mock(spec=BillingAPIClient)
            mock.get.return_value = {"header": {"isSuccessful": True}}
            mock.post.return_value = {"header": {"isSuccessful": True}}
            mock.put.return_value = {"header": {"isSuccessful": True}}
            mock.delete.return_value = {"header": {"isSuccessful": True}}
            return mock

        container.register(BillingAPIClient, create_mock_client, singleton=True)
    else:
        # Register real implementations
        container.register(
            BillingAPIClient,
            lambda: create_http_client(base_url, timeout, retry_count),
            singleton=True,
        )


# Decorators for dependency injection
def inject(**dependencies):
    """Decorator to inject dependencies into a class or function.

    Example:
        @inject(client=BillingAPIClient)
        class MyService:
            def __init__(self, client):
                self.client = client
    """

    def decorator(cls_or_func):
        if isinstance(cls_or_func, type):
            # Class decorator
            original_init = cls_or_func.__init__  # type: ignore[misc]

            def new_init(self, *args, **kwargs) -> None:
                # Inject dependencies
                for name, service_type in dependencies.items():
                    if name not in kwargs:
                        kwargs[name] = get_container().get(service_type)
                original_init(self, *args, **kwargs)

            cls_or_func.__init__ = new_init  # type: ignore[misc]
            return cls_or_func

        # Function decorator
        def wrapper(*args, **kwargs):
            # Inject dependencies
            for name, service_type in dependencies.items():
                if name not in kwargs:
                    kwargs[name] = get_container().get(service_type)
            return cls_or_func(*args, **kwargs)

        return wrapper

    return decorator
