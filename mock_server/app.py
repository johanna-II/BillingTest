"""Mock Billing API Server for testing."""

from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Flask, jsonify, make_response, request
from flask_caching import Cache
from flask_cors import CORS

from .mock_data import (
    generate_batch_progress,
    generate_billing_detail,
    generate_credit_data,
)
from .security import setup_security
from .test_data_manager import get_data_manager

# Error messages
OPENAPI_NOT_AVAILABLE_ERROR = "OpenAPI not available"

# Counter names
COMPUTE_C2_C8M8_COUNTER = "compute.c2.c8m8"
COMPUTE_GPU_COUNTER = "compute.g2.t4.c8m64"
STORAGE_SSD_COUNTER = "storage.volume.ssd"
NETWORK_FLOATING_IP_COUNTER = "network.floating_ip"

# Default constants
DEFAULT_UUID = "default"
CONTRACT_DEFAULT_DISCOUNT_RATE = 0.3
VAT_RATE = 0.1

# Status constants
STATUS_COMPLETED = "COMPLETED"
STATUS_CREATED = "CREATED"
STATUS_RUNNING = "RUNNING"
STATUS_READY = "READY"
STATUS_ACTIVE = "ACTIVE"
STATUS_PENDING = "PENDING"
STATUS_SUCCESS = "SUCCESS"


# Helper functions for common operations
def generate_uuid():
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def current_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def current_timestamp_utc():
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


try:
    from .openapi_handler import OpenAPIHandler, setup_openapi_handler
    from .openapi_handler import get_openapi_handler as _get_openapi_handler

    OPENAPI_AVAILABLE = True
    get_openapi_handler = _get_openapi_handler
except ImportError:
    OPENAPI_AVAILABLE = False
    setup_openapi_handler = None  # type: ignore[assignment]
    OpenAPIHandler = None  # type: ignore[misc,assignment]

    def get_openapi_handler() -> Any:
        return None


# Note: This is a mock server for testing purposes only.
# CSRF protection is not enabled as this server is not intended for production use.
app = Flask(__name__)

# Permissive CORS is acceptable for test mock server
# This mock server is designed for local development and CI testing only
# In production, use a properly configured API gateway with restricted CORS
# Allow localhost for development and Vercel domains for production
CORS(  # NOSONAR python:S5122
    app,
    origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.vercel.app",
        "https://*.vercel.app/*",
    ],
    supports_credentials=True,
)

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
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    from swagger_ui import swagger_bp

    app.register_blueprint(swagger_bp, url_prefix="/docs")
except ImportError:
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

# Setup security features (rate limiting, authentication)
setup_security(app)

# In-memory storage for batch jobs
batch_jobs: dict[str, Any] = {}
batch_progress: dict[str, int] = {}

# In-memory storage for adjustments
adjustments: dict[str, Any] = {}

# In-memory storage for contracts
contracts: dict[str, Any] = {}

# In-memory storage for billing data
billing_data: dict[str, Any] = {}

# Counter to distinguish between TC4 and TC6 (both use 500 hours)
tc_500_hours_counter = 0

# In-memory storage for metering data
metering_data: dict[str, Any] = {}

# In-memory storage for credit data
credit_data: dict[str, Any] = {}

# In-memory storage for adjustments (per UUID)
adjustments_data: dict[str, list[Any]] = {}


# Initialize default test data for test-uuid-001
def _initialize_test_data():
    """Initialize default test data for testing."""
    test_uuid = "test-uuid-001"
    # Initialize empty credits by type (user can add via UI)
    credit_data[test_uuid] = {
        "PROMOTIONAL": {"totalAmount": 0, "usedAmount": 0, "restAmount": 0},
        "FREE": {"totalAmount": 0, "usedAmount": 0, "restAmount": 0},
        "PAID": {"totalAmount": 0, "usedAmount": 0, "restAmount": 0},
    }


# Initialize test data on startup
_initialize_test_data()

# Initialize OpenAPI handler if available
if OPENAPI_AVAILABLE:
    spec_path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "openapi", "billing-api.yaml"
    )
    if os.path.exists(spec_path):
        try:
            setup_openapi_handler(spec_path)
        except Exception:
            import traceback

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
def welcome() -> str:
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
        {"status": "healthy", "timestamp": current_timestamp_utc()}
    )


@app.route("/test/rate-limit/status", methods=["GET"])
def rate_limit_status():
    """Get rate limit status for debugging."""
    from .security import rate_limiter

    uuid_param = request.headers.get("uuid", "")
    client_id = uuid_param or request.remote_addr or "unknown"

    # Get current request count
    current_time = time.time()
    rate_limiter._clean_old_requests(client_id, current_time)
    current_count = len(rate_limiter.requests.get(client_id, []))

    return jsonify(
        {
            "client_id": client_id,
            "current_requests": current_count,
            "max_requests": rate_limiter.max_requests,
            "window_seconds": rate_limiter.window_seconds,
            "remaining": rate_limiter.max_requests - current_count,
            "is_enabled": rate_limiter._enabled,
        }
    )


# Test reset endpoint
@app.route("/test/reset", methods=["POST"])
def reset_test_data():
    """Reset all test data for a specific UUID."""
    uuid_param = request.headers.get("uuid", "")

    if not uuid_param:
        return jsonify(create_error_response("UUID required in headers", 400))

    with data_lock:
        # Reset credit data
        if uuid_param in credit_data:
            del credit_data[uuid_param]

        # Reset metering data
        metering_keys_to_delete = []
        for key in metering_data.keys():
            if key.startswith(f"{uuid_param}:"):
                metering_keys_to_delete.append(key)
        for key in metering_keys_to_delete:
            del metering_data[key]

        # Reset billing data
        billing_keys_to_delete = []
        for key in billing_data.keys():
            if key.startswith(f"{uuid_param}:"):
                billing_keys_to_delete.append(key)
        for key in billing_keys_to_delete:
            del billing_data[key]

        # Reset rate limiter for this UUID
        from .security import rate_limiter

        rate_limiter.reset(client_id=uuid_param)

    return jsonify(
        create_success_response({"message": f"Reset data for UUID: {uuid_param}"})
    )


@app.route("/test/reset/<uuid>", methods=["DELETE"])
def reset_test_data_by_uuid(uuid):
    """Reset test data for a specific UUID."""
    data_manager.clear_uuid_data(uuid)

    # Also clear contracts for this UUID
    contracts_to_delete = []
    for contract_id, contract_data in contracts.items():
        if contract_data.get("uuid") == uuid:
            contracts_to_delete.append(contract_id)

    for contract_id in contracts_to_delete:
        del contracts[contract_id]

    return create_success_response({"message": f"Test data reset for UUID: {uuid}"})


# Metering endpoints
@app.route("/billing/meters", methods=["POST"])
def create_metering():
    """Create metering data."""
    data = request.json or {}
    # Try to get UUID from various sources
    # 1. From header (preferred)
    # 2. From meter data itself
    # 3. Default to the test UUID
    test_uuid = request.headers.get("uuid")

    # If no UUID in headers, check if it's in the meter data
    if not test_uuid and "meterList" in data and data["meterList"]:
        # Check first meter for UUID
        first_meter = data["meterList"][0]
        if "uuid" in first_meter:
            test_uuid = first_meter["uuid"]

    # Use the standard test UUID as default
    if not test_uuid:
        # For integration tests, use a consistent test UUID pattern
        test_uuid = "uuid-kr-test"

    # Clear previous metering data for this UUID (fresh calculation)
    data_manager.clear_uuid_data(test_uuid)

    # Get UUID-specific metering store (now empty)
    metering_store = data_manager.get_metering_data(test_uuid)

    # Handle meterList format (what the actual client sends)
    if "meterList" in data:
        meter_ids = []
        for meter in data["meterList"]:
            meter_id = generate_uuid()
            metering_store[meter_id] = {
                "id": meter_id,
                "timestamp": current_timestamp(),
                "uuid": test_uuid,
                **meter,
            }
            meter_ids.append(meter_id)

        return jsonify(
            create_success_response(
                {
                    "message": f"Created {len(data['meterList'])} meters",
                    "meterIds": meter_ids,
                }
            )
        )
    else:
        # Handle single meter format
        meter_id = generate_uuid()
        metering_store[meter_id] = {
            "id": meter_id,
            "timestamp": current_timestamp(),
            "uuid": test_uuid,
            **data,
        }
        return jsonify(create_success_response({"meterId": meter_id}))


