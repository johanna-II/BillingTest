# Integration Tests

이 디렉토리에는 전체 시스템 통합 테스트가 포함되어 있습니다.

## 🚀 Quick Start

### 로컬 실행

```bash
# Mock 서버와 함께 병렬로 실행 (권장)
python tests/integration/run.py

# 병렬 워커 수 지정
python tests/integration/run.py --parallel 4

# 순차 실행 (디버깅용)
python tests/integration/run.py --parallel 0
```

### CI 환경

CI에서는 자동으로 병렬 실행됩니다:

- **통합 테스트**: 4개 워커로 병렬 실행, 120초 타임아웃
- **단위 테스트**: auto 워커로 병렬 실행, 60초 타임아웃
- **계약 테스트**: 순차 실행, 300초 타임아웃

## ⚡ 병렬 실행

### 장점

- ✅ **속도 향상**: 4개 워커로 약 4배 빠른 실행
- ✅ **타임아웃 방지**: 개별 테스트가 짧게 실행되어 전체 타임아웃 방지
- ✅ **리소스 활용**: CI 환경의 멀티코어 CPU 활용

### 설정

#### pytest-xdist 사용

```bash
# auto: CPU 코어 수만큼 워커 생성
pytest tests/integration/ -n auto

# 고정 워커 수
pytest tests/integration/ -n 4

# 순차 실행
pytest tests/integration/
```

#### run.py 스크립트 사용

```bash
# 기본 (2 워커)
python tests/integration/run.py

# 커스텀 워커
python tests/integration/run.py --parallel 4

# 순차 실행
python tests/integration/run.py --parallel 0
```

## ⏱️ 타임아웃 설정

### 전역 타임아웃

- **기본값**: 120초
- **설정 방법**: `--timeout 120`

### 개별 테스트 타임아웃

```python
@pytest.mark.timeout(60)  # 이 테스트만 60초
def test_fast_operation():
    pass

@pytest.mark.timeout(300)  # 이 테스트만 300초
def test_slow_operation():
    pass
```

### 느린 테스트

`test_payment_lifecycle`와 같이 외부 API를 호출하는 테스트:

- 개별 타임아웃: 120초
- Retry 횟수 감소: 3회 → 2회
- 연결 실패 시 skip 처리

## 🧪 테스트 카테고리

### test_all_business_combinations.py

- 모든 비즈니스 로직 조합 테스트
- 할인, 크레딧, 요금 조정 등의 복합 시나리오
- **병렬 실행 안전**: ✅

### test_billing_workflows.py

- 전체 빌링 워크플로우 테스트
- 결제, 크레딧, 조정 라이프사이클
- **병렬 실행 안전**: ⚠️ (일부 테스트는 순차 권장)

### test_business_scenarios.py

- 실제 비즈니스 시나리오
- 엔터프라이즈, 스타트업 등의 실제 케이스
- **병렬 실행 안전**: ✅

## 🔧 트러블슈팅

### 타임아웃 발생

```bash
# 타임아웃 증가
python tests/integration/run.py --timeout 300

# 특정 테스트만 실행
python tests/integration/run.py -k test_name
```

### 병렬 실행 시 충돌

```bash
# 순차 실행으로 전환
python tests/integration/run.py --parallel 0

# 워커 수 감소
python tests/integration/run.py --parallel 2
```

### Mock 서버 연결 실패

```bash
# Mock 서버 출력 확인
python tests/integration/run.py --mock-verbose

# Mock 서버 없이 실행 (실제 API 사용 - 주의!)
python tests/integration/run.py --no-mock
```

## 📊 성능 벤치마크

### 순차 실행

```text
509 tests in ~30 minutes (일부 타임아웃)
```

### 병렬 실행 (4 워커)

```text
509 tests in ~8-10 minutes (타임아웃 최소화)
```

### 병렬 실행 (auto, ~8 워커)

```text
509 tests in ~5-7 minutes
```

## ✅ Best Practices

1. **기본적으로 병렬 실행**: 속도와 타임아웃 방지
2. **디버깅 시 순차 실행**: `--parallel 0`으로 명확한 에러 추적
3. **느린 테스트 표시**: `@pytest.mark.timeout()` 사용
4. **API 실패 처리**: Timeout/Connection 에러 시 skip
5. **Clean teardown**: fixture에서 짧은 타임아웃 사용

## 📝 예제

### 기본 실행

```bash
# 2 워커로 병렬 실행
python tests/integration/run.py
```

### 빠른 실행

```bash
# 최대 병렬화
python tests/integration/run.py --parallel auto
```

### 안전한 실행

```bash
# 순차 실행 + 긴 타임아웃
python tests/integration/run.py --parallel 0 --timeout 300
```

### 특정 테스트

```bash
# 특정 워크플로우만 병렬 실행
python tests/integration/run.py -k workflow --parallel 4
```

---

**CI에서 자동으로 최적 설정이 적용됩니다!**
