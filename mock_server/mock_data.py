"""Mock data templates for billing API responses."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

# Metering data templates
COMPUTE_METERING_TEMPLATE = {
    "compute.g2.t4.c8m64": {
        "productCode": "COMPUTE",
        "productType": "GPU_INSTANCE",
        "pricePerUnit": 166.67,  # per hour
        "unit": "HOURS",
        "description": "GPU Instance g2.t4.c8m64",
    },
    "volume.ssd": {
        "productCode": "STORAGE",
        "productType": "BLOCK_STORAGE",
        "pricePerUnit": 0.0001,  # per GB per hour
        "unit": "GB_HOURS",
        "description": "SSD Block Storage",
    },
    "bandwidth.public": {
        "productCode": "NETWORK",
        "productType": "BANDWIDTH",
        "pricePerUnit": 0.01,  # per GB
        "unit": "GB",
        "description": "Public Bandwidth",
    },
}


# Billing detail templates
def generate_billing_detail(
    uuid: str, month: str, has_discount: bool = False
) -> dict[str, Any]:
    """Generate realistic billing detail data."""
    # Calculate base amounts
    compute_amount = 120000  # 720 hours * 166.67
    storage_amount = 30000
    network_amount = 5000

    subtotal = compute_amount + storage_amount + network_amount
    discount = subtotal * 0.1 if has_discount else 0
    charge = subtotal - discount
    vat = int(charge * 0.1)
    total = charge + vat

    return {
        "uuid": uuid,
        "month": month,
        "currency": "KRW",
        "totalAmount": total,
        "charge": charge,
        "vat": vat,
        "discount": discount,
        "totalCredit": 0,  # Will be updated based on actual credits
        "statements": [
            {
                "productCode": "COMPUTE",
                "productName": "Compute",
                "amount": compute_amount,
                "discount": compute_amount * 0.1 if has_discount else 0,
                "details": [
                    {
                        "meteringType": "compute.g2.t4.c8m64",
                        "unit": "HOURS",
                        "quantity": 720,
                        "unitPrice": 166.67,
                        "amount": compute_amount,
                    }
                ],
            },
            {
                "productCode": "STORAGE",
                "productName": "Storage",
                "amount": storage_amount,
                "discount": storage_amount * 0.1 if has_discount else 0,
                "details": [
                    {
                        "meteringType": "volume.ssd",
                        "unit": "GB_HOURS",
                        "quantity": 300000,  # 300GB * 1000 hours
                        "unitPrice": 0.0001,
                        "amount": storage_amount,
                    }
                ],
            },
            {
                "productCode": "NETWORK",
                "productName": "Network",
                "amount": network_amount,
                "discount": 0,
                "details": [
                    {
                        "meteringType": "bandwidth.public",
                        "unit": "GB",
                        "quantity": 500,
                        "unitPrice": 0.01,
                        "amount": network_amount,
                    }
                ],
            },
        ],
    }


# Credit data templates
def generate_credit_data(uuid: str, credit_amount: int = 0) -> dict[str, Any]:
    """Generate credit data for user."""
    # Start with no usage for testing
    used_amount = 0

    return {
        "uuid": uuid,
        "totalAmount": credit_amount,
        "usedAmount": used_amount,
        "restAmount": credit_amount,
        "credits": (
            [
                {
                    "creditId": f"CRD-{uuid[:8]}",
                    "campaignId": "CAMPAIGN-001",
                    "creditCode": "FREE_CREDIT",
                    "amount": credit_amount,
                    "usedAmount": used_amount,
                    "restAmount": credit_amount,
                    "status": "ACTIVE",
                    "expireDate": (datetime.now() + timedelta(days=365)).isoformat(),
                    "createdAt": datetime.now().isoformat(),
                }
            ]
            if credit_amount > 0
            else []
        ),
    }


# Contract data templates
def generate_contract_data(contract_type: str = "REGULAR") -> dict[str, Any]:
    """Generate contract data."""
    discount_rate = 0.1 if contract_type == "COMMITMENT" else 0

    return {
        "contractType": contract_type,
        "status": "ACTIVE",
        "discountRate": discount_rate,
        "startDate": datetime.now().isoformat(),
        "endDate": (datetime.now() + timedelta(days=365)).isoformat(),
        "details": {
            "minimumCommitment": 1000000 if contract_type == "COMMITMENT" else 0,
            "currentUsage": 0,
            "products": ["COMPUTE", "STORAGE", "NETWORK"],
        },
    }


# Batch job templates
def generate_batch_progress(job_code: str, current_progress: int = 0) -> dict[str, Any]:
    """Generate batch job progress data."""
    total = 100
    is_completed = current_progress >= total

    return {
        "batchJobCode": job_code,
        "status": "COMPLETED" if is_completed else "RUNNING",
        "completedCount": min(current_progress, total),
        "totalCount": total,
        "progress": min(current_progress / total * 100, 100),
        "startTime": datetime.now().isoformat(),
        "endTime": datetime.now().isoformat() if is_completed else None,
        "message": (
            "Batch job completed successfully"
            if is_completed
            else f"Processing... {current_progress}/{total}"
        ),
    }


# Payment data templates
def generate_payment_data(
    uuid: str, amount: int, status: str = "PAID"
) -> dict[str, Any]:
    """Generate payment data."""
    return {
        "paymentId": f"PAY-{uuid[:8]}",
        "uuid": uuid,
        "amount": amount,
        "status": status,
        "paymentMethod": "CREDIT_CARD",
        "paymentDate": datetime.now().isoformat() if status == "PAID" else None,
        "dueDate": (datetime.now() + timedelta(days=30)).isoformat(),
        "details": {"cardNumber": "**** **** **** 1234", "cardType": "VISA"},
    }


# Adjustment data templates
def generate_adjustment_data(
    uuid: str, adjustment_type: str, amount: int
) -> dict[str, Any]:
    """Generate adjustment data."""
    return {
        "adjustmentId": f"ADJ-{uuid[:8]}",
        "uuid": uuid,
        "type": adjustment_type,
        "amount": amount,
        "reason": f"{adjustment_type} adjustment",
        "status": "APPLIED",
        "appliedDate": datetime.now().isoformat(),
        "details": {
            "originalAmount": amount * 1.1,
            "adjustedAmount": amount,
            "adjustmentRate": 0.1,
        },
    }