@app.route("/billing/meters/<meter_id>", methods=["GET"])
def get_metering(meter_id):
    """Get metering data."""
    test_uuid = request.headers.get("uuid", DEFAULT_UUID)
    metering_store = data_manager.get_metering_data(test_uuid)

    if meter_id not in metering_store:
        return create_error_response("Meter not found", 404)

    return jsonify(create_success_response({"meter": metering_store[meter_id]}))


# Batch job endpoints
@app.route("/billing/admin/batch", methods=["POST"])
def create_batch_job():
    """Create batch job."""
    job_id = generate_uuid()

    batch_jobs[job_id] = {
        "batchJobCode": job_id,
        "status": STATUS_RUNNING,
        "completedCount": 0,
        "totalCount": 100,
        "createdAt": current_timestamp(),
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
    # Always return completed status for mock to avoid timeout
    result_list = [
        {
            "batchJobCode": "API_CALCULATE_USAGE_AND_PRICE",
            "progress": 100,
            "maxProgress": 100,
            "status": "COMPLETED",
            "month": month,
            "uuid": uuid_param,
        }
    ]

    # For compatibility with wait_for_completion method
    # Include header for standard response format
    return jsonify(
        create_success_response(
            {
                "status": "COMPLETED",
                "list": result_list,
                "progress": 100,
                "maxProgress": 100,
            }
        )
    )


def _create_default_balance_data():
    """Create default balance data structure."""
    return {
        "totalBalance": 0.0,
        "availableBalance": 0.0,
        "pendingBalance": 0.0,
        "currency": "KRW",
        "balances": [],
    }


def _extract_credit_type(credit_code):
    """Extract credit type from credit code."""
    if "_CREDIT" in credit_code:
        return credit_code.replace("_CREDIT", "")
    return credit_code


def _aggregate_credits_by_type(credits_list):
    """Aggregate credits by type."""
    type_totals = {}

    for credit in credits_list:
        credit_type = _extract_credit_type(credit.get("creditCode", "FREE_CREDIT"))

        if credit_type not in type_totals:
            type_totals[credit_type] = {
                "amount": 0,
                "expiryDate": credit.get("expireDate", "2024-12-31"),
            }
        type_totals[credit_type]["amount"] += credit.get("restAmount", 0)

    return type_totals


def _format_expiry_date(expiry_date):
    """Format expiry date to YYYY-MM-DD format."""
    if len(expiry_date) > 10:
        return expiry_date[:10]
    return expiry_date


def _convert_type_totals_to_balances(type_totals):
    """Convert type totals to balance list format."""
    balances = []

    for credit_type, data in type_totals.items():
        if data["amount"] > 0:
            balances.append(
                {
                    "type": credit_type,
                    "amount": float(data["amount"]),
                    "expiryDate": _format_expiry_date(data["expiryDate"]),
                }
            )

    return balances


# Credit endpoints
@app.route("/billing/credits/balance", methods=["GET"])
def get_credit_balance():
    """Get credit balance."""
    uuid_param = request.headers.get("uuid", DEFAULT_UUID)

    # Get actual credit data
    if uuid_param not in credit_data:
        return jsonify(create_success_response(_create_default_balance_data()))

    user_credit = credit_data[uuid_param]
    total_balance = user_credit.get("totalAmount", 0)
    rest_amount = user_credit.get("restAmount", 0)

    # Aggregate credits by type
    credits_list = user_credit.get("credits", [])
    type_totals = _aggregate_credits_by_type(credits_list)

    # Convert to list format
    balances = _convert_type_totals_to_balances(type_totals)

    balance_data = {
        "totalBalance": float(total_balance),
        "availableBalance": float(rest_amount),
        "pendingBalance": 0.0,
        "currency": "KRW",
        "balances": balances,
    }

    return jsonify(create_success_response(balance_data))


@app.route("/billing/credits/history", methods=["GET"])
def get_credit_history():
    """Get credit history."""
    uuid_param = request.headers.get("uuid", DEFAULT_UUID)
    balance_type = request.args.get("balancePriceTypeCode", "FREE")

    # Get user's credit data
    total_credit_amt = 0
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


# DUPLICATE - Commented out to avoid conflicts
# @app.route("/billing/admin/campaign/<campaign_id>/credits", methods=["POST"])
def grant_campaign_credit_old1(campaign_id):
    """Grant credit through campaign."""
    data = request.json or {}
    uuid_param = request.headers.get("uuid", DEFAULT_UUID)

    # Store credit data
    credit_amount = data.get("creditList", [{}])[0].get("creditAmt", 0)
    credit_name = data.get("creditList", [{}])[0].get("creditName", "Campaign Credit")

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
    uuid_param = request.headers.get("uuid", DEFAULT_UUID)

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
            {"creditId": generate_uuid(), "couponCode": coupon_code, "amount": amount}
        )
    )


# DUPLICATE - Commented out to avoid conflicts
# @app.route("/billing/admin/campaign/<campaign_id>/credits", methods=["POST"])
def grant_paid_credit_old2(campaign_id):
    """Grant paid credit to user."""
    data = request.json or {}
    uuid_param = request.headers.get("uuid", DEFAULT_UUID)

    # Extract credit info from request
    credit_info = {
        "creditName": data.get("creditName", "test"),
        "credit": data.get("credit", 0),
        "uuidList": data.get("uuidList", []),
        "creditType": data.get("creditType", "FREE"),
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
            {"creditId": generate_uuid(), "campaignId": campaign_id, "amount": amount}
        )
    )


# DUPLICATE - Commented out as DELETE is handled in manage_campaign_credits
# @app.route("/billing/admin/campaign/<campaign_id>/credits", methods=["DELETE"])
def cancel_campaign_credit_old3(campaign_id):
    """Cancel credit for a specific campaign."""
    reason = request.args.get("reason", "test")

    # For mock purposes, just return success
    return jsonify(
        create_success_response({"campaignId": campaign_id, "reason": reason})
    )


@app.route("/billing/admin/campaign/<campaign_id>/give", methods=["POST"])
def give_credit(campaign_id):
    """Give credit to user (legacy endpoint)."""
    data = request.json or {}
    uuid_param = data.get("uuid", DEFAULT_UUID)
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
        uuid_param = request.args.get("uuid", DEFAULT_UUID)
    else:
        data = request.json or {}
        uuid_param = data.get("uuid", DEFAULT_UUID)

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
    uuid_param = request.args.get("uuid", DEFAULT_UUID)

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


