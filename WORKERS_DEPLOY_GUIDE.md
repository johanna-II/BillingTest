# 🚀 Cloudflare Workers 배포 가이드

완전 무료로 백엔드 API를 배포하는 방법입니다!

## ⚡ 빠른 배포 (5분)

### 1단계: Wrangler 설치 및 로그인

```bash
# workers 디렉토리로 이동
cd workers/billing-api

# 패키지 설치
npm install

# Cloudflare 로그인 (처음 한 번만)
npx wrangler login
```

브라우저가 열리면 Cloudflare 계정으로 로그인하세요.

### 2단계: 배포!

```bash
npm run deploy
```

배포가 완료되면 URL이 표시됩니다:
```
✅ Published billing-api
   https://billing-api.your-subdomain.workers.dev
```

### 3단계: 프론트엔드 환경 변수 업데이트

**Cloudflare Pages Dashboard에서:**

1. 프로젝트 선택
2. **Settings** → **Environment variables**
3. **Production** 탭에서 추가:
   ```
   Variable name: NEXT_PUBLIC_API_URL
   Value: https://billing-api.your-subdomain.workers.dev
   ```
4. **Save** 클릭

### 4단계: 프론트엔드 재배포

**옵션 A: 수동 재배포**
- Cloudflare Pages Dashboard → Deployments → Create deployment

**옵션 B: 더미 커밋 푸시**
```bash
git commit --allow-empty -m "chore: trigger redeploy with new API URL"
git push
```

---

## ✅ 테스트

### Health Check

```bash
curl https://billing-api.your-subdomain.workers.dev/health
```

예상 응답:
```json
{
  "header": {
    "isSuccessful": true,
    "resultCode": 0,
    "resultMessage": "SUCCESS"
  },
  "status": "healthy",
  "timestamp": "2025-10-08T16:30:00.000Z"
}
```

### Calculate Billing

```bash
curl -X POST https://billing-api.your-subdomain.workers.dev/api/billing/admin/calculate \
  -H "Content-Type: application/json" \
  -H "uuid: test-uuid" \
  -d '{
    "uuid": "test-uuid",
    "billingGroupId": "bg-test",
    "targetDate": "2025-10-08",
    "usage": [
      {
        "counterName": "compute.c2.c8m8",
        "counterVolume": 100,
        "counterType": "DELTA",
        "counterUnit": "HOURS",
        "resourceId": "vm-001",
        "appKey": "test"
      }
    ],
    "credits": [],
    "adjustments": []
  }'
```

---

## 🌐 커스텀 도메인 연결 (선택사항)

### 방법 1: Workers Dashboard에서

1. **Cloudflare Dashboard** → **Workers & Pages**
2. `billing-api` 프로젝트 선택
3. **Settings** → **Triggers** → **Custom Domains**
4. **Add Custom Domain**:
   ```
   api.your-domain.com
   ```
5. 자동으로 DNS 레코드가 생성됩니다!

### 방법 2: wrangler.toml에서

```toml
[env.production]
routes = [
  { pattern = "api.your-domain.com/*", zone_name = "your-domain.com" }
]
```

재배포:
```bash
npm run deploy
```

---

## 🔧 CORS 설정 업데이트

프론트엔드 도메인 추가:

`src/index.ts` 파일 수정:
```typescript
app.use('/*', cors({
  origin: [
    'http://localhost:3000',
    'https://your-project.pages.dev',  // ← 실제 URL로 변경
    'https://your-domain.com'           // ← 커스텀 도메인 추가
  ],
  ...
}))
```

재배포:
```bash
npm run deploy
```

---

## 📊 무료 티어 제한

**Cloudflare Workers (무료):**
- ✅ **10만 요청/일** (= 300만 요청/월)
- ✅ **10ms CPU 시간/요청**
- ✅ **무제한 대역폭**
- ✅ **충분함!** 개인 프로젝트는 절대 초과 불가

**예시 계산:**
- 일 1,000명 방문 × 평균 20 API 요청 = 20,000 요청/일
- → 무료 범위 내! ✅

---

## 🔍 모니터링 & 디버깅

### 실시간 로그 확인

```bash
npm run tail
```

### 배포 로그 확인

```bash
npx wrangler deployments list
```

### Dashboard에서 확인

Cloudflare Dashboard → Workers & Pages → billing-api → Logs

---

## 🆘 트러블슈팅

### 문제 1: "Unauthorized" 에러

**해결:**
```bash
npx wrangler login
npm run deploy
```

### 문제 2: CORS 에러

**해결:**
1. `src/index.ts`에서 프론트엔드 도메인 확인
2. 재배포: `npm run deploy`

### 문제 3: "Worker exceeded CPU time limit"

**원인:** 복잡한 계산으로 10ms 초과

**해결:**
- 계산 로직 최적화
- 또는 Durable Objects 사용 (유료)

---

## 🎯 다음 단계

1. ✅ Workers 배포 완료
2. ✅ 프론트엔드 환경 변수 업데이트
3. ✅ 프론트엔드 재배포
4. ✅ 테스트: 프론트엔드에서 빌링 계산
5. ✅ 커스텀 도메인 연결 (선택)

---

## 💡 고급 기능

### Durable Objects (상태 저장)

```bash
# wrangler.toml에 추가
[[durable_objects.bindings]]
name = "BILLING_STATE"
class_name = "BillingState"
```

### KV Storage (캐싱)

```bash
# KV 네임스페이스 생성
npx wrangler kv:namespace create "BILLING_CACHE"

# wrangler.toml에 추가
[[kv_namespaces]]
binding = "BILLING_CACHE"
id = "your-namespace-id"
```

### Cron Triggers (스케줄링)

```toml
[triggers]
crons = ["0 0 * * *"]  # 매일 자정
```

---

**축하합니다! 🎉**

이제 완전 무료로 24시간 운영되는 풀스택 애플리케이션이 준비되었습니다!

- 프론트엔드: Cloudflare Pages (무료)
- 백엔드: Cloudflare Workers (무료)
- 도메인: Cloudflare DNS (무료)
- SSL: Cloudflare (무료)
- CDN: Cloudflare (무료)

**총 비용: $0/월** 🎉

