# API Specification

## Mock Server API 엔드포인트

### 1. Metering (사용량 전송)

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

### 2. Calculate (계산 실행)

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

### 3. Get Statements (명세서 조회)

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

### 4. Process Payment (결제)

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
  "paymentId": "PAY-20251004120000",
  "paymentGroupId": "bg-kr-test",
  "status": "COMPLETED",
  "amount": 100000,
  "paymentDate": "2025-10-04T12:00:00Z",
  "month": "2025-10"
}
```

## Web UI → Mock Server 플로우

```
1. User Input
   ↓
2. POST /api/billing/meters (프론트엔드)
   ↓ (프록시)
3. POST /billing/meters (Mock 서버)
   ↓
4. POST /api/billing/admin/calculate (프론트엔드)
   ↓ (프록시)
5. POST /billing/admin/calculate (Mock 서버)
   ↓
6. GET /api/billing/payments/{month}/statements (프론트엔드)
   ↓ (프록시)
7. GET /billing/payments/{month}/statements (Mock 서버)
   ↓
8. Display Statement
   ↓
9. POST /api/billing/payments/{month} (프론트엔드)
   ↓ (프록시)
10. POST /billing/payments/{month} (Mock 서버)
   ↓
11. Display Payment Result
```

## Next.js API Routes (CORS 우회)

### `/api/billing/meters`
- 프록시: → `/billing/meters` (Mock 서버)
- Method: POST
- Purpose: metering 데이터 전송

### `/api/billing/admin/calculate`
- 프록시: → `/billing/admin/calculate` (Mock 서버)
- Method: POST
- Purpose: 계산 job 실행

### `/api/billing/payments/[month]/statements`
- 프록시: → `/billing/payments/{month}/statements` (Mock 서버)
- Method: GET
- Purpose: 명세서 조회

### `/api/billing/payments/[month]`
- 프록시: → `/billing/payments/{month}` (Mock 서버)
- Method: POST
- Purpose: 결제 처리

## 에러 처리

### Client-Side Fallback
API가 statement를 반환하지 않으면, 프론트엔드에서 자체 계산:

```typescript
// Client-side billing calculation
const subtotal = usage.reduce((sum, u) => sum + u.volume * 1000, 0)
const adjustmentTotal = adjustments.reduce(...)
const creditApplied = credits.reduce(...)
const total = subtotal + adjustmentTotal - creditApplied + unpaid + lateFee
```

### Error Response Format
```json
{
  "header": {
    "isSuccessful": false,
    "resultCode": "400|500",
    "resultMessage": "Error description"
  },
  "error": "Additional error details"
}
```

## 테스트 방법

### 1. Mock 서버 확인
```bash
curl http://localhost:5000/health
```

### 2. Metering 테스트
```bash
curl -X POST http://localhost:5000/billing/meters \
  -H "Content-Type: application/json" \
  -H "uuid: test-uuid-001" \
  -d '{"meterList":[{"appKey":"app-kr-master-001","counterName":"test","counterVolume":100}]}'
```

### 3. Calculate 테스트
```bash
curl -X POST http://localhost:5000/billing/admin/calculate \
  -H "Content-Type: application/json" \
  -H "uuid: test-uuid-001" \
  -d '{"month":"2025-10","uuid":"test-uuid-001","billingGroupId":"bg-kr-test"}'
```

### 4. Statements 테스트
```bash
curl "http://localhost:5000/billing/payments/2025-10/statements?uuid=test-uuid-001" \
  -H "uuid: test-uuid-001"
```

### 5. Payment 테스트
```bash
curl -X POST http://localhost:5000/billing/payments/2025-10 \
  -H "Content-Type: application/json" \
  -H "uuid: test-uuid-001" \
  -d '{"paymentGroupId":"bg-kr-test","amount":100000}'
```

## 환경 변수

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## 디버깅 팁

### CORS 에러 발생 시
- Next.js dev server 재시작: `npm run dev`
- API routes가 제대로 프록시하고 있는지 확인
- 브라우저 Network 탭에서 요청 확인

### "Unexpected token '<'" 에러
- HTML 응답을 받았다는 의미 (404 페이지일 가능성)
- URL 경로 확인
- Mock 서버가 해당 엔드포인트를 지원하는지 확인

### Mock 서버 로그 확인
```bash
# Mock 서버 실행 시 로그 출력
python -m mock_server.run_server
```

## 추가 엔드포인트 (향후)

### Credits 관리
- `POST /billing/admin/campaign/{id}/credits` - 크레딧 부여
- `DELETE /billing/credits/cancel` - 크레딧 취소

### Adjustments 관리
- `POST /billing/admin/projects/adjustments` - 프로젝트 조정
- `POST /billing/admin/billing-groups/adjustments` - 빌링그룹 조정

### Contracts
- `POST /billing/contracts` - 계약 생성
- `GET /billing/contracts` - 계약 조회