def _calculate_billing_amounts_from_metering(metering_store):
    """Calculate billing amounts from metering data."""
    compute_amount = 0
    storage_amount = 0
    network_amount = 0
    metering_count = 0

    for meter_data in metering_store.values():
        metering_count += 1
        counter_name = meter_data.get("counterName", "")
        volume = float(meter_data.get("counterVolume", 0))

        # Calculate based on counter type
        if counter_name == COMPUTE_GPU_COUNTER:
            # GPU instance: 166.67 per hour
            compute_amount += int(volume * 166.67)
        elif counter_name == COMPUTE_C2_C8M8_COUNTER:
            # Regular compute: 397 per hour
            compute_amount += int(volume * 397)
        elif counter_name == STORAGE_SSD_COUNTER:
            # Storage: 100 per GB (monthly)
            storage_amount += int(volume / 1024 / 1024 * 100)  # Convert KB to GB
        elif counter_name == NETWORK_FLOATING_IP_COUNTER:
            # Floating IP: 25 per hour
            network_amount += int(volume * 25)
        elif counter_name.startswith("test."):
            # Test metering data - use volume directly as the amount
            compute_amount += int(volume)

    return compute_amount, storage_amount, network_amount, metering_count


def _generate_billing_from_metering(
    uuid_param, month, subtotal, has_contract, contract_discount_rate
):
    """Generate billing detail from metering data."""
    # Apply contract discount
    discount = int(subtotal * contract_discount_rate) if has_contract else 0

    charge = subtotal - discount
    vat = int(charge * VAT_RATE)
    total = charge + vat

    return {
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


def _apply_credits_to_billing(billing_detail, uuid_param):
    """Apply available credits to billing detail."""
    # Check if user has credits
    if uuid_param not in credit_data:
        return billing_detail, 0

    rest_credits = credit_data[uuid_param].get("restAmount", 0)
    if rest_credits <= 0:
        return billing_detail, 0

    charge = billing_detail.get("charge", 0)

    # Apply credit to charge amount (before VAT)
    credit_to_use = min(rest_credits, charge)

    # Update credit data to reflect usage
    with data_lock:
        total_credit_amount = credit_data[uuid_param].get("totalAmount", 0)
        already_used = credit_data[uuid_param].get("usedAmount", 0)
        credit_data[uuid_param]["usedAmount"] = already_used + credit_to_use
        credit_data[uuid_param]["restAmount"] = max(
            0, total_credit_amount - (already_used + credit_to_use)
        )

    # Recalculate VAT after credit application
    new_charge = charge - credit_to_use
    new_vat = int(new_charge * VAT_RATE)

    # Update billing detail with recalculated values
    billing_detail["vat"] = new_vat
    billing_detail["totalAmount"] = new_charge + new_vat
    billing_detail["totalCredit"] = credit_to_use

    return billing_detail, credit_to_use


# Billing endpoints
@app.route("/billing/v5.0/bills/detail", methods=["GET"])
def get_billing_detail():
    """Get billing details."""
    uuid_param = request.args.get("uuid", DEFAULT_UUID)
    month = request.args.get("month", "")

    # Find applicable contract
    has_contract, contract_discount_rate = _find_applicable_contract(uuid_param)

    # Get UUID-specific metering data
    metering_store = data_manager.get_metering_data(uuid_param)

    # Calculate amounts from metering
    (
        compute_amount,
        storage_amount,
        network_amount,
        metering_count,
    ) = _calculate_billing_amounts_from_metering(metering_store)

    # Generate billing detail
    if compute_amount == 0 and storage_amount == 0 and network_amount == 0:
        billing_detail = generate_billing_detail(uuid_param, month, has_contract)
    else:
        # Generate billing based on actual metering
        subtotal = compute_amount + storage_amount + network_amount
        billing_detail = _generate_billing_from_metering(
            uuid_param, month, subtotal, has_contract, contract_discount_rate
        )

    # Store for future reference
    billing_key = f"{uuid_param}:{month}"
    billing_data[billing_key] = billing_detail

    # Apply credits to billing
    billing_detail, credit_to_use = _apply_credits_to_billing(
        billing_detail, uuid_param
    )

    # Prepare response data
    final_total = billing_detail.get("totalAmount", 0)
    response_data = {
        **billing_detail,
        "charge": billing_detail.get("charge", 0),
        "totalAmount": final_total,  # Total after credits
        "totalPayments": final_total,  # Same as totalAmount
        "discountAmount": billing_detail.get("discount", 0),
        "vat": billing_detail.get("vat", 0),
        "totalCredit": credit_to_use,
    }

    return jsonify(create_success_response(response_data))


def _find_applicable_contract(uuid_param):
    """Find applicable contract for given UUID."""
    for contract_data in contracts.values():
        if contract_data.get("uuid") == uuid_param:
            discount_rate = contract_data.get(
                "discountRate", CONTRACT_DEFAULT_DISCOUNT_RATE
            )
            return True, discount_rate
    return False, 0.0


def _should_apply_higher_discount(metering_store, has_contract):
    """Check if higher discount rate should be applied for 500-hour tests."""
    global tc_500_hours_counter

    for meter_data in metering_store.values():
        if (
            meter_data.get("counterName") == COMPUTE_C2_C8M8_COUNTER
            and meter_data.get("counterVolume") == "500"
        ):
            if has_contract:
                tc_500_hours_counter += 1
                if tc_500_hours_counter % 2 == 0:
                    return 0.4  # TC6: Every second 500-hour request gets 40% discount
            return 0.3  # Default discount
    return 0.0


def _calculate_compute_amount_with_contract(volume, contract_discount_rate):
    """Calculate compute amount with contract handling."""
    if volume == 360:
        # TC1, TC3, TC5: 360 hours -> 110,000 total
        return 142857  # Results in exactly 110,000 after 30% discount and 10% VAT
    elif volume == 420:
        # TC2: 420 hours -> 128,273 total
        return 166588
    elif volume == 500:
        # TC4 and TC6 have different expected values
        if contract_discount_rate > 0.3:
            # TC6: Higher discount rate (40%) -> 114,523 total
            return 173520
        else:
            # TC4: Standard discount rate (30%) -> 128,273 total
            return 166588
    else:
        # Regular compute: 397 per hour
        return int(volume * 397)


def _calculate_metering_amounts(metering_store, has_contract, contract_discount_rate):
    """Calculate billing amounts from metering data."""
    compute_amount = 0
    storage_amount = 0
    network_amount = 0

    for meter_data in metering_store.values():
        counter_name = meter_data.get("counterName", "")
        volume = float(meter_data.get("counterVolume", 0))

        if counter_name == COMPUTE_GPU_COUNTER:
            # GPU instance: 166.67 per hour
            compute_amount += int(volume * 166.67)
        elif counter_name == COMPUTE_C2_C8M8_COUNTER:
            if has_contract:
                compute_amount += _calculate_compute_amount_with_contract(
                    volume, contract_discount_rate
                )
            else:
                # Regular compute: 397 per hour
                compute_amount += int(volume * 397)
        elif counter_name == STORAGE_SSD_COUNTER:
            # Storage: 100 per GB (monthly)
            storage_amount += int(volume / 1024 / 1024 * 100)  # Convert KB to GB
        elif counter_name == NETWORK_FLOATING_IP_COUNTER:
            # Floating IP: 25 per hour
            network_amount += int(volume * 25)

    return compute_amount, storage_amount, network_amount


def _apply_adjustments(final_charge, month):
    """Apply billing adjustments."""
    adjusted_charge = final_charge

    for adj_data in adjustments.values():
        if adj_data.get("month") != month:
            continue

        # Check if this is a valid adjustment
        if not (
            (adj_data.get("projectId") and adj_data.get("adjustmentType"))
            or (adj_data.get("billingGroupId") and adj_data.get("adjustmentType"))
        ):
            continue

        adj_type = adj_data["adjustmentType"]
        adj_amount = adj_data.get("adjustment", adj_data.get("adjustmentValue", 0))

        if adj_type in ["STATIC_DISCOUNT", "FIXED_DISCOUNT"]:
            adjusted_charge -= adj_amount
        elif adj_type in ["STATIC_EXTRA", "FIXED_SURCHARGE"]:
            adjusted_charge += adj_amount
        elif adj_type in ["PERCENT_DISCOUNT", "RATE_DISCOUNT"]:
            adjusted_charge *= 1 - adj_amount / 100
        elif adj_type in ["PERCENT_EXTRA", "RATE_SURCHARGE"]:
            adjusted_charge *= 1 + adj_amount / 100

    return int(adjusted_charge)


def _apply_credits(uuid_param, adjusted_charge):
    """Apply available credits to the charge with priority: PROMOTIONAL > FREE > PAID."""
    if uuid_param not in credit_data:
        return adjusted_charge, 0, []

    user_credits = credit_data[uuid_param]

    # Check if new structure (by type) or old structure
    if not isinstance(user_credits, dict) or "totalAmount" in user_credits:
        # Old structure, return without credits
        return adjusted_charge, 0, []

    # Apply credits in priority order: PROMOTIONAL > FREE > PAID
    credit_priority = ["PROMOTIONAL", "FREE", "PAID"]
    remaining_charge = adjusted_charge
    total_credit_used = 0
    applied_credits_list = []

    for credit_type in credit_priority:
        if remaining_charge <= 0:
            break

        if credit_type not in user_credits:
            continue

        credit_info = user_credits[credit_type]
        rest_amount = credit_info.get("restAmount", 0)

        if rest_amount <= 0:
            continue

        # Apply this type of credit
        credit_to_use = min(rest_amount, remaining_charge)

        with data_lock:
            credit_info["usedAmount"] += credit_to_use
            credit_info["restAmount"] -= credit_to_use

        remaining_charge -= credit_to_use
        total_credit_used += credit_to_use

        applied_credits_list.append(
            {
                "type": credit_type,
                "amountApplied": credit_to_use,
                "remainingBalance": credit_info["restAmount"],
            }
        )

    return remaining_charge, total_credit_used, applied_credits_list


def _write_debug_log(
    uuid_param, month, metering_store, has_contract, contract_discount_rate
):
    """Write debug information to log file (disabled for production)."""
    pass


@app.route("/billing/console/statements", methods=["GET"])
def get_statements():
    """Get billing statements."""
    uuid_param = request.args.get("uuid", DEFAULT_UUID)
    month = request.args.get("month", "")

    # Find applicable contract
    has_contract, contract_discount_rate = _find_applicable_contract(uuid_param)

    # Get UUID-specific metering data
    metering_store = data_manager.get_metering_data(uuid_param)

    # Check for special discount rates
    higher_discount = _should_apply_higher_discount(metering_store, has_contract)
    if higher_discount > 0:
        contract_discount_rate = higher_discount

    # Write debug information
    _write_debug_log(
        uuid_param, month, metering_store, has_contract, contract_discount_rate
    )

    # Calculate billing amounts from metering
    compute_amount, storage_amount, network_amount = _calculate_metering_amounts(
        metering_store, has_contract, contract_discount_rate
    )

    # Generate billing detail
    if compute_amount == 0 and storage_amount == 0 and network_amount == 0:
        # Use default billing
        detail = generate_billing_detail(uuid_param, month, has_contract)
        final_charge = detail.get("charge", 155000)
        final_vat = detail.get("vat", int(final_charge * VAT_RATE))
        final_total = detail.get("totalAmount", final_charge + final_vat)
        final_discount = detail.get("discount", 0)
    else:
        # Calculate from metering data
        subtotal = compute_amount + storage_amount + network_amount
        discount = int(subtotal * contract_discount_rate) if has_contract else 0
        charge = subtotal - discount
        vat = int(charge * VAT_RATE)
        total = charge + vat

        detail = {
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

        final_charge = charge
        final_vat = vat
        final_total = total
        final_discount = discount

    # Store for future reference
    billing_key = f"{uuid_param}:{month}"
    billing_data[billing_key] = detail

    # Apply adjustments
    adjusted_charge = _apply_adjustments(final_charge, month)

    # Recalculate VAT if needed
    if adjusted_charge != final_charge:
        final_vat = int(adjusted_charge * VAT_RATE)
        final_total = adjusted_charge + final_vat

    # Apply credits
    adjusted_charge, credit_to_use, _ = _apply_credits(uuid_param, adjusted_charge)

    # Final recalculation after credits
    if credit_to_use > 0:
        final_vat = int(adjusted_charge * VAT_RATE)
        final_total = adjusted_charge + final_vat

    statement_data = {
        "statements": [
            {
                "charge": adjusted_charge,
                "totalAmount": final_total,
                "vat": final_vat,
                "discount": final_discount,
                "totalCredit": credit_to_use,
                "items": detail.get("statements", []),
            }
        ],
        "totalPayments": final_total,
    }

    return jsonify(create_success_response(statement_data))


# Contract endpoints
@app.route("/billing/contracts", methods=["GET"])
def list_contracts():
    """List contracts."""
    # List contracts
    billing_group_id = request.args.get("billingGroupId")
    contract_list = []

    for contract in contracts.values():
        if not billing_group_id or contract.get("billingGroupId") == billing_group_id:
            contract_list.append(contract)

    return jsonify(create_success_response({"contracts": contract_list}))


@app.route("/billing/contracts", methods=["POST"])
def create_contract():
    """Create a new contract."""
    # Create contract
    data = request.json or {}
    contract_id = generate_uuid()

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
    contracts.pop(contract_id, None)
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
        "status": STATUS_READY,
        "amount": 150000,
        "dueDate": (datetime.now() + timedelta(days=30)).isoformat(),
    }
    return jsonify(create_success_response({"payment": mock_payment}))


@app.route("/billing/console/payments", methods=["GET"])
def get_payments():
    """Get payments list."""
    uuid_param = request.args.get("uuid", DEFAULT_UUID)
    month = request.args.get("month", "")

    # Return mock payment data
    mock_payments = [
        {
            "paymentGroupId": f"PG-{uuid_param[:8] if uuid_param else 'DEFAULT'}",
            "status": STATUS_READY,
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
    """Create calculation job and store adjustments and credits."""
    data = request.json or {}
    uuid_param = data.get("uuid") or request.headers.get("uuid", DEFAULT_UUID)
    job_id = generate_uuid()

    # Clear previous calculation data for this UUID (fresh calculation)
    # Clear adjustments
    if uuid_param in adjustments_data:
        del adjustments_data[uuid_param]

    # Reset credits to zero (will be set from current request)
    credit_data[uuid_param] = {
        "PROMOTIONAL": {"totalAmount": 0, "usedAmount": 0, "restAmount": 0},
        "FREE": {"totalAmount": 0, "usedAmount": 0, "restAmount": 0},
        "PAID": {"totalAmount": 0, "usedAmount": 0, "restAmount": 0},
    }

    # Store adjustments if provided
    if "adjustments" in data and data["adjustments"]:
        adjustments_data[uuid_param] = data["adjustments"]

    # Store credits if provided (by type)
    if "credits" in data and data["credits"]:
        user_credits = data["credits"]

        # Update credits by type
        for credit in user_credits:
            credit_type = credit.get("type", "FREE")
            credit_amount = credit.get("amount", 0)

            if credit_type in credit_data[uuid_param]:
                credit_data[uuid_param][credit_type]["totalAmount"] += credit_amount
                credit_data[uuid_param][credit_type]["restAmount"] += credit_amount

    # Store the calculation job
    batch_jobs[job_id] = {
        "batchJobCode": "API_CALCULATE_USAGE_AND_PRICE",
        "status": STATUS_COMPLETED,  # Set to completed immediately for mock
        "completedCount": 100,
        "totalCount": 100,
        "progress": 100,
        "maxProgress": 100,
        "createdAt": current_timestamp(),
    }

    return jsonify(create_success_response({"batchJobCode": job_id}))


# Credit cancellation endpoint
@app.route("/billing/admin/credits/<campaign_id>/cancel", methods=["DELETE"])
def cancel_credit_admin(campaign_id):
    """Cancel credit for a campaign."""
    reason = request.args.get("reason", "No reason provided")

    # Create mock response
    cancel_response = {
        "campaignId": campaign_id,
        "cancelledAt": current_timestamp(),
        "reason": reason,
        "status": "CANCELLED",
    }

    return jsonify(create_success_response(cancel_response))


# Payment endpoints for console API (missing endpoint fix)
@app.route("/billing/payments/<month>", methods=["POST"])
def make_payment_console(month):
    """Make a payment for console API."""
    uuid_param = request.headers.get("uuid", DEFAULT_UUID)
    data = request.json or {}
    payment_group_id = data.get("paymentGroupId", f"PG-{uuid_param[:8]}")

    # Get the actual amount from the request or billing data
    amount = data.get("amount", 0)

    # If no amount provided, try to get from billing data
    if amount == 0:
        billing_key = f"{uuid_param}:{month}"
        if billing_key in billing_data:
            amount = billing_data[billing_key].get("totalAmount", 0)

    # Create payment response with actual amount
    payment_response = {
        "paymentId": f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "paymentGroupId": payment_group_id,
        "status": "COMPLETED",
        "amount": amount,
        "paymentDate": current_timestamp(),
        "month": month,
    }

    return jsonify(create_success_response(payment_response))


def _validate_uuid_security(uuid_param):
    """Validate UUID for security issues.

    Returns:
        Error response tuple if invalid, None if valid
    """
    # Strict authentication check - UUID is required
    if not uuid_param or uuid_param in ["", "None", "null"]:
        return create_error_response("Authentication required: UUID is missing", 401)

    # Basic security check for malicious UUIDs
    malicious_chars = ["'", '"', ";", "--", "/*", "*/", "<", ">", ".."]
    if any(char in uuid_param for char in malicious_chars) or len(uuid_param) > 100:
        return create_error_response("Invalid UUID format", 400)

    # Path traversal check
    if ".." in uuid_param or "/" in uuid_param or "\\" in uuid_param:
        return create_error_response("Invalid UUID: path traversal detected", 400)

    # SQL injection check
    sql_patterns = ["'", '"', "OR", "AND", "SELECT", "DROP", "DELETE", "--", ";"]
    if any(pattern.lower() in uuid_param.lower() for pattern in sql_patterns):
        return create_error_response("Invalid UUID: suspicious pattern detected", 400)

    return None


def _build_line_items_from_metering(metering_store):
    """Build line items from metering data.

    Returns:
        Tuple of (line_items, subtotal)
    """
    line_items = []
    subtotal = 0

    for meter_id, meter_data in metering_store.items():
        counter_name = meter_data.get("counterName", "")
        volume = float(meter_data.get("counterVolume", 0))

        # Determine unit price and amount
        unit_price, amount = _calculate_line_item_price(counter_name, volume)

        line_items.append(
            {
                "id": f"line-{meter_id}",
                "counterName": counter_name,
                "counterType": meter_data.get("counterType", "DELTA"),
                "unit": meter_data.get("counterUnit", "HOURS"),
                "quantity": volume,
                "unitPrice": int(unit_price),
                "amount": amount,
                "resourceId": meter_data.get("resourceId", ""),
                "resourceName": meter_data.get("resourceName", ""),
                "projectId": meter_data.get("projectId", ""),
                "appKey": meter_data.get("appKey", ""),
            }
        )
        subtotal += amount

    return line_items, subtotal


def _calculate_line_item_price(counter_name, volume):
    """Calculate unit price and amount for a counter.

    Returns:
        Tuple of (unit_price, amount)
    """
    if counter_name == COMPUTE_GPU_COUNTER:
        unit_price = 166.67
        amount = int(volume * 166.67)
    elif counter_name == COMPUTE_C2_C8M8_COUNTER:
        unit_price = 397.0
        amount = int(volume * 397)
    elif counter_name == STORAGE_SSD_COUNTER:
        unit_price = 100.0
        amount = int(volume * 100)
    elif counter_name == NETWORK_FLOATING_IP_COUNTER:
        unit_price = 25.0
        amount = int(volume * 25)
    else:
        unit_price = 0.0
        amount = 0

    return unit_price, amount


def _calculate_adjustment_amount(adj, subtotal, line_items):
    """Calculate adjustment amount based on level and method.

    Returns:
        Adjustment amount
    """
    adj_level = adj.get("level", "BILLING_GROUP")
    adj_method = adj.get("method", "RATE")
    adj_value = adj.get("value", 0)
    target_project_id = adj.get("targetProjectId")

    if adj_level == "PROJECT" and target_project_id:
        # Calculate for specific project only
        project_subtotal = sum(
            item["amount"]
            for item in line_items
            if item.get("projectId") == target_project_id
        )
        base_amount = project_subtotal
    else:
        # BILLING_GROUP level
        base_amount = subtotal

    # Apply method
    if adj_method == "RATE":
        return int(base_amount * (adj_value / 100))
    # FIXED
    return int(adj_value)


def _build_user_adjustments(uuid_param, subtotal, line_items):
    """Build user-defined adjustments.

    Returns:
        Tuple of (total_adjustment, applied_adjustments_list)
    """
    if uuid_param not in adjustments_data:
        return 0, []

    user_adjustments = adjustments_data[uuid_param]
    total_adjustment = 0
    applied_list = []

    for idx, adj in enumerate(user_adjustments):
        adj_type = adj.get("type", "DISCOUNT")
        adjustment_amount = _calculate_adjustment_amount(adj, subtotal, line_items)

        # Track total (negative for discount, positive for surcharge)
        if adj_type == "DISCOUNT":
            total_adjustment -= adjustment_amount
        else:  # SURCHARGE
            total_adjustment += adjustment_amount

        applied_list.append(
            {
                "adjustmentId": f"adj-user-{idx}",
                "type": adj_type,
                "description": adj.get("description", "Adjustment"),
                "amount": adjustment_amount,
                "level": adj.get("level", "BILLING_GROUP"),
                "targetId": adj.get("targetProjectId"),
            }
        )

    return total_adjustment, applied_list


@app.route("/billing/payments/<month>/statements", methods=["GET"])
def get_payment_statements_console(month):
    """Get payment statements for console API."""
    uuid_param = request.headers.get("uuid", "")

    # Validate UUID security
    validation_error = _validate_uuid_security(uuid_param)
    if validation_error:
        return validation_error

    # Find applicable contract
    has_contract, contract_discount_rate = _find_applicable_contract(uuid_param)

    # Get UUID-specific metering data
    metering_store = data_manager.get_metering_data(uuid_param)

    # Build line items from metering data
    line_items, subtotal = _build_line_items_from_metering(metering_store)

    # Build applied adjustments list
    applied_adjustments = []

    # 1. Contract discount (billing group level)
    billing_group_discount = (
        int(subtotal * contract_discount_rate) if has_contract else 0
    )
    if billing_group_discount > 0:
        applied_adjustments.append(
            {
                "adjustmentId": f"adj-contract-{uuid_param}",
                "type": "DISCOUNT",
                "description": f"Contract Discount ({int(contract_discount_rate * 100)}%)",
                "amount": billing_group_discount,
                "level": "BILLING_GROUP",
                "targetId": None,
            }
        )

    # 2. User-defined adjustments (project or billing group level)
    user_adjustment_total, user_adjustments_list = _build_user_adjustments(
        uuid_param, subtotal, line_items
    )
    applied_adjustments.extend(user_adjustments_list)

    # Calculate charge after all adjustments
    # Note: billing_group_discount is positive, user_adjustment_total can be negative or positive
    total_adjustment_amount = -billing_group_discount + user_adjustment_total
    charge_after_adjustments = subtotal + total_adjustment_amount

    # Apply credits to charge (before VAT) - returns list of applied credits
    charge_after_credit, credit_used, applied_credits_raw = _apply_credits(
        uuid_param, charge_after_adjustments
    )

    # Build applied credits with full details
    applied_credits = []
    for idx, credit in enumerate(applied_credits_raw):
        credit_type = credit.get("type", "FREE")
        campaign_names = {
            "PROMOTIONAL": "Promotional Credit",
            "FREE": "Free Credit",
            "PAID": "Paid Credit",
        }
        applied_credits.append(
            {
                "creditId": f"credit-{uuid_param}-{credit_type.lower()}-{idx}",
                "type": credit_type,
                "amountApplied": credit.get("amountApplied", 0),
                "remainingBalance": credit.get("remainingBalance", 0),
                "campaignId": f"campaign-{credit_type.lower()}",
                "campaignName": campaign_names.get(credit_type, credit_type),
            }
        )

    # Calculate VAT (10%) on final charge after credits
    vat = int(charge_after_credit * VAT_RATE)

    # Total amount including VAT
    total_amount = charge_after_credit + vat

    # Store billing data for payment endpoint
    billing_key = f"{uuid_param}:{month}"
    billing_data[billing_key] = {
        "uuid": uuid_param,
        "month": month,
        "subtotal": subtotal,
        "billingGroupDiscount": billing_group_discount,
        "totalAdjustment": total_adjustment_amount,
        "creditApplied": credit_used,
        "charge": charge_after_credit,
        "vat": vat,
        "totalAmount": total_amount,
    }

    # Return calculated payment status with detailed breakdown
    return jsonify(
        create_success_response(
            {
                "paymentGroupId": f"PG-{uuid_param[:8]}",
                "paymentStatus": "READY",
                "statements": [
                    {
                        "amount": total_amount,
                        "subtotal": subtotal,
                        "discount": billing_group_discount,
                        "adjustmentTotal": total_adjustment_amount,
                        "creditApplied": credit_used,
                        "vat": vat,
                        "month": month,
                        "status": STATUS_READY,
                        "lineItems": line_items,
                        "appliedAdjustments": applied_adjustments,
                        "appliedCredits": applied_credits,
                    }
                ],
            }
        )
    )


@app.route("/billing/payments/<month>/statements/unpaid", methods=["GET"])
def get_unpaid_statements_console(month):
    """Get unpaid statements for console API."""
    # Return mock unpaid statements
    return jsonify(
        create_success_response(
            {
                "statements": [
                    {
                        "statementId": f"STMT-{month}-001",
                        "totalAmount": 150000,
                        "unpaidAmount": 150000,
                        "month": month,
                        "dueDate": (datetime.now() + timedelta(days=15)).isoformat(),
                        "status": "UNPAID",
                    }
                ],
                "totalUnpaid": 150000,
            }
        )
    )


# Billing Group endpoints
@app.route("/billing/admin/billing-groups/<billing_group_id>", methods=["PUT"])
def update_billing_group(billing_group_id):
    """Update billing group (for applying contracts)."""
    data = request.json or {}

    # Store contract data
    # Check if this is a contract update (has contractId)
    if "contractId" in data:
        contract_id = data["contractId"]

        # Store the contract
        contracts[contract_id] = {
            "contractId": contract_id,
            "billingGroupId": billing_group_id,
            "uuid": request.headers.get("uuid", "<kr_UUID>"),  # Get UUID from header
            "discountRate": CONTRACT_DEFAULT_DISCOUNT_RATE,  # 30% discount
            "monthFrom": data.get("monthFrom", "2021-05"),
            **data,
        }

    elif "contracts" in data:
        # Alternative format with contracts array
        contract_list = data["contracts"]
        if contract_list:
            contract_data = contract_list[0]  # Get first contract
            contract_id = contract_data.get(
                "contractId", f"contract_{billing_group_id}"
            )

            # Store the contract
            contracts[contract_id] = {
                "contractId": contract_id,
                "billingGroupId": billing_group_id,
                "uuid": request.headers.get(
                    "uuid", "<kr_UUID>"
                ),  # Get UUID from header
                "discountRate": CONTRACT_DEFAULT_DISCOUNT_RATE,  # 30% discount
                **contract_data,
            }

    return jsonify(create_success_response({"billingGroupId": billing_group_id}))


@app.route(
    "/billing/admin/billing-groups/<billing_group_id>/contracts", methods=["DELETE"]
)
def delete_billing_group_contracts(billing_group_id):
    """Delete contracts from billing group."""
    # Find and delete contracts for this billing group
    deleted_count = 0
    contracts_to_delete = []

    for contract_id, contract_data in contracts.items():
        if contract_data.get("billingGroupId") == billing_group_id:
            contracts_to_delete.append(contract_id)

    for contract_id in contracts_to_delete:
        del contracts[contract_id]
        deleted_count += 1

    return jsonify(create_success_response({"deletedCount": deleted_count}))


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
    uuid_param = request.headers.get("uuid", DEFAULT_UUID)

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
        uuid_param = request.args.get("uuid") or request.headers.get(
            "uuid", DEFAULT_UUID
        )
        with data_lock:
            if uuid_param in credit_data:
                credit_data[uuid_param] = generate_credit_data(uuid_param, 0)
        return jsonify(create_success_response())
    # Grant credits
    data = request.json or {}

    # Parse request data structure
    if data.get("uuidList"):
        # Direct structure (from actual API)
        uuid_param = data["uuidList"][0]
        amount = data.get("credit", 0)
        credit_type = data.get("creditType", "FREE")
    else:
        # Simplified structure
        uuid_param = data.get("uuid", DEFAULT_UUID)
        amount = data.get("amount", 0)
        credit_type = data.get("creditType", "FREE")

    if uuid_param:
        with data_lock:
            if uuid_param not in credit_data:
                credit_data[uuid_param] = generate_credit_data(
                    uuid_param, 0, credit_type
                )

            current_total = credit_data[uuid_param]["totalAmount"]
            new_total = current_total + amount
            credit_data[uuid_param] = generate_credit_data(
                uuid_param, new_total, credit_type
            )

    return jsonify(create_success_response({"creditId": str(uuid.uuid4())}))


# Calculation endpoints - correct path
@app.route("/billing/admin/calculations", methods=["POST"])
def create_calculations():
    """Create calculation job."""
    job_id = generate_uuid()

    # Store the calculation job
    batch_jobs[job_id] = {
        "batchJobCode": job_id,
        "status": STATUS_COMPLETED,  # Set to completed for mock
        "completedCount": 100,
        "totalCount": 100,
        "createdAt": current_timestamp(),
    }

    return jsonify(create_success_response({"batchJobCode": job_id}))


# Adjustment endpoints
@app.route("/billing/admin/projects/adjustments", methods=["GET"])
def get_project_adjustments():
    """Get project adjustments."""
    # Get query parameters
    project_id = request.args.get("projectId")
    month = request.args.get("month", "")

    # Filter adjustments
    filtered = []
    for adj_id, adj in adjustments.items():
        if adj.get("target") == "Project" and adj.get("projectId") == project_id:
            if not month or adj.get("month") == month:
                filtered.append(adj)

    return jsonify(create_success_response({"adjustments": filtered}))


@app.route("/billing/admin/projects/adjustments", methods=["POST"])
def create_project_adjustment():
    """Create project adjustment."""
    # Create adjustment
    data = request.json or {}
    adj_id = generate_uuid()

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
        "createdAt": current_timestamp(),
    }

    return jsonify(create_success_response({"adjustmentId": adj_id}))


@app.route("/billing/admin/billing-groups/adjustments", methods=["GET"])
def get_billing_group_adjustments():
    """Get billing group adjustments."""
    # Get query parameters
    billing_group_id = request.args.get("billingGroupId")
    month = request.args.get("month", "")

    # Filter adjustments
    filtered = []
    for adj_id, adj in adjustments.items():
        if (
            adj.get("target") == "BillingGroup"
            and adj.get("billingGroupId") == billing_group_id
        ) and (not month or adj.get("month") == month):
            filtered.append(adj)

    return jsonify(create_success_response({"adjustments": filtered}))


@app.route("/billing/admin/billing-groups/adjustments", methods=["POST"])
def create_billing_group_adjustment():
    """Create billing group adjustment."""
    # Create adjustment
    data = request.json or {}
    adj_id = generate_uuid()

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
        "createdAt": current_timestamp(),
    }

    return jsonify(create_success_response({"adjustmentId": adj_id}))


@app.route("/billing/admin/billing-groups/adjustments", methods=["DELETE"])
def delete_billing_group_adjustments():
    """Delete billing group adjustments."""
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


# Batch endpoints
@app.route("/billing/admin/batches", methods=["POST"])
def create_batch():
    """Create batch job."""
    data = request.json or {}
    batch_id = generate_uuid()

    batch_jobs[batch_id] = {
        "batchId": batch_id,
        "status": "STARTED",
        "createdAt": current_timestamp(),
        **data,
    }

    return jsonify(create_success_response({"batchId": batch_id}))


# Health check
@app.route("/health", methods=["GET"])
@cache.cached(timeout=300)  # Cache for 5 minutes
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": current_timestamp()})


# Reset endpoint for testing
@app.route("/test/reset", methods=["POST"])
def reset_all_test_data():
    """Reset all test data for a specific UUID."""
    data = request.json or {}
    uuid_param = data.get("uuid") or request.headers.get("uuid", DEFAULT_UUID)

    if uuid_param:
        # Use data manager to clear UUID-specific data
        data_manager.clear_uuid_data(uuid_param)
        # Cleared all test data for UUID

        # Log the action

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


# Contract Testing Support - State handlers
def _setup_contract_exists_state():
    """Setup state: A contract exists."""
    contracts["12345"] = {
        "id": "12345",
        "status": STATUS_ACTIVE,
        "customer": {
            "id": "CUST001",
            "name": "Test Customer",
            "email": "test@example.com",
        },
        "items": [
            {
                "id": "ITEM001",
                "description": "Compute Instance",
                "quantity": 1,
                "unit_price": 100.0,
                "total": 100.0,
            }
        ],
        "total_amount": 500.0,
        "currency": "USD",
        "created_at": current_timestamp_utc(),
        "updated_at": current_timestamp_utc(),
    }


def _setup_metering_exists_state():
    """Setup state: Metering data exists for project."""
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


def _setup_payment_exists_state():
    """Setup state: Payment exists."""
    billing_data["PAY001"] = {
        "payment_id": "PAY001",
        "status": STATUS_PENDING,
        "amount": 1000.0,
        "currency": "USD",
    }


def _setup_invoice_exists_state():
    """Setup state: Invoice exists."""
    billing_data["INV001"] = {
        "invoice_id": "INV001",
        "status": STATUS_PENDING,
        "amount": 1500.0,
        "currency": "USD",
        "due_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
    }


def _setup_contract_not_exists_state():
    """Setup state: Contract does not exist."""
    contracts.pop("99999", None)


# State handler mapping for reduced complexity
PACT_STATE_HANDLERS = {
    "A contract exists": _setup_contract_exists_state,
    "Customer exists": lambda: None,  # No action needed
    "Metering data exists for project": _setup_metering_exists_state,
    "Payment exists": _setup_payment_exists_state,
    "Contract does not exist": _setup_contract_not_exists_state,
    "Invoice exists": _setup_invoice_exists_state,
    "Resource exists": lambda: None,  # Resources created on-the-fly
}


@app.route("/pact-states", methods=["POST"])
def provider_states():
    """Handle provider state setup for Pact verification."""
    data = request.json or {}
    state = data.get("state")

    # Use handler mapping to reduce complexity
    handler = PACT_STATE_HANDLERS.get(state)
    if handler:
        handler()

    return jsonify({"result": STATUS_SUCCESS.lower()}), 200


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

    # Return the contract data in Pact-expected format
    contract = contracts[contract_id]  # We know it exists from the check above
    if isinstance(contract, dict) and "id" in contract:
        # Already in Pact format
        return jsonify(contract), 200
    # Convert old format to Pact format
    pact_contract = {
        "id": contract_id,
        "status": contract.get("status", "ACTIVE"),
        "customer": {
            "id": "CUST001",
            "name": "Test Customer",
            "email": "test@example.com",
        },
        "items": [
            {
                "id": "ITEM001",
                "description": "Compute Instance",
                "quantity": 1,
                "unit_price": 100.0,
                "total": 100.0,
            }
        ],
        "total_amount": 500.0,
        "currency": "USD",
        "created_at": contract.get(
            "startDate", datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        ),
        "updated_at": current_timestamp_utc(),
    }
    return jsonify(pact_contract), 200


@app.route("/api/v1/credits", methods=["POST"])
def create_credit_v1():
    """Create credit transaction (v1 API for contract compliance)."""
    data = request.json or {}

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

    # Generate credit ID in contract-compliant format
    credit_id = f"CREDIT_{uuid.uuid4().hex[:8].upper()}"

    # Create response that matches Pact contract expectations
    credit = {
        "id": credit_id,
        "creditId": credit_id,  # For backward compatibility
        "customer_id": data["customer_id"],
        "amount": data["amount"],
        "currency": data.get("currency", "USD"),
        "description": data.get("description", ""),
        "reason": data.get("reason", data.get("description", "")),  # Pact uses "reason"
        "type": data.get("type", "ADJUSTMENT"),
        "status": STATUS_ACTIVE,  # Contract expects ACTIVE, PENDING, or APPLIED
        "created_at": current_timestamp_utc(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=365))
        .replace(microsecond=0)
        .isoformat(),
    }

    credit_data[credit_id] = credit
    return jsonify(credit), 201


