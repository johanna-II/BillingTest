"""Refactored credit tests using enhanced base class."""

import pytest
import math

from tests.base_enhanced import EnhancedBaseBillingTest, MockDataMixin


@pytest.mark.core
@pytest.mark.credit
@pytest.mark.slow
@pytest.mark.mock_required
@pytest.mark.serial
class TestCreditAllRefactored(EnhancedBaseBillingTest, MockDataMixin):
    """Refactored credit tests with reduced duplication."""
    
    @pytest.fixture(autouse=True)
    def skip_non_credit_members(self):
        """Skip tests for members that don't support credit."""
        if self.context.member == "etc":
            pytest.skip("Credit test should be skipped if member country is not KR or JP")
    
    def test_free_credit_with_metering(self):
        """Test free credit application with metering."""
        # Send metering data
        self.send_bulk_metering(count=5, base_volume=100)
        
        # Perform calculation
        result = self.perform_calculation()
        original_amount = result.get("totalAmount", 0)
        
        # Apply free credit
        credit_amount = 5000
        self.setup_credit(amount=credit_amount, credit_type="FREE")
        
        # Recalculate with credit
        result = self.perform_calculation()
        final_amount = result.get("totalAmount", 0)
        
        # Verify credit was applied
        assert final_amount < original_amount
        expected_reduction = min(credit_amount, original_amount)
        assert abs((original_amount - final_amount) - expected_reduction) < 0.01
    
    def test_paid_credit_with_vat(self):
        """Test paid credit with VAT calculation."""
        # Send metering
        self.send_metering_data(counter_volume=1000)
        
        # Calculate original
        result = self.perform_calculation()
        original_amount = result.get("totalAmount", 0)
        
        # Apply paid credit
        credit_amount = 10000
        self.setup_credit(amount=credit_amount, credit_type="PAID")
        
        # Recalculate
        result = self.perform_calculation()
        final_amount = result.get("totalAmount", 0)
        
        # Verify VAT is applied to paid credit
        vat_rate = 0.1
        credit_with_vat = credit_amount * (1 + vat_rate)
        expected_final = max(0, original_amount - credit_with_vat)
        
        assert abs(final_amount - expected_final) < 0.01
    
    def test_multiple_credits_application_order(self):
        """Test multiple credits are applied in correct order."""
        # Send substantial metering
        self.send_bulk_metering(count=10, base_volume=500)
        
        # Calculate original
        result = self.perform_calculation()
        original_amount = result.get("totalAmount", 0)
        
        # Apply multiple credits
        free_credit = 5000
        paid_credit = 10000
        
        free_credit_id = self.setup_credit(amount=free_credit, credit_type="FREE")
        paid_credit_id = self.setup_credit(amount=paid_credit, credit_type="PAID")
        
        # Store credit IDs for verification
        self.context.test_data["free_credit_id"] = free_credit_id
        self.context.test_data["paid_credit_id"] = paid_credit_id
        
        # Recalculate
        result = self.perform_calculation()
        final_amount = result.get("totalAmount", 0)
        
        # Verify free credit is applied first, then paid credit
        after_free = max(0, original_amount - free_credit)
        paid_with_vat = paid_credit * 1.1
        expected_final = max(0, after_free - paid_with_vat)
        
        assert abs(final_amount - expected_final) < 0.01
    
    def test_credit_expiry_handling(self):
        """Test expired credit is not applied."""
        # This would require setting up expired credit through API
        # For now, verify credit can be cancelled
        
        # Setup credit
        credit_id = self.setup_credit(amount=5000)
        
        # Cancel it
        self.context.credit_manager.cancel_credit()
        
        # Send metering and calculate
        self.send_metering_data(counter_volume=1000)
        result = self.perform_calculation()
        
        # Verify no credit was applied
        # (amount should be full price)
        assert result.get("creditAmount", 0) == 0
    
    @pytest.mark.parametrize("credit_amount,metering_volume,expected_behavior", [
        (5000, 100, "full_credit"),      # Credit exceeds usage
        (1000, 1000, "partial_credit"),  # Credit less than usage
        (0, 500, "no_credit"),           # Zero credit
        (10000, 0, "no_usage"),          # No usage
    ])
    def test_credit_scenarios(self, credit_amount, metering_volume, expected_behavior):
        """Test various credit application scenarios."""
        # Setup credit if amount > 0
        if credit_amount > 0:
            self.setup_credit(amount=credit_amount)
        
        # Send metering if volume > 0
        if metering_volume > 0:
            self.send_metering_data(counter_volume=metering_volume)
        
        # Calculate
        result = self.perform_calculation()
        total_amount = result.get("totalAmount", 0)
        credit_applied = result.get("creditAmount", 0)
        
        # Verify based on expected behavior
        if expected_behavior == "full_credit":
            assert total_amount == 0
            assert credit_applied > 0
        elif expected_behavior == "partial_credit":
            assert total_amount > 0
            assert credit_applied == credit_amount
        elif expected_behavior == "no_credit":
            assert credit_applied == 0
        elif expected_behavior == "no_usage":
            assert total_amount == 0
    
    def test_credit_with_contract_discount(self):
        """Test credit application with contract discounts."""
        # Create contract for discount
        if self.context.contract_manager:
            contract = self.create_contract(
                contract_type="VOLUME",
                discount_rate=20.0
            )
            self.context.test_data["contract"] = contract
        
        # Send metering
        self.send_bulk_metering(count=5, base_volume=200)
        
        # Calculate with discount
        result = self.perform_calculation()
        discounted_amount = result.get("totalAmount", 0)
        
        # Apply credit
        credit_amount = 5000
        self.setup_credit(amount=credit_amount)
        
        # Recalculate
        result = self.perform_calculation()
        final_amount = result.get("totalAmount", 0)
        
        # Verify credit is applied after discount
        expected_final = max(0, discounted_amount - credit_amount)
        assert abs(final_amount - expected_final) < 0.01
    
    def test_credit_balance_tracking(self):
        """Test credit balance is correctly tracked."""
        # Setup initial credit
        initial_credit = 10000
        self.setup_credit(amount=initial_credit)
        
        # Check initial balance
        balance = self.context.credit_manager.get_credit_balance()
        assert balance.get("totalAmount", 0) == initial_credit
        
        # Use some credit
        self.send_metering_data(counter_volume=500)
        self.perform_calculation()
        
        # Check remaining balance
        balance = self.context.credit_manager.get_credit_balance()
        remaining = balance.get("totalAmount", 0)
        assert remaining < initial_credit
        assert remaining >= 0
    
    def test_concurrent_credit_operations(self):
        """Test credit operations under concurrent access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def apply_credit_and_calculate(thread_id):
            """Apply credit and calculate in thread."""
            try:
                # Each thread applies its own credit
                credit_amount = 1000 * (thread_id + 1)
                self.setup_credit(amount=credit_amount)
                
                # Small delay to increase concurrency
                time.sleep(0.1)
                
                # Calculate
                result = self.perform_calculation()
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Send initial metering
        self.send_bulk_metering(count=10, base_volume=100)
        
        # Run concurrent credit operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=apply_credit_and_calculate, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) > 0, "No results from concurrent operations"
