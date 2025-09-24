"""Payment-specific API client extensions."""

from typing import Any, Dict, List, Optional
from libs.http_client import BillingAPIClient


class PaymentAPIClient(BillingAPIClient):
    """Extended API client with payment-specific methods."""
    
    def get_statements_admin(self, month: str, uuid: str) -> Dict[str, Any]:
        """Get billing statements using admin API."""
        return self.get("billing/admin/statements", params={
            "uuid": uuid,
            "month": month
        })
    
    def get_statements_console(self, month: str, uuid: str) -> Dict[str, Any]:
        """Get billing statements using console API."""
        return self.get("billing/console/statements", params={
            "uuid": uuid,
            "month": month
        })
    
    def change_status(self, month: str, payment_group_id: str, target_status: str) -> Dict[str, Any]:
        """Change payment status."""
        return self.put(f"billing/payment/{payment_group_id}/status", json={
            "month": month,
            "status": target_status
        })
    
    def cancel_payment(self, month: str, payment_group_id: str) -> Dict[str, Any]:
        """Cancel a payment."""
        return self.delete(f"billing/payment/{payment_group_id}", params={
            "month": month
        })
    
    def make_payment(self, month: str, payment_group_id: str, uuid: str) -> Dict[str, Any]:
        """Make a payment."""
        return self.post("billing/payment/make", json={
            "month": month,
            "paymentGroupId": payment_group_id,
            "uuid": uuid
        })
    
    def get_unpaid_statements(self, month: str, uuid: str) -> Dict[str, Any]:
        """Get unpaid statements."""
        return self.get("billing/unpaid", params={
            "month": month,
            "uuid": uuid
        })
    
    def create_payment(self, payment_group_id: str, amount: float, payment_method: str) -> Dict[str, Any]:
        """Create a payment record."""
        return self.post("billing/payment", json={
            "paymentGroupId": payment_group_id,
            "amount": amount,
            "paymentMethod": payment_method
        })
    
    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """Get payment details."""
        return self.get(f"billing/payment/{payment_id}")
    
    def process_refund(self, payment_id: str, amount: float, reason: Optional[str] = None) -> Dict[str, Any]:
        """Process a refund."""
        data = {
            "paymentId": payment_id,
            "amount": amount
        }
        if reason:
            data["reason"] = reason
        return self.post("billing/refund", json=data)
    
    def get_payment_history(self, payment_group_id: Optional[str] = None, 
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None,
                          **kwargs) -> List[Dict[str, Any]]:
        """Get payment history."""
        params = {}
        if payment_group_id:
            params["paymentGroupId"] = payment_group_id
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        params.update(kwargs)
        
        response = self.get("billing/payment/history", params=params)
        return response.get("payments", [])
    
    def retry_payment(self, payment_id: str, retry_count: int = 1) -> Dict[str, Any]:
        """Retry a failed payment."""
        return self.post(f"billing/payment/{payment_id}/retry", json={
            "retryCount": retry_count
        })
    
    def batch_process_payments(self, payment_ids: List[str], action: str = "process") -> Dict[str, Any]:
        """Batch process multiple payments."""
        return self.post("billing/payment/batch", json={
            "paymentIds": payment_ids,
            "action": action
        })
    
    def process_batch_payments(self, payment_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process batch payments."""
        return self.post("billing/payment/batch", json={
            "requests": payment_requests
        })