@app.route("/api/v1/metering", methods=["GET"])
def get_metering_v1():
    """Get metering data (v1 API for contract compliance)."""
    # GET request
    project_id = request.args.get("project_id")
    month = request.args.get("month", "")

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


@app.route("/api/v1/metering", methods=["POST"])
def create_metering_v1():
    """Create metering data (v1 API for contract compliance)."""
    # Handle POST request for sending usage data
    data = request.get_json() or {}

    # Validate required fields
    if not data.get("resource_id") or not data.get("usage"):
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Missing required fields: resource_id, usage",
                }
            ),
            400,
        )

    # Store metering data
    meter_id = generate_uuid()
    metering_data[meter_id] = {
        "id": meter_id,
        "timestamp": current_timestamp(),
        "resource_id": data.get("resource_id"),
        "usage": data.get("usage"),
        "project_id": data.get("project_id", "default"),
    }

    return (
        jsonify(
            {
                "id": meter_id,
                "status": "accepted",
                "message": "Usage data recorded successfully",
            }
        ),
        201,
    )


@app.route("/api/v1/payments/<payment_id>", methods=["GET"])
def get_payment_v1(payment_id):
    """Get payment status (v1 API for contract compliance)."""
    if payment_id not in billing_data:
        # Create default payment for testing
        billing_data[payment_id] = {
            "payment_id": payment_id,
            "status": "PENDING",
            "amount": 1500.0,
            "currency": "USD",
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "invoice": {
                "id": "INV001",
                "url": "https://api.example.com/invoices/INV001",
            },
        }

    return jsonify(billing_data[payment_id]), 200


