"""Mock Billing API Server for testing."""

from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any

from flask import Flask, jsonify, make_response, request
from flask_caching import Cache
from flask_cors import CORS

from .mock_data import (
    generate_batch_progress,
    generate_billing_detail,
    generate_contract_data,
    generate_credit_data,
)
from .test_data_manager import get_data_manager

try:
    from .openapi_handler import get_openapi_handler, setup_openapi_handler

    OPENAPI_AVAILABLE = True
except ImportError:
    OPENAPI_AVAILABLE = False
    setup_openapi_handler = None
    get_openapi_handler = lambda: None

app = Flask(__name__)
CORS(app)

# Configure caching for better performance
cache = Cache(
    app,
    config={
        "CACHE_TYPE": "simple",
        "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minute cache
        "CACHE_THRESHOLD": 1000,  # Cache up to 1000 items
    },
)

# Register Swagger UI
try:
    import os
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    from swagger_ui import swagger_bp

    app.register_blueprint(swagger_bp, url_prefix="/docs")
    print("Swagger UI successfully registered at /docs")
except ImportError as e:
    print(f"Failed to import swagger_ui: {e}")
    import traceback

    traceback.print_exc()

# Thread lock for thread-safe operations
data_lock = threading.Lock()

# Performance optimization: disable Flask debug features
app.config["PROPAGATE_EXCEPTIONS"] = False
app.config["TRAP_HTTP_EXCEPTIONS"] = False
app.config["JSON_SORT_KEYS"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

# Get data manager instance
data_manager = get_data_manager()

# In-memory storage for batch jobs
batch_jobs = {}

# In-memory storage for adjustments
adjustments = {}

# In-memory storage for contracts
contracts = {}

# In-memory storage for billing data
billing_data = {}

# Initialize OpenAPI handler if available
if OPENAPI_AVAILABLE:
    spec_path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "openapi", "billing-api.yaml"
    )
    if os.path.exists(spec_path):
        try:
            setup_openapi_handler(spec_path)
            print(f"OpenAPI handler initialized with spec: {spec_path}")
        except Exception as e:
            import traceback

            print(f"Failed to initialize OpenAPI handler: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            OPENAPI_AVAILABLE = False


def create_success_response(data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create standard success response."""
    return {
        "header": {"isSuccessful": True, "resultCode": 0, "resultMessage": "SUCCESS"},
        **(data or {}),
    }


def create_error_response(message: str, code: int = -1) -> tuple[dict[str, Any], int]:
    """Create standard error response."""
    return {
        "header": {"isSuccessful": False, "resultCode": code, "resultMessage": message}
    }, 400


# Welcome page with links
@app.route("/", methods=["GET"])
def welcome():
    """Welcome page with API documentation links."""
    host = request.host_url.rstrip("/")
    return f"""
    <html>
    <head>
        <title>Billing API Mock Server</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }}
            .links {{
                margin: 20px 0;
            }}
            .links a {{
                display: inline-block;
                margin: 10px 20px 10px 0;
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }}
            .links a:hover {{
                background-color: #0056b3;
            }}
            .info {{
                background-color: #e9ecef;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            code {{
                background-color: #f8f9fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Billing API Mock Server</h1>
            <p>Welcome to the Billing API Mock Server for testing and development.</p>
            
            <div class="info">
                <strong>Base URL:</strong> <code>{host}/api/v1</code>
            </div>
            
            <h2>📚 Documentation</h2>
            <div class="links">
                <a href="/docs">Swagger UI</a>
                <a href="/docs/openapi.json">OpenAPI JSON</a>
                <a href="/docs/openapi.yaml">OpenAPI YAML</a>
                <a href="/health">Health Check</a>
            </div>
            
            <h2>🔧 Available Endpoints</h2>
            <ul>
                <li><strong>Contracts:</strong> /api/v1/billing/contracts</li>
                <li><strong>Credits:</strong> /api/v1/billing/credits</li>
                <li><strong>Metering:</strong> /api/v1/billing/meters</li>
                <li><strong>Payments:</strong> /api/v1/billing/payments</li>
                <li><strong>Adjustments:</strong> /api/v1/billing/adjustments</li>
                <li><strong>Batch Jobs:</strong> /api/v1/billing/admin/batches</li>
            </ul>
            
            <h2>💡 Quick Start</h2>
            <p>To start using the API:</p>
            <ol>
                <li>Check the <a href="/docs">Swagger UI</a> for interactive API documentation</li>
                <li>Use the base URL <code>{host}/api/v1</code> for your API calls</li>
                <li>All endpoints return JSON responses with standard headers</li>
            </ol>
        </div>
    </body>
    </html>
    """


# Health check endpoint
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return create_success_response(
        {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    )


# Metering endpoints
@app.route("/billing/meters", methods=["POST"])
def create_metering():
    """Create metering data."""
    data = request.json
    test_uuid = request.headers.get("uuid", "default")

    # Get UUID-specific metering store
    metering_store = data_manager.get_metering_data(test_uuid)

    # Handle meterList format (what the actual client sends)
    if "meterList" in data:
        meter_ids = []
        for meter in data["meterList"]:
            meter_id = str(uuid.uuid4())
            metering_store[meter_id] = {
                "id": meter_id,
                "timestamp": datetime.now().isoformat(),
                "uuid": test_uuid,
                **meter,
            }
            meter_ids.append(meter_id)

        with open("mock_metering.log", "a") as f:
            f.write(
                f"Created {len(data['meterList'])} meters for UUID: {test_uuid}, total: {len(metering_store)}\n"
            )

        return jsonify(
            create_success_response(
                {
                    "message": f"Created {len(data['meterList'])} meters",
                    "meterIds": meter_ids,
                }
            )
        )
    # Handle single meter format
    meter_id = str(uuid.uuid4())
    metering_store[meter_id] = {
        "id": meter_id,
        "timestamp": datetime.now().isoformat(),
        "uuid": test_uuid,
        **data,
    }
    return jsonify(create_success_response({"meterId": meter_id}))


@app.route("/billing/meters/<meter_id>", methods=["GET"])
def get_metering(meter_id):
    """Get metering data."""
    test_uuid = request.headers.get("uuid", "default")
    metering_store = data_manager.get_metering_data(test_uuid)

    if meter_id not in metering_store:
        return create_error_response("Meter not found", 404)

    return jsonify(create_success_response({"meter": metering_store[meter_id]}))


# Batch job endpoints
@app.route("/billing/admin/batch", methods=["POST"])
def create_batch_job():
    """Create batch job."""
    data = request.json
    job_id = str(uuid.uuid4())

    batch_jobs[job_id] = {
        "batchJobCode": job_id,
        "status": "RUNNING",
        "completedCount": 0,
        "totalCount": 100,
        "createdAt": datetime.now().isoformat(),
    }

    return jsonify(create_success_response({"batchJobCode": job_id}))


@app.route("/billing/admin/batch/progress", methods=["GET"])
def get_batch_progress():
    """Get batch job progress."""
    # Simulate progress
    result_list = []
    for job_id, job in batch_jobs.items():
        if job_id not in batch_progress:
            batch_progress[job_id] = 0

        if job["status"] == "RUNNING":
            batch_progress[job_id] = min(batch_progress[job_id] + 20, 100)

        progress_data = generate_batch_progress(job_id, batch_progress[job_id])
        result_list.append(progress_data)

    return jsonify(create_success_response({"list": result_list}))


@app.route("/billing/admin/progress", methods=["GET"])
def get_calculation_progress():
    """Get calculation progress for batch jobs."""
    # Get query parameters
    month = request.args.get("month")
    uuid_param = request.args.get("uuid")

    # Check if we have a batch job for this combination
    job_key = f"{month}_{uuid_param}" if month and uuid_param else None

    # Always return completed status for mock
    result_list = [
        {
            "batchJobCode": "API_CALCULATE_USAGE_AND_PRICE",
            "progress": 100,
            "maxProgress": 100,
            "status": "COMPLETED",
        }
    ]

    # For compatibility with wait_for_completion method
    return jsonify(
        {
            "status": "COMPLETED",
            "list": result_list,
            "progress": 100,
            "maxProgress": 100,
        }
    )


# Credit endpoints
@app.route("/billing/credits/balance", methods=["GET"])
def get_credit_balance():
    """Get credit balance."""
    uuid_param = request.headers.get("uuid")

    # Return mock balance data
    balance_data = {
        "totalBalance": 1000.0,
        "availableBalance": 800.0,
        "pendingBalance": 200.0,
        "currency": "USD",
        "balances": [
            {"type": "FREE", "amount": 500.0, "expiryDate": "2024-12-31"},
            {"type": "PAID", "amount": 300.0, "expiryDate": "2024-12-31"},
        ],
    }

    return jsonify(create_success_response(balance_data))


@app.route("/billing/credits/history", methods=["GET"])
def get_credit_history():
    """Get credit history."""
    uuid_param = request.headers.get("uuid")
    balance_type = request.args.get("balancePriceTypeCode", "FREE")

    # Get user's credit data
    total_credit_amt = 0
    credit_data = data_manager.credit_data
    if uuid_param in credit_data:
        data = credit_data[uuid_param]
        # For history, return the remaining amount (not total given)
        # This matches the test expectation that fully used credits show 0 in history
        total_credit_amt = data.get("restAmount", 0)

    # Return mock credit history data
    return jsonify(
        create_success_response(
            {
                "totalCreditAmt": total_credit_amt,
                "balancePriceTypeCode": balance_type,
                "history": [],
            }
        )
    )


@app.route("/billing/admin/campaign/<campaign_id>/credits", methods=["POST"])
def grant_campaign_credit(campaign_id):
    """Grant credit through campaign."""
    data = request.json
    uuid_param = request.headers.get("uuid")

    # Store credit data
    credit_amount = data.get("creditList", [{}])[0].get("creditAmt", 0)
    credit_name = data.get("creditList", [{}])[0].get("creditName", "Campaign Credit")

    credit_data = data_manager.credit_data
    if uuid_param not in credit_data:
        credit_data[uuid_param] = {
            "grantAmount": 0,
            "useAmount": 0,
            "refundAmount": 0,
            "restAmount": 0,
        }

    # Add to granted amount and rest amount
    credit_data[uuid_param]["grantAmount"] += credit_amount
    credit_data[uuid_param]["restAmount"] += credit_amount

    return jsonify(
        create_success_response(
            {
                "campaignId": campaign_id,
                "creditAmount": credit_amount,
                "creditName": credit_name,
                "status": "SUCCESS",
            }
        )
    )


@app.route("/billing/coupons/<coupon_code>", methods=["POST"])
def apply_coupon_credit(coupon_code):
    """Apply coupon credit to user."""
    uuid_param = request.headers.get("uuid")

    # Default coupon amounts based on code pattern
    coupon_amounts = {
        "CAMPAIGN-001": 100000,  # Default test coupon
        "CAMPAIGN-002": 2000000,  # Large test coupon
    }

    # Get amount from coupon code or use default
    amount = coupon_amounts.get(coupon_code, 100000)

    # Initialize credit data if not exists
    with data_lock:
        if uuid_param not in credit_data:
            credit_data[uuid_param] = generate_credit_data(uuid_param, 0)

        # Update credit amounts
        current_total = credit_data[uuid_param]["totalAmount"]
        new_total = current_total + amount

        # Regenerate credit data with new amount
        credit_data[uuid_param] = generate_credit_data(uuid_param, new_total)

    return jsonify(
        create_success_response(
            {"creditId": str(uuid.uuid4()), "couponCode": coupon_code, "amount": amount}
        )
    )


@app.route("/billing/admin/campaign/<campaign_id>/credits", methods=["POST"])
def grant_paid_credit(campaign_id):
    """Grant paid credit to user."""
    data = request.json
    uuid_param = request.headers.get("uuid")

    # Extract credit info from request
    credit_info = {
        "creditName": data.get("creditName", "test"),
        "credit": data.get("credit", 0),
        "uuidList": data.get("uuidList", []),
    }

    # Use first UUID from list if header UUID not provided
    if not uuid_param and credit_info["uuidList"]:
        uuid_param = credit_info["uuidList"][0]

    amount = credit_info["credit"]

    # Initialize credit data if not exists
    with data_lock:
        if uuid_param not in credit_data:
            credit_data[uuid_param] = generate_credit_data(uuid_param, 0)

        # Update credit amounts
        current_total = credit_data[uuid_param]["totalAmount"]
        new_total = current_total + amount

        # Regenerate credit data with new amount
        credit_data[uuid_param] = generate_credit_data(uuid_param, new_total)

    return jsonify(
        create_success_response(
            {"creditId": str(uuid.uuid4()), "campaignId": campaign_id, "amount": amount}
        )
    )


@app.route("/billing/admin/campaign/<campaign_id>/credits", methods=["DELETE"])
def cancel_campaign_credit(campaign_id):
    """Cancel credit for a specific campaign."""
    reason = request.args.get("reason", "test")

    # For mock purposes, just return success
    return jsonify(
        create_success_response({"campaignId": campaign_id, "reason": reason})
    )


@app.route("/billing/admin/campaign/<campaign_id>/give", methods=["POST"])
def give_credit(campaign_id):
    """Give credit to user (legacy endpoint)."""
    data = request.json
    uuid_param = data.get("uuid")
    amount = data.get("amount", 0)

    # Initialize credit data if not exists
    with data_lock:
        if uuid_param not in credit_data:
            credit_data[uuid_param] = generate_credit_data(uuid_param, 0)

        # Update credit amounts
        current_total = credit_data[uuid_param]["totalAmount"]
        new_total = current_total + amount

        # Regenerate credit data with new amount
        credit_data[uuid_param] = generate_credit_data(uuid_param, new_total)

    return jsonify(create_success_response({"creditId": str(uuid.uuid4())}))


@app.route("/billing/credits/cancel", methods=["POST", "DELETE"])
def cancel_credit():
    """Cancel credit."""
    if request.method == "DELETE":
        uuid_param = request.args.get("uuid")
    else:
        data = request.json
        uuid_param = data.get("uuid")

    with data_lock:
        if uuid_param in credit_data:
            credit_data[uuid_param] = {
                "totalAmount": 0,
                "usedAmount": 0,
                "restAmount": 0,
                "credits": [],
            }

    return jsonify(create_success_response())


@app.route("/billing/credits/remaining", methods=["GET"])
def get_remaining_credits():
    """Get remaining credits."""
    uuid_param = request.args.get("uuid")

    # Return mock remaining credits based on uuid
    if uuid_param in credit_data:
        data = credit_data[uuid_param]
        return jsonify(
            create_success_response(
                {
                    "remainingCredits": data.get("restAmount", 0),
                    "totalCredit": data.get("totalAmount", 0),
                    "usedCredit": data.get("usedAmount", 0),
                }
            )
        )

    # Default response if no data exists
    return jsonify(
        create_success_response(
            {"remainingCredits": 0, "totalCredit": 0, "usedCredit": 0}
        )
    )


# Billing endpoints
@app.route("/billing/v5.0/bills/detail", methods=["GET"])
def get_billing_detail():
    """Get billing details."""
    uuid_param = request.args.get("uuid")
    month = request.args.get("month")

    # Check if user has any discounts (e.g., from contracts)
    has_discount = uuid_param in contracts

    # Calculate billing based on actual metering data
    compute_amount = 0
    storage_amount = 0
    network_amount = 0

    # Calculate amounts based on metering data
    metering_count = 0
    metering_data = data_manager.metering_data
    for meter_id, meter_data in metering_data.items():
        if meter_data.get("appKey") and "uuid" not in meter_data:
            metering_count += 1
            # This is metering data
            counter_name = meter_data.get("counterName", "")
            volume = float(meter_data.get("counterVolume", 0))

            # Calculate based on counter type
            if counter_name == "compute.g2.t4.c8m64":
                # GPU instance: 166.67 per hour
                compute_amount += int(volume * 166.67)
            elif counter_name == "compute.c2.c8m8":
                # Regular compute: 125 per hour (adjusted to match test expectations)
                compute_amount += int(volume * 125)
            elif counter_name == "storage.volume.ssd":
                # Storage: 100 per GB (monthly)
                # 524288000 KB = 500 GB
                storage_amount += int(volume / 1024 / 1024 * 100)  # Convert KB to GB
            elif counter_name == "network.floating_ip":
                # Floating IP: 25 per hour (adjusted to match test expectations)
                network_amount += int(volume * 25)

    # If no metering data, use default billing
    with open("mock_metering.log", "a") as f:
        f.write(
            f"Billing calculation - metering_count: {metering_count}, compute: {compute_amount}, storage: {storage_amount}, network: {network_amount}\n"
        )

    if compute_amount == 0 and storage_amount == 0 and network_amount == 0:
        billing_detail = generate_billing_detail(uuid_param, month, has_discount)
    else:
        # Generate billing based on actual metering
        subtotal = compute_amount + storage_amount + network_amount
        discount = int(subtotal * 0.1) if has_discount else 0
        charge = subtotal - discount
        vat = int(charge * 0.1)
        total = charge + vat

        billing_detail = {
            "uuid": uuid_param,
            "month": month,
            "currency": "KRW",
            "totalAmount": total,
            "charge": charge,
            "vat": vat,
            "discount": discount,
            "totalCredit": 0,
            "statements": [],
        }

    # Store for future reference
    billing_key = f"{uuid_param}:{month}"
    billing_data[billing_key] = billing_detail

    # Check if user has credits
    user_credits = 0
    if uuid_param in credit_data:
        user_credits = credit_data[uuid_param].get("totalAmount", 0)
        rest_credits = credit_data[uuid_param].get("restAmount", user_credits)
    else:
        rest_credits = 0

    # Apply credits to the bill (consume credits)
    total_bill = billing_detail.get("totalAmount", 0)
    charge = billing_detail.get("charge", 0)
    original_vat = billing_detail.get("vat", 0)

    # Calculate how much credit to use (use available rest credits)
    if rest_credits > 0:
        # Apply credit to charge amount (before VAT)
        credit_to_use = min(rest_credits, charge)

        # Update credit data to reflect usage
        with data_lock:
            if uuid_param in credit_data:
                total_credit_amount = credit_data[uuid_param].get("totalAmount", 0)
                already_used = credit_data[uuid_param].get("usedAmount", 0)
                credit_data[uuid_param]["usedAmount"] = already_used + credit_to_use
                credit_data[uuid_param]["restAmount"] = max(
                    0, total_credit_amount - (already_used + credit_to_use)
                )
    else:
        credit_to_use = 0

    # Add credit information to billing detail
    billing_detail["totalCredit"] = credit_to_use

    # Recalculate VAT after credit application (as tests expect)
    if credit_to_use > 0:
        new_charge = charge - credit_to_use
        new_vat = int(new_charge * 0.1)
        new_total = new_charge + new_vat

        # Update billing detail with recalculated values
        billing_detail["vat"] = new_vat
        billing_detail["totalAmount"] = new_total

    # Add top-level fields that tests expect
    # totalAmount stays original, totalPayments is what user actually pays
    original_total = billing_detail.get("totalAmount", 0)

    response_data = {
        **billing_detail,
        "charge": billing_detail.get("charge", 0),
        "totalAmount": original_total,  # Keep original total
        "totalPayments": original_total,  # Will be adjusted by common_test()
        "discountAmount": billing_detail.get("discount", 0),
        "vat": billing_detail.get("vat", 0),
        "totalCredit": credit_to_use,
    }

    return jsonify(create_success_response(response_data))


@app.route("/billing/console/statements", methods=["GET"])
def get_statements():
    """Get billing statements."""
    uuid_param = request.args.get("uuid")
    month = request.args.get("month")

    # Get billing detail if exists
    billing_key = f"{uuid_param}:{month}"
    if billing_key in billing_data:
        detail = billing_data[billing_key]
    else:
        # Generate new billing data
        has_discount = uuid_param in contracts
        detail = generate_billing_detail(uuid_param, month, has_discount)
        billing_data[billing_key] = detail

    # Get base charge before adjustments
    base_charge = detail.get("charge", 155000)

    # Apply adjustments
    adjusted_charge = base_charge

    # Apply project adjustments
    for adj_key, adj_data in adjustments.items():
        if adj_data.get("month") == month:
            # Check if this is a project adjustment
            if (adj_data.get("projectId") and adj_data.get("adjustmentType")) or (
                adj_data.get("billingGroupId") and adj_data.get("adjustmentType")
            ):
                adj_type = adj_data["adjustmentType"]
                adj_amount = adj_data.get("adjustment", 0)

                if adj_type == "STATIC_DISCOUNT":
                    adjusted_charge -= adj_amount
                elif adj_type == "STATIC_EXTRA":
                    adjusted_charge += adj_amount
                elif adj_type == "PERCENT_DISCOUNT":
                    adjusted_charge *= 1 - adj_amount / 100
                elif adj_type == "PERCENT_EXTRA":
                    adjusted_charge *= 1 + adj_amount / 100

    # Calculate VAT and total with adjusted charge
    adjusted_charge = int(adjusted_charge)
    vat = int(adjusted_charge * 0.1)
    total = adjusted_charge + vat

    statement_data = {
        "statements": [
            {
                "charge": adjusted_charge,
                "totalAmount": total,
                "vat": vat,
                "discount": detail.get("discount", 0),
                "items": detail.get("statements", []),
            }
        ],
        "totalPayments": total,
    }

    return jsonify(create_success_response(statement_data))


# Contract endpoints
@app.route("/billing/contracts", methods=["POST", "GET"])
def handle_contracts():
    """Handle contracts - create or list."""
    if request.method == "GET":
        # List contracts
        billing_group_id = request.args.get("billingGroupId")
        contract_list = []

        for cid, contract in contracts.items():
            if (
                not billing_group_id
                or contract.get("billingGroupId") == billing_group_id
            ):
                contract_list.append(contract)

        return jsonify(create_success_response({"contracts": contract_list}))
    # Create contract
    data = request.json
    contract_id = str(uuid.uuid4())

    contracts[contract_id] = {"contractId": contract_id, "status": "ACTIVE", **data}

    return jsonify(create_success_response({"contractId": contract_id}))


@app.route("/billing/contracts/<contract_id>", methods=["GET"])
def get_contract(contract_id):
    """Get contract details."""
    if contract_id not in contracts:
        return create_error_response("Contract not found", 404)

    return jsonify(create_success_response({"contract": contracts[contract_id]}))


# Admin endpoints
@app.route("/billing/admin/meters", methods=["DELETE"])
def delete_meters():
    """Delete metering data."""
    app_keys = request.args.getlist("appKeys")
    # Just return success for mock
    return jsonify(create_success_response({"deletedCount": len(app_keys)}))


@app.route("/billing/admin/contracts/<contract_id>", methods=["DELETE"])
def delete_contract(contract_id):
    """Delete contract."""
    if contract_id in contracts:
        del contracts[contract_id]
    return jsonify(create_success_response())


@app.route("/billing/admin/contracts", methods=["DELETE"])
def delete_all_contracts():
    """Delete all contracts."""
    contracts.clear()
    return jsonify(create_success_response())


@app.route("/billing/admin/adjustments", methods=["GET"])
def get_adjustments():
    """Get adjustments."""
    # Return empty list for now
    return jsonify(create_success_response({"adjustments": []}))


@app.route("/billing/admin/adjustments", methods=["DELETE"])
def delete_adjustments():
    """Delete adjustments."""
    return jsonify(create_success_response({"deletedCount": 0}))


@app.route("/billing/admin/resources", methods=["DELETE"])
def delete_resources():
    """Delete calculation resources."""
    return jsonify(create_success_response({"deletedCount": 0}))


@app.route("/billing/console/payment/<payment_id>", methods=["GET"])
def get_payment_status(payment_id):
    """Get payment status."""
    mock_payment = {
        "paymentGroupId": payment_id,
        "status": "READY",
        "amount": 150000,
        "dueDate": (datetime.now() + timedelta(days=30)).isoformat(),
    }
    return jsonify(create_success_response({"payment": mock_payment}))


@app.route("/billing/console/payments", methods=["GET"])
def get_payments():
    """Get payments list."""
    uuid_param = request.args.get("uuid")
    month = request.args.get("month")

    # Return mock payment data
    mock_payments = [
        {
            "paymentGroupId": f"PG-{uuid_param[:8] if uuid_param else 'DEFAULT'}",
            "status": "READY",
            "amount": 150000,
            "month": month,
            "dueDate": (datetime.now() + timedelta(days=30)).isoformat(),
        }
    ]

    return jsonify(create_success_response({"payments": mock_payments}))


@app.route("/billing/console/payment/statements/<billing_group_id>", methods=["GET"])
def get_payment_statements(billing_group_id):
    """Get payment statements for billing group."""
    # Return mock payment status
    return jsonify(
        create_success_response(
            {"paymentGroupId": f"PG-{billing_group_id[:8]}", "paymentStatus": "READY"}
        )
    )


@app.route("/billing/console/billing-info/<billing_group_id>", methods=["GET"])
def get_billing_info(billing_group_id):
    """Get billing info for billing group."""
    # Return mock billing info
    return jsonify(
        create_success_response(
            {
                "billingGroupId": billing_group_id,
                "paymentStatus": "REGISTERED",
                "paymentGroupId": f"PG-{billing_group_id[:8]}",
            }
        )
    )


@app.route("/billing/console/payment/<payment_id>", methods=["PUT"])
def update_payment(payment_id):
    """Update payment (for payment/cancel operations)."""
    return jsonify(create_success_response())


@app.route("/billing/admin/calculate", methods=["POST"])
def create_calculation():
    """Create calculation job."""
    data = request.json
    job_id = str(uuid.uuid4())

    # Store the calculation job
    batch_jobs[job_id] = {
        "batchJobCode": "API_CALCULATE_USAGE_AND_PRICE",
        "status": "COMPLETED",  # Set to completed for mock
        "completedCount": 100,
        "totalCount": 100,
        "createdAt": datetime.now().isoformat(),
    }

    return jsonify(create_success_response({"batchJobCode": job_id}))


# Duplicate endpoint removed - handled by /billing/credits/cancel above


# Payment endpoints for console API (missing endpoint fix)
@app.route("/billing/payments/<month>/statements", methods=["GET"])
def get_payment_statements_console(month):
    """Get payment statements for console API."""
    uuid_param = request.headers.get("uuid")

    # Return mock payment status
    return jsonify(
        create_success_response(
            {
                "paymentGroupId": f"PG-{uuid_param[:8] if uuid_param else 'DEFAULT'}",
                "paymentStatus": "READY",
                "statements": [{"amount": 150000, "month": month, "status": "READY"}],
            }
        )
    )


# Billing Group endpoints
@app.route("/billing/admin/billing-groups/<billing_group_id>", methods=["PUT"])
def update_billing_group(billing_group_id):
    """Update billing group (for applying contracts)."""
    return jsonify(create_success_response({"billingGroupId": billing_group_id}))


@app.route(
    "/billing/admin/billing-groups/<billing_group_id>/contracts", methods=["DELETE"]
)
def delete_billing_group_contracts(billing_group_id):
    """Delete contracts from billing group."""
    return jsonify(create_success_response({"deletedCount": 1}))


# Contract price lookup
@app.route("/billing/admin/contracts/<contract_id>/products/prices", methods=["GET"])
def get_contract_prices(contract_id):
    """Get contract prices."""
    counter_name = request.args.get("counterName")
    return jsonify(
        create_success_response(
            {"price": 100, "counterName": counter_name, "contractId": contract_id}
        )
    )


# Credit endpoints - v5.0 API
@app.route("/billing/v5.0/credits", methods=["GET"])
def get_credits_v5():
    """Get credits (v5.0 API)."""
    uuid_param = request.headers.get("uuid")

    if uuid_param in credit_data:
        data = credit_data[uuid_param]
        rest_amount = data.get("restAmount", 0)
        return jsonify(
            create_success_response(
                {
                    "stats": {
                        "totalAmount": rest_amount,
                        "restCreditsByBalancePriceTypeCode": [
                            {"balancePriceTypeCode": "FREE", "restAmount": rest_amount}
                        ],
                    },
                    "totalCredit": data.get("totalAmount", 0),
                    "usedCredit": data.get("usedAmount", 0),
                    "restCredit": rest_amount,
                }
            )
        )

    return jsonify(
        create_success_response(
            {
                "stats": {"totalAmount": 0, "restCreditsByBalancePriceTypeCode": []},
                "totalCredit": 0,
                "usedCredit": 0,
                "restCredit": 0,
            }
        )
    )


# Campaign credit management
@app.route("/billing/admin/campaign/<campaign_id>/credits", methods=["POST", "DELETE"])
def manage_campaign_credits(campaign_id):
    """Manage campaign credits."""
    if request.method == "DELETE":
        # Delete credits
        uuid_param = request.args.get("uuid") or request.headers.get("uuid")
        with data_lock:
            if uuid_param in credit_data:
                credit_data[uuid_param] = generate_credit_data(uuid_param, 0)
        return jsonify(create_success_response())
    # Grant credits
    data = request.json
    # Handle different data structures
    uuid_param = None
    amount = 0

    # Check for direct structure (from actual API)
    if data.get("uuidList"):
        uuid_param = data["uuidList"][0]
        amount = data.get("credit", 0)
    # Check for simplified structure
    else:
        uuid_param = data.get("uuid")
        amount = data.get("amount", 0)

    if uuid_param:
        with data_lock:
            if uuid_param not in credit_data:
                credit_data[uuid_param] = generate_credit_data(uuid_param, 0)

            current_total = credit_data[uuid_param]["totalAmount"]
            new_total = current_total + amount
            credit_data[uuid_param] = generate_credit_data(uuid_param, new_total)

    return jsonify(create_success_response({"creditId": str(uuid.uuid4())}))


# Calculation endpoints - correct path
@app.route("/billing/admin/calculations", methods=["POST"])
def create_calculations():
    """Create calculation job."""
    data = request.json
    job_id = str(uuid.uuid4())

    # Store the calculation job
    batch_jobs[job_id] = {
        "batchJobCode": job_id,
        "status": "COMPLETED",  # Set to completed for mock
        "completedCount": 100,
        "totalCount": 100,
        "createdAt": datetime.now().isoformat(),
    }

    return jsonify(create_success_response({"batchJobCode": job_id}))


# Adjustment endpoints
@app.route("/billing/admin/projects/adjustments", methods=["POST", "GET"])
def project_adjustments():
    """Handle project adjustments."""
    if request.method == "GET":
        # Get query parameters
        project_id = request.args.get("projectId")
        month = request.args.get("month")

        # Filter adjustments
        filtered = []
        for adj_id, adj in adjustments.items():
            if adj.get("target") == "Project" and adj.get("projectId") == project_id:
                if not month or adj.get("month") == month:
                    filtered.append(adj)

        return jsonify(create_success_response({"adjustments": filtered}))
    # Create adjustment
    data = request.json
    adj_id = str(uuid.uuid4())

    # Store adjustment
    descriptions = data.get("descriptions", [])
    description = (
        descriptions[0]["message"] if descriptions else data.get("description", "")
    )

    adjustments[adj_id] = {
        "adjustmentId": adj_id,
        "target": "Project",
        "projectId": data.get("projectId"),
        "month": data.get("monthFrom", data.get("month")),
        "adjustmentType": data.get("adjustmentTypeCode", data.get("adjustmentType")),
        "adjustmentValue": data.get("adjustment", data.get("adjustmentValue")),
        "description": description,
        "createdAt": datetime.now().isoformat(),
    }

    return jsonify(create_success_response({"adjustmentId": adj_id}))


@app.route(
    "/billing/admin/billing-groups/adjustments", methods=["POST", "GET", "DELETE"]
)
def billing_group_adjustments():
    """Handle billing group adjustments."""
    if request.method == "GET":
        # Get query parameters
        billing_group_id = request.args.get("billingGroupId")
        month = request.args.get("month")

        # Filter adjustments
        filtered = []
        for adj_id, adj in adjustments.items():
            if (
                adj.get("target") == "BillingGroup"
                and adj.get("billingGroupId") == billing_group_id
            ):
                if not month or adj.get("month") == month:
                    filtered.append(adj)

        return jsonify(create_success_response({"adjustments": filtered}))
    if request.method == "DELETE":
        # Delete adjustments by IDs
        adjustment_ids = request.args.get("adjustmentIds", "").split(",")
        deleted_count = 0

        for adj_id in adjustment_ids:
            adj_id = adj_id.strip()
            if adj_id in adjustments:
                del adjustments[adj_id]
                deleted_count += 1

        return jsonify(
            create_success_response(
                {
                    "deletedCount": deleted_count,
                    "message": f"Deleted {deleted_count} adjustments",
                }
            )
        )
    # Create adjustment
    data = request.json
    adj_id = str(uuid.uuid4())

    # Store adjustment
    descriptions = data.get("descriptions", [])
    description = (
        descriptions[0]["message"] if descriptions else data.get("description", "")
    )

    adjustments[adj_id] = {
        "adjustmentId": adj_id,
        "target": "BillingGroup",
        "billingGroupId": data.get("billingGroupId"),
        "month": data.get("monthFrom", data.get("month")),
        "adjustmentType": data.get("adjustmentTypeCode", data.get("adjustmentType")),
        "adjustmentValue": data.get("adjustment", data.get("adjustmentValue")),
        "description": description,
        "createdAt": datetime.now().isoformat(),
    }

    return jsonify(create_success_response({"adjustmentId": adj_id}))


# Batch endpoints
@app.route("/billing/admin/batches", methods=["POST"])
def create_batch():
    """Create batch job."""
    data = request.json
    batch_id = str(uuid.uuid4())

    batch_jobs[batch_id] = {
        "batchId": batch_id,
        "status": "STARTED",
        "createdAt": datetime.now().isoformat(),
        **data,
    }

    return jsonify(create_success_response({"batchId": batch_id}))


# Health check
@app.route("/health", methods=["GET"])
@cache.cached(timeout=300)  # Cache for 5 minutes
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


# Reset endpoint for testing
@app.route("/test/reset", methods=["POST"])
def reset_test_data():
    """Reset all test data for a specific UUID."""
    data = request.json or {}
    uuid_param = data.get("uuid") or request.headers.get("uuid")

    if uuid_param:
        # Use data manager to clear UUID-specific data
        data_manager.clear_uuid_data(uuid_param)
        logger.info(f"Cleared all test data for UUID: {uuid_param}")

        # Log the action
        with open("mock_metering.log", "a") as f:
            f.write(f"Cleared all data for UUID: {uuid_param}\n")

        # Clear cache for this UUID
        cache.delete_many(f"*{uuid_param}*")

        return jsonify(
            create_success_response(
                {"message": f"Test data reset for UUID: {uuid_param}"}
            )
        )
    # Reset all data if no UUID specified
    credit_data.clear()
    billing_data.clear()
    metering_data.clear()
    batch_jobs.clear()
    contracts.clear()
    batch_progress.clear()

    return jsonify(create_success_response({"message": "All test data reset"}))


# Contract Testing Support
@app.route("/pact-states", methods=["POST"])
def provider_states():
    """Handle provider state setup for Pact verification."""
    data = request.json
    state = data.get("state")

    # Handle different states
    if state == "A contract exists":
        # Ensure contract 12345 exists
        contracts["12345"] = generate_contract_data("12345")
    elif state == "Customer exists":
        # Customer data is already available
        pass
    elif state == "Metering data exists for project":
        # Ensure metering data exists
        project_id = "PROJ001"
        metering_data[project_id] = {
            "project_id": project_id,
            "period": {"start": "2025-01-01T00:00:00", "end": "2025-01-31T23:59:59"},
            "usage": [
                {
                    "resource_type": "compute",
                    "resource_id": "vm-001",
                    "quantity": 744.0,
                    "unit": "hours",
                    "cost": 74.40,
                }
            ],
            "total_cost": 74.40,
        }
    elif state == "Payment exists":
        # Ensure payment PAY001 exists
        billing_data["PAY001"] = {
            "payment_id": "PAY001",
            "status": "PENDING",
            "amount": 1000.0,
            "currency": "USD",
        }
    elif state == "Contract does not exist":
        # Remove contract 99999 if it exists
        contracts.pop("99999", None)

    return jsonify({"result": "success"}), 200


# Additional Contract-compliant endpoints
@app.route("/api/v1/contracts/<contract_id>", methods=["GET"])
def get_contract_v1(contract_id):
    """Get contract details (v1 API for contract compliance)."""
    if contract_id not in contracts:
        return (
            jsonify(
                {"error": "NOT_FOUND", "message": "Contract not found", "code": 404}
            ),
            404,
        )

    return jsonify(contracts[contract_id]), 200


@app.route("/api/v1/credits", methods=["POST"])
def create_credit_v1():
    """Create credit transaction (v1 API for contract compliance)."""
    data = request.json

    # Validate amount
    if data.get("amount", 0) < 0:
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid credit amount",
                    "field": "amount",
                    "code": 400,
                }
            ),
            400,
        )

    credit_id = str(uuid.uuid4())
    credit = {
        "id": credit_id,
        "customer_id": data["customer_id"],
        "amount": data["amount"],
        "currency": data.get("currency", "USD"),
        "description": data.get("description", ""),
        "type": data.get("type", "ADJUSTMENT"),
        "status": "APPROVED",
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }

    credit_data[credit_id] = credit
    return jsonify(credit), 201


@app.route("/api/v1/metering", methods=["GET"])
def get_metering_v1():
    """Get metering data (v1 API for contract compliance)."""
    project_id = request.args.get("project_id")
    month = request.args.get("month")

    if project_id in metering_data:
        return jsonify(metering_data[project_id]), 200

    # Generate default metering data
    data = {
        "project_id": project_id,
        "period": {"start": f"{month}-01T00:00:00", "end": f"{month}-31T23:59:59"},
        "usage": [
            {
                "resource_type": "compute",
                "resource_id": "vm-default",
                "quantity": 744.0,
                "unit": "hours",
                "cost": 74.40,
            }
        ],
        "total_cost": 74.40,
    }

    return jsonify(data), 200


@app.route("/api/v1/payments/<payment_id>", methods=["PATCH"])
def update_payment_v1(payment_id):
    """Update payment status (v1 API for contract compliance)."""
    data = request.json

    if payment_id not in billing_data:
        billing_data[payment_id] = {
            "payment_id": payment_id,
            "amount": 1000.0,
            "currency": "USD",
        }

    payment = billing_data[payment_id]
    payment["status"] = data.get("status", payment.get("status", "PENDING"))
    payment["transaction_id"] = data.get(
        "transaction_id", payment.get("transaction_id")
    )
    payment["updated_at"] = data.get(
        "completed_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    )

    return jsonify(payment), 200


# OpenAPI Support Endpoints
@app.route("/openapi", methods=["GET"])
@app.route("/openapi.json", methods=["GET"])
@app.route("/openapi.yaml", methods=["GET"])
def get_openapi_spec():
    """Get OpenAPI specification."""
    handler = get_openapi_handler()
    if not handler:
        return jsonify({"error": "OpenAPI not available"}), 404

    spec = handler.spec_dict

    if request.path.endswith(".yaml"):
        import yaml

        response = make_response(yaml.dump(spec))
        response.headers["Content-Type"] = "application/x-yaml"
        return response

    return jsonify(spec)


@app.route("/openapi/validate", methods=["POST"])
def validate_openapi_request():
    """Validate request against OpenAPI spec."""
    handler = get_openapi_handler()
    if not handler:
        return jsonify({"error": "OpenAPI not available"}), 404

    data = request.json
    method = data.get("method", "GET")
    path = data.get("path", "/")
    body = data.get("body")
    query_params = data.get("query_params")

    error = handler.validate_request(method, path, body, query_params)

    if error:
        return jsonify({"valid": False, "error": error}), 400

    return jsonify({"valid": True})


@app.route(
    "/openapi/generate/<path:api_path>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
def generate_openapi_response(api_path):
    """Generate response based on OpenAPI spec."""
    handler = get_openapi_handler()
    if not handler:
        # Fallback to default behavior
        return jsonify({"error": "OpenAPI not available"}), 404

    # Construct full path
    full_path = f"/api/v1/{api_path}"

    # Find operation
    operation = handler.find_operation(request.method, full_path)
    if not operation:
        return (
            jsonify(
                {
                    "error": "NOT_FOUND",
                    "message": f"No operation found for {request.method} {full_path}",
                    "code": 404,
                }
            ),
            404,
        )

    # Validate request if it has body
    if request.is_json:
        error = handler.validate_request(
            request.method, full_path, request.json, request.args.to_dict()
        )
        if error:
            return (
                jsonify({"error": "VALIDATION_ERROR", "message": error, "code": 400}),
                400,
            )

    # Determine status code
    status_code = 200
    if request.method == "POST":
        status_code = 201
    elif request.method == "DELETE":
        status_code = 204

    # Generate response
    response_data = handler.generate_response(operation, status_code)

    # Special handling for 204 No Content
    if status_code == 204:
        return "", 204

    return jsonify(response_data), status_code


# Catch-all route for undefined API endpoints
@app.route("/api/v1/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def handle_undefined_api(path):
    """Handle undefined API endpoints using OpenAPI if available."""
    handler = get_openapi_handler()
    if handler:
        # Try to handle with OpenAPI
        return generate_openapi_response(path)

    # Default 404 response
    return (
        jsonify(
            {
                "error": "NOT_FOUND",
                "message": f"Endpoint not found: /api/v1/{path}",
                "code": 404,
            }
        ),
        404,
    )


if __name__ == "__main__":
    port = int(os.environ.get("MOCK_SERVER_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
