# Billing API - Cloudflare Workers

무료로 운영 가능한 서버리스 빌링 API입니다.

## 🚀 빠른 시작

### 1. 설치

```bash
cd workers/billing-api
npm install
```

### 2. 로컬 개발

```bash
npm run dev
```

→ <http://localhost:8787> 에서 테스트

### 3. 배포

```bash
# Cloudflare 로그인 (처음 한 번만)
npx wrangler login

# 배포
npm run deploy
```

→ <https://billing-api.your-subdomain.workers.dev>

## 🎯 API 엔드포인트

### Health Check

```bash
GET /health
```

### Calculate Billing

```bash
POST /api/billing/admin/calculate
Headers: uuid: test-uuid
Body: {
  "uuid": "test-uuid",
  "billingGroupId": "bg-test",
  "targetDate": "2025-10-08",
  "usage": [...],
  "credits": [...],
  "adjustments": [...]
}
```

### Get Payment Statements

```bash
GET /api/billing/payments/{month}/statements
Headers: uuid: test-uuid
```

### Process Payment

```bash
POST /api/billing/payments/{month}
Headers: uuid: test-uuid
Body: {
  "amount": 100000,
  "paymentGroupId": "PG-test"
}
```

## 💰 비용

**완전 무료!**

- 10만 요청/일 (= 300만 요청/월)
- 10ms CPU 시간/요청
- 무제한 대역폭

## 🔧 환경 변수 설정

배포 후 Cloudflare Dashboard에서 설정:

```text
ALLOWED_ORIGINS=https://your-project.pages.dev,https://your-domain.com
```

## 📊 모니터링

```bash
# 실시간 로그 확인
npm run tail
```

## 🌐 커스텀 도메인 연결

1. Cloudflare Dashboard → Workers → 프로젝트 선택
2. Settings → Triggers → Custom Domains
3. Add Custom Domain: `api.your-domain.com`