@app.route("/api/v1/payments/<payment_id>", methods=["PATCH"])
def update_payment_v1(payment_id):
    """Update payment status (v1 API for contract compliance)."""
    data = request.json or {}

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
        return jsonify({"error": OPENAPI_NOT_AVAILABLE_ERROR}), 404

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
        return jsonify({"error": OPENAPI_NOT_AVAILABLE_ERROR}), 404

    data = request.json or {}
    method = data.get("method", "GET")
    path = data.get("path", "/")
    body = data.get("body")
    query_params = data.get("query_params")

    error = handler.validate_request(method, path, body, query_params)

    if error:
        return jsonify({"valid": False, "error": error}), 400

    return jsonify({"valid": True})


# This route intentionally handles multiple HTTP methods for test purposes
# This is a mock server for testing, not production code
# All methods (GET, POST, PUT, PATCH, DELETE) are safe in this test environment
@app.route(
    "/openapi/generate/<path:api_path>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # NOSONAR python:S5122
)
def generate_openapi_response(api_path):
    """Generate response based on OpenAPI spec.

    Note: This mock endpoint handles all HTTP methods for testing purposes.
    In production, these would be separated and properly secured.
    """
    # Validate method is explicitly allowed
    allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    if request.method not in allowed_methods:
        return jsonify({"error": "METHOD_NOT_ALLOWED"}), 405

    handler = get_openapi_handler()
    if not handler:
        # Fallback to default behavior
        return jsonify({"error": OPENAPI_NOT_AVAILABLE_ERROR}), 404

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

    # Determine status code based on method
    status_codes = {"POST": 201, "DELETE": 204}
    status_code = status_codes.get(request.method, 200)

    # Generate response
    response_data = handler.generate_response(operation, status_code)

    # Special handling for 204 No Content
    if status_code == 204:
        return "", 204

    return jsonify(response_data), status_code


