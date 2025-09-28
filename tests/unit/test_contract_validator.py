"""Unit tests for ContractValidator - pure contract validation and calculation logic."""

from decimal import Decimal

import pytest

from libs.contract_validator import ContractValidator
from libs.exceptions import ValidationException


class TestContractValidator:
    """Unit tests for contract validation and calculation logic."""

    def test_validate_month_format_valid(self):
        """Test valid month formats."""
        # Should not raise
        ContractValidator.validate_month_format("2024-01")
        ContractValidator.validate_month_format("2024-12")
        ContractValidator.validate_month_format("2025-06")

    def test_validate_month_format_invalid_format(self):
        """Test invalid month formats."""
        invalid_formats = [
            "2024",  # Missing month
            "01-2024",  # Wrong order
            "2024-1",  # Single digit month
            "2024-13",  # Invalid month
            "2024-00",  # Zero month
            "24-01",  # 2-digit year
            "2024/01",  # Wrong separator
            "202401",  # No separator
            "",  # Empty
            "abc",  # Non-numeric
        ]

        for invalid in invalid_formats:
            with pytest.raises(ValidationException, match="Invalid month"):
                ContractValidator.validate_month_format(invalid)

    def test_validate_contract_id_valid(self):
        """Test valid contract IDs."""
        # Should not raise
        ContractValidator.validate_contract_id("contract-123")
        ContractValidator.validate_contract_id("CONTRACT_456")
        ContractValidator.validate_contract_id("abc123")
        ContractValidator.validate_contract_id("A-B_C-123")

    def test_validate_contract_id_invalid(self):
        """Test invalid contract IDs."""
        with pytest.raises(ValidationException, match="cannot be empty"):
            ContractValidator.validate_contract_id("")

        with pytest.raises(ValidationException, match="Invalid contract ID format"):
            ContractValidator.validate_contract_id("contract@123")  # Special char

        with pytest.raises(ValidationException, match="Invalid contract ID format"):
            ContractValidator.validate_contract_id("contract 123")  # Space

    def test_validate_billing_group_id(self):
        """Test billing group ID validation."""
        # Valid
        ContractValidator.validate_billing_group_id("bg-123")
        ContractValidator.validate_billing_group_id("billing_group_456")

        # Invalid
        with pytest.raises(ValidationException, match="cannot be empty"):
            ContractValidator.validate_billing_group_id("")

        with pytest.raises(ValidationException, match="cannot be empty"):
            ContractValidator.validate_billing_group_id("   ")

    def test_calculate_discount(self):
        """Test discount calculation."""
        # Normal discount
        amount, rate = ContractValidator.calculate_discount(1000, 800)
        assert amount == Decimal("200.00")
        assert rate == Decimal("20.00")

        # No discount
        amount, rate = ContractValidator.calculate_discount(1000, 1000)
        assert amount == Decimal("0.00")
        assert rate == Decimal("0.00")

        # 100% discount
        amount, rate = ContractValidator.calculate_discount(1000, 0)
        assert amount == Decimal("1000.00")
        assert rate == Decimal("100.00")

        # Zero original price
        amount, rate = ContractValidator.calculate_discount(0, 0)
        assert amount == Decimal("0.00")
        assert rate == Decimal("0.00")

    def test_validate_price(self):
        """Test price validation."""
        # Valid prices
        ContractValidator.validate_price(100)
        ContractValidator.validate_price(0)
        ContractValidator.validate_price(999999999)
        ContractValidator.validate_price(Decimal("123.45"))

        # Invalid prices
        with pytest.raises(ValidationException, match="cannot be negative"):
            ContractValidator.validate_price(-100)

        with pytest.raises(ValidationException, match="cannot exceed"):
            ContractValidator.validate_price(1000000001)

    def test_validate_discount_rate(self):
        """Test discount rate validation."""
        # Valid rates
        ContractValidator.validate_discount_rate(Decimal("0"))
        ContractValidator.validate_discount_rate(Decimal("50"))
        ContractValidator.validate_discount_rate(Decimal("100"))

        # Invalid rates
        with pytest.raises(ValidationException, match="cannot be negative"):
            ContractValidator.validate_discount_rate(Decimal("-10"))

        with pytest.raises(ValidationException, match="cannot exceed 100%"):
            ContractValidator.validate_discount_rate(Decimal("150"))

    def test_calculate_total_discount(self):
        """Test total discount calculation from multiple counters."""
        counter_prices = {
            "counter1": {"original_price": 1000, "price": 800},
            "counter2": {"original_price": 500, "price": 450},
            "counter3": {"original_price": 200, "price": 200},
        }

        total_orig, total_disc, total_amount = ContractValidator.calculate_total_discount(
            counter_prices
        )

        assert total_orig == Decimal("1700.00")
        assert total_disc == Decimal("1450.00")
        assert total_amount == Decimal("250.00")

    def test_calculate_total_discount_with_errors(self):
        """Test total discount calculation skips errors."""
        counter_prices = {
            "counter1": {"original_price": 1000, "price": 800},
            "counter2": {"error": "Failed to get price"},
            "counter3": {"original_price": 500, "price": 400},
        }

        total_orig, total_disc, total_amount = ContractValidator.calculate_total_discount(
            counter_prices
        )

        assert total_orig == Decimal("1500.00")
        assert total_disc == Decimal("1200.00")
        assert total_amount == Decimal("300.00")

    def test_validate_counter_name(self):
        """Test counter name validation."""
        # Valid names
        ContractValidator.validate_counter_name("compute.instance")
        ContractValidator.validate_counter_name("storage_block")
        ContractValidator.validate_counter_name("network-bandwidth")
        ContractValidator.validate_counter_name("service.api.calls")

        # Invalid names
        with pytest.raises(ValidationException, match="cannot be empty"):
            ContractValidator.validate_counter_name("")

        with pytest.raises(ValidationException, match="Invalid counter name format"):
            ContractValidator.validate_counter_name("counter@special")

        with pytest.raises(ValidationException, match="Invalid counter name format"):
            ContractValidator.validate_counter_name("counter name")

    def test_is_default_contract(self):
        """Test default contract detection."""
        # True cases
        assert ContractValidator.is_default_contract("Y")
        assert ContractValidator.is_default_contract("yes")
        assert ContractValidator.is_default_contract("YES")
        assert ContractValidator.is_default_contract("true")
        assert ContractValidator.is_default_contract("1")

        # False cases
        assert not ContractValidator.is_default_contract("N")
        assert not ContractValidator.is_default_contract("no")
        assert not ContractValidator.is_default_contract("false")
        assert not ContractValidator.is_default_contract("0")
        assert not ContractValidator.is_default_contract("")

    def test_format_contract_name(self):
        """Test contract name formatting."""
        assert ContractValidator.format_contract_name("Test Contract") == "Test Contract"
        assert ContractValidator.format_contract_name("  Spaces  ") == "Spaces"
        assert ContractValidator.format_contract_name("") == "billing group default"
        assert ContractValidator.format_contract_name(None) == "billing group default"
        assert ContractValidator.format_contract_name("   ") == "billing group default"

    def test_calculate_base_fee_impact(self):
        """Test base fee impact calculation."""
        # Monthly fee for a year
        impact = ContractValidator.calculate_base_fee_impact(Decimal("100"), 12)
        assert impact == Decimal("1200.00")

        # Monthly fee for 6 months
        impact = ContractValidator.calculate_base_fee_impact(Decimal("250.50"), 6)
        assert impact == Decimal("1503.00")

        # Zero fee
        impact = ContractValidator.calculate_base_fee_impact(Decimal("0"), 12)
        assert impact == Decimal("0.00")

    def test_compare_contracts(self):
        """Test contract comparison."""
        contract1_fees = {
            "compute": Decimal("100"),
            "storage": Decimal("50"),
            "network": Decimal("30"),
        }

        contract2_fees = {
            "compute": Decimal("90"),  # 10% cheaper
            "storage": Decimal("60"),  # 20% more expensive
            "network": Decimal("30"),  # Same price
            "monitoring": Decimal("10"),  # New service
        }

        comparison = ContractValidator.compare_contracts(contract1_fees, contract2_fees)

        # Check individual comparisons
        assert comparison["compute"]["difference"] == Decimal("-10")
        assert comparison["compute"]["percentage_change"] == Decimal("-10.00")

        assert comparison["storage"]["difference"] == Decimal("10")
        assert comparison["storage"]["percentage_change"] == Decimal("20.00")

        assert comparison["network"]["difference"] == Decimal("0")
        assert comparison["network"]["percentage_change"] == Decimal("0.00")

        assert comparison["monitoring"]["contract1_fee"] == Decimal("0")
        assert comparison["monitoring"]["contract2_fee"] == Decimal("10")
        assert comparison["monitoring"]["difference"] == Decimal("10")

        # Check total
        assert comparison["total_difference"] == Decimal("10")  # -10 + 10 + 0 + 10
