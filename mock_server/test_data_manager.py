"""Test data management with UUID-based isolation."""

from __future__ import annotations

import threading
from collections import defaultdict


class TestDataManager:
    """Manages test data with UUID-based isolation."""

    def __init__(self):
        self._lock = threading.Lock()
        # UUID-based data stores
        self.metering_data = defaultdict(dict)
        self.batch_jobs = defaultdict(dict)
        self.billing_data = defaultdict(dict)
        self.credit_data = defaultdict(dict)
        self.payments = defaultdict(dict)
        self.contracts = defaultdict(dict)
        self.meters = defaultdict(dict)
        self.bills = defaultdict(dict)
        self.cache = defaultdict(dict)
        self.adjustments = defaultdict(dict)

    def get_store(self, store_name: str, uuid: str) -> dict:
        """Get UUID-specific data store."""
        with self._lock:
            store = getattr(self, store_name, None)
            if store is None:
                raise ValueError(f"Unknown store: {store_name}")
            return store[uuid]

    def clear_uuid_data(self, uuid: str) -> None:
        """Clear all data for a specific UUID."""
        with self._lock:
            for store_name in [
                "metering_data",
                "batch_jobs",
                "billing_data",
                "credit_data",
                "payments",
                "contracts",
                "meters",
                "bills",
                "cache",
                "adjustments",
            ]:
                store = getattr(self, store_name, None)
                if store and uuid in store:
                    del store[uuid]

    def clear_all_data(self) -> None:
        """Clear all data for all UUIDs."""
        with self._lock:
            for store_name in [
                "metering_data",
                "batch_jobs",
                "billing_data",
                "credit_data",
                "payments",
                "contracts",
                "meters",
                "bills",
                "cache",
                "adjustments",
            ]:
                store = getattr(self, store_name, None)
                if store:
                    store.clear()

    def get_metering_data(self, uuid: str) -> dict:
        """Get metering data for UUID."""
        return self.get_store("metering_data", uuid)

    def get_batch_jobs(self, uuid: str) -> dict:
        """Get batch jobs for UUID."""
        return self.get_store("batch_jobs", uuid)

    def get_billing_data(self, uuid: str) -> dict:
        """Get billing data for UUID."""
        return self.get_store("billing_data", uuid)

    def get_credit_data(self, uuid: str) -> dict:
        """Get credit data for UUID."""
        return self.get_store("credit_data", uuid)

    def get_payments(self, uuid: str) -> dict:
        """Get payments for UUID."""
        return self.get_store("payments", uuid)

    def get_contracts(self, uuid: str) -> dict:
        """Get contracts for UUID."""
        return self.get_store("contracts", uuid)


# Global instance
_data_manager = TestDataManager()


def get_data_manager() -> TestDataManager:
    """Get the global data manager instance."""
    return _data_manager
