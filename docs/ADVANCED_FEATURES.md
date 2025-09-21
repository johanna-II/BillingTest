# 고급 기능 가이드

## Contract Testing (Pact)

### 빠른 시작
```bash
# 1. Consumer 테스트 (계약 생성)
pytest tests/contracts/test_billing_consumer.py

# 2. Provider 검증
pytest tests/contracts/test_billing_provider.py
```

### 계약 파일
- 위치: `tests/contracts/pacts/`
- 형식: JSON
- Consumer: BillingTest
- Provider: BillingAPI

## OpenAPI Integration

### 엔드포인트
- `/openapi.json` - JSON 형식
- `/openapi.yaml` - YAML 형식
- `/openapi/validate` - 요청 검증

### 자동 기능
1. 정의되지 않은 엔드포인트 자동 응답
2. Request/Response 검증
3. 예제 데이터 생성

### 검증 예시
```python
validation_request = {
    "method": "POST",
    "path": "/credits",
    "body": {"customer_id": "CUST001", "amount": 100.0}
}
response = requests.post("http://localhost:5000/openapi/validate", json=validation_request)
```

## Observability

### 활성화
```bash
# 기본 텔레메트리
pytest --enable-telemetry

# Jaeger 연동
export JAEGER_ENABLED=true
export JAEGER_HOST=localhost
export JAEGER_PORT=6831
pytest --enable-telemetry
```

### Docker Compose
```bash
docker-compose -f docker-compose.observability.yml up -d
```

### 메트릭
- `test_executions_total` - 테스트 실행 횟수
- `test_duration_seconds` - 실행 시간
- `api_calls_total` - API 호출 수
- `mock_server_response_time_ms` - 응답 시간

### 대시보드
- Jaeger UI: http://localhost:16686
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Mock Server 고급 기능

### 캐싱
- 자동 응답 캐싱
- TTL: 300초
- 메모리 기반

### 상태 관리
- In-memory 데이터 저장
- Thread-safe 구현
- 테스트별 격리

### Provider States
```python
# Pact 상태 설정
requests.post("http://localhost:5000/pact-states", json={"state": "A contract exists"})
```

## 성능 최적화

### 병렬 실행
```bash
# CPU 기반 자동 조정
pytest -n auto

# 워크로드 분산
pytest -n 4 --dist worksteal
```

### 캐시 활용
```bash
# 실패한 테스트만
pytest --lf

# 새로운 테스트 우선
pytest --nf
```

더 자세한 내용은 각 기능의 소스 코드를 참고하세요.