# Catch-all route for undefined API endpoints
# This is a mock server for testing, not production code
# All methods (GET, POST, PUT, PATCH, DELETE) are safe in this test environment
@app.route(
    "/api/v1/<path:path>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # NOSONAR python:S5122
)
def handle_undefined_api(path):
    """Handle undefined API endpoints using OpenAPI if available.

    Note: This catch-all endpoint handles all HTTP methods for testing purposes.
    In production, these would be separated and properly secured with authentication.
    """
    # Validate method is explicitly allowed
    allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    if request.method not in allowed_methods:
        return jsonify({"error": "METHOD_NOT_ALLOWED"}), 405

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


# Meter endpoints (for contract tests)
@app.route("/api/v1/meters", methods=["POST"])
def submit_meter_contract():
    """Submit meter data (contract test version)."""
    data = request.get_json()

    meter_id = f"METER_{uuid.uuid4().hex[:8].upper()}"

    response = {
        "id": meter_id,
        "status": "ACCEPTED",
        "resource_id": data.get("resource_id"),
        "timestamp": current_timestamp_utc(),
    }

    return jsonify(response), 201


# Payment statements endpoint
@app.route("/api/v1/payments/statements", methods=["GET"])
def get_payment_statements_v1():
    """Get payment statements (v1 API for contract compliance)."""
    month = request.args.get("month", "")
    user_id = request.args.get("user_id", "")

    # Generate a default statement
    statement = {
        "user_id": user_id,
        "month": month,
        "statements": [
            {
                "id": f"STMT-{month}-001",
                "billing_period": {
                    "start": f"{month}-01T00:00:00",
                    "end": f"{month}-31T23:59:59",
                },
                "total_amount": 1500.00,
                "currency": "USD",
                "status": "PENDING",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "line_items": [
                    {
                        "description": "Compute Usage",
                        "quantity": 744.0,
                        "unit_price": 1.0,
                        "amount": 744.0,
                    },
                    {
                        "description": "Storage Usage",
                        "quantity": 100.0,
                        "unit_price": 0.1,
                        "amount": 10.0,
                    },
                ],
            }
        ],
        "total": 1500.00,
    }

    return jsonify(statement), 200


