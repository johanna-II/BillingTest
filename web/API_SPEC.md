# API Specification

## Mock Server API Endpoints

### 1. Metering (Usage Submission)

```http
POST /billing/meters
Content-Type: application/json
uuid: {uuid}

{
  "meterList": [
    {
      "appKey": "app-kr-master-001",
      "counterName": "compute.c2.c8m8",
      "counterType": "DELTA",
      "counterUnit": "HOURS",
      "counterVolume": 100,
      "resourceId": "resource-001",
      "resourceName": "Test Resource",
      "projectId": "project-001",
      "timestamp": "2025-10-04T00:00:00.000Z",
      "source": "web.billing.calculator"
    }
  ]
}
```

**Response:**

```json
{
  "header": {
    "isSuccessful": true,
    "resultCode": "0",
    "resultMessage": "SUCCESS"
  },
  "message": "Created 1 meters",
  "meterIds": ["meter-uuid-1"]
}
```

### 2. Calculate (Execute Calculation)

```http
POST /billing/admin/calculate
Content-Type: application/json
uuid: {uuid}

{
  "month": "2025-10",
  "uuid": "test-uuid-001",
  "billingGroupId": "bg-kr-test"
}
```

**Response:**

```json
{
  "header": {
    "isSuccessful": true,
    "resultCode": "0",
    "resultMessage": "SUCCESS"
  },
  "batchJobCode": "job-uuid"
}
```

### 3. Get Statements (Retrieve Statements)

```http
GET /billing/payments/{month}/statements?uuid={uuid}
uuid: {uuid}
```

**Response:**

```json
{
  "header": {
    "isSuccessful": true,
    "resultCode": "0",
    "resultMessage": "SUCCESS"
  },
  "statements": [
    {
      "statementId": "stmt-001",
      "uuid": "test-uuid-001",
      "billingGroupId": "bg-kr-test",
      "month": "2025-10",
      "billingAmount": 100000,
      "totalAmount": 100000,
      "status": "PENDING",
      "lineItems": [],
      "dueDate": "2025-11-04T00:00:00Z"
    }
  ]
}
```

### 4. Process Payment (Payment Processing)

```http
POST /billing/payments/{month}
Content-Type: application/json
uuid: {uuid}

{
  "paymentGroupId": "bg-kr-test",
  "amount": 100000
}
```

**Response:**

```json
{
  "header": {
    "isSuccessful": true,
    "resultCode": "0",
    "resultMessage": "SUCCESS"
  },
  "paymentId": "pay-001",
  "status": "COMPLETED",
  "paymentMethod": "CREDIT_CARD",
  "amount": 100000,
  "transactionId": "txn-001",
  "paymentDate": "2025-10-04T12:00:00Z",
  "month": "2025-10"
}
```

## Web UI to Mock Server Flow

```text
1. User Input
   ↓
2. POST /api/billing/meters (Frontend)
   ↓ (Proxy)
3. POST /billing/meters (Mock Server)
   ↓
4. POST /api/billing/admin/calculate (Frontend)
   ↓ (Proxy)
5. POST /billing/admin/calculate (Mock Server)
   ↓
6. GET /api/billing/payments/{month}/statements (Frontend)
   ↓ (Proxy)
7. GET /billing/payments/{month}/statements (Mock Server)
   ↓
8. Display Statement
   ↓
9. POST /api/billing/payments/{month} (Frontend)
   ↓ (Proxy)
10. POST /billing/payments/{month} (Mock Server)
   ↓
11. Display Payment Result
```

## Next.js API Routes (CORS Bypass)

### `/api/billing/meters`

- Proxies to `POST /billing/meters`
- Adds CORS headers

### `/api/billing/admin/calculate`

- Proxies to `POST /billing/admin/calculate`

### `/api/billing/payments/{month}/statements`

- Proxies to `GET /billing/payments/{month}/statements`

### `/api/billing/payments/{month}`

- Proxies to `POST /billing/payments/{month}`

## Calculation Logic

```javascript
const subtotal = lineItems.reduce((sum, item) => sum + item.amount, 0)
const adjustmentTotal = adjustments.reduce((sum, adj) => sum + adj.amount, 0)
const creditApplied = credits.reduce(...)
const total = subtotal + adjustmentTotal - creditApplied + unpaid + lateFee
```

### Error Response Format

```json
{
  "header": {
    "isSuccessful": false,
    "resultCode": "400",
    "resultMessage": "ERROR"
  },
  "error": "Additional error details"
}
```

## Testing Methods

### 1. Health Check

```bash
curl http://localhost:5000/health
```

### 2. Metering Test

```bash
curl -X POST http://localhost:5000/billing/meters \
  -H "Content-Type: application/json" \
  -H "uuid: test-uuid-001" \
  -d '{"meterList":[{"appKey":"app-kr-master-001","counterName":"test","counterVolume":100}]}'
```

### 3. Calculate Test

```bash
curl -X POST http://localhost:5000/billing/admin/calculate \
  -H "Content-Type: application/json" \
  -H "uuid: test-uuid-001" \
  -d '{"month":"2025-10","uuid":"test-uuid-001","billingGroupId":"bg-kr-test"}'
```

### 4. Statements Test

```bash
curl "http://localhost:5000/billing/payments/2025-10/statements?\
uuid=test-uuid-001" \
  -H "uuid: test-uuid-001"
```

### 5. Payment Test

```bash
curl -X POST http://localhost:5000/billing/payments/2025-10 \
  -H "Content-Type: application/json" \
  -H "uuid: test-uuid-001" \
  -d '{"paymentGroupId":"bg-kr-test","amount":100000}'
```

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Debugging Tips

- Check Mock Server logs
- Use browser DevTools Network tab
- Verify CORS headers
- Check request/response format

```bash
# Mock server with logging
python -m mock_server.run_server
```

## Additional Endpoints (Future)

- Batch operations
- Reporting endpoints
- Admin operations
- Analytics APIs