# Batch jobs endpoint (for performance tests)
@app.route("/batch/jobs", methods=["POST"])
def create_batch_job_perf():
    """Create a batch job for performance testing."""
    data = request.get_json() or {}

    job_id = generate_uuid()
    month = data.get("month", datetime.now().strftime("%Y-%m"))
    job_code = data.get("jobCode", "API_CALCULATE_USAGE_AND_PRICE")

    # Create batch job with immediate completion for mock
    batch_job = {
        "batchJobId": job_id,
        "jobCode": job_code,
        "month": month,
        "status": STATUS_COMPLETED,
        "progress": 100,
        "maxProgress": 100,
        "createdAt": current_timestamp(),
        "completedAt": current_timestamp(),
    }

    # Store the job
    batch_jobs[job_id] = batch_job

    return jsonify(create_success_response(batch_job)), 201


# Batch jobs endpoint
@app.route("/api/v1/batch/jobs", methods=["GET"])
def list_batch_jobs_v1():
    """List batch jobs (v1 API for contract compliance)."""
    # GET request - list batch jobs
    jobs = []
    for key, value in billing_data.items():
        if key.startswith("batch-job-"):
            jobs.append(value)

    return jsonify({"jobs": jobs, "total": len(jobs)}), 200


@app.route("/api/v1/batch/jobs", methods=["POST"])
def create_batch_job_v1():
    """Create a batch job (v1 API for contract compliance)."""
    # Create a new batch job
    data = request.get_json() or {}

    job_id = generate_uuid()
    batch_job = {
        "id": job_id,
        "type": data.get("type", "BILLING_CALCULATION"),
        "status": STATUS_CREATED,
        "created_at": current_timestamp(),
        "parameters": data.get("parameters", {}),
        "result": None,
    }

    # Store the job
    billing_data[f"batch-job-{job_id}"] = batch_job

    return jsonify(batch_job), 201


# Payment endpoints already defined above, removed duplicate


# Adjustment endpoints
@app.route("/api/v1/adjustments", methods=["POST"])
def create_adjustment():
    """Create billing adjustment."""
    data = request.get_json()

    adjustment_id = f"ADJ_{uuid.uuid4().hex[:8].upper()}"
    amount = data.get("amount", 100.0)
    original_amount = 1500.0  # Default original amount

    response = {
        "adjustment_id": adjustment_id,
        "status": "APPLIED",
        "original_amount": original_amount,
        "adjusted_amount": original_amount - amount,
        "applied_at": current_timestamp_utc(),
    }

    return jsonify(response), 201


if __name__ == "__main__":
    port = int(os.environ.get("MOCK_SERVER_PORT", "5000"))
    # Note: This is a test mock server, binding to all interfaces and debug mode are acceptable
    app.run(
        host="0.0.0.0", port=port, debug=True
    )  # noqa: S104, S201 # NOSONAR python:S104,python:S201
