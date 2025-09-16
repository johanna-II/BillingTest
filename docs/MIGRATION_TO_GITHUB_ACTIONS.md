# 🚀 Jenkins에서 GitHub Actions로 마이그레이션 가이드

## 개요

이 문서는 기존 Jenkins 기반 CI/CD 파이프라인을 GitHub Actions로 마이그레이션하는 방법을 설명합니다.

## 주요 차이점

### Jenkins vs GitHub Actions

| 기능 | Jenkins | GitHub Actions |
|------|---------|----------------|
| 설정 파일 | `ci_billing_test` (Groovy) | `.github/workflows/*.yml` (YAML) |
| 실행 환경 | 자체 호스팅 노드 | GitHub 호스팅 러너 |
| 파라미터 | Jenkins UI에서 입력 | `workflow_dispatch` inputs |
| 아티팩트 | `publishHTML` | `actions/upload-artifact` |
| Docker | Docker 플러그인 | Docker 공식 Actions |
| 비용 | 인프라 비용 | 무료 (Public repo) / 분당 과금 (Private) |

## 마이그레이션 단계

### 1. GitHub Actions 활성화

1. GitHub 저장소의 Settings > Actions 로 이동
2. "Allow all actions and reusable workflows" 선택
3. Save 클릭

### 2. Secrets 설정

GitHub 저장소의 Settings > Secrets and variables > Actions에서 다음 시크릿 추가:

```bash
DOCKER_USERNAME     # Docker Hub 사용자명
DOCKER_PASSWORD     # Docker Hub 비밀번호
SLACK_WEBHOOK_URL   # Slack 알림 URL (선택사항)
```

### 3. 워크플로우 파일 추가

이미 생성된 워크플로우 파일들:
- `.github/workflows/billing-test.yml` - 수동 실행 테스트
- `.github/workflows/ci.yml` - PR/Push 자동 테스트
- `.github/workflows/scheduled-tests.yml` - 일일 자동 테스트
- `.github/workflows/security.yml` - 보안 스캔

### 4. 테스트 마커 추가

빠른 CI를 위해 pytest 마커 추가:

```python
# tests/conftest.py에 추가
import pytest

# 느린 테스트 표시
@pytest.mark.slow
def test_full_billing_cycle():
    pass

# 빠른 smoke 테스트
def test_api_connection():
    pass
```

### 5. 첫 실행

1. **수동 테스트 실행**:
   - Actions 탭 > Billing Test 선택
   - Run workflow 클릭
   - 파라미터 입력 후 실행

2. **자동 CI 확인**:
   - 새 브랜치 생성 및 PR 생성
   - CI 워크플로우 자동 실행 확인

## 기능 매핑

### Jenkins 파라미터 → GitHub Actions Inputs

```yaml
# Jenkins
parameters([
    choice(name: 'env', choices: ['alpha']),
    choice(name: 'member', choices: ['kr', 'jp', 'etc']),
    string(name: 'month'),
    string(name: 'singlefile')
])

# GitHub Actions
inputs:
  environment:
    type: choice
    options: [alpha]
  member:
    type: choice
    options: [kr, jp, etc]
  month:
    type: string
  test_case:
    type: string
```

### Jenkins 조건문 → GitHub Actions 조건

```groovy
// Jenkins
if (singlefile ==~ /.*contract.*/) {
    // contract 검증
}

# GitHub Actions
if: contains(github.event.inputs.test_case, 'contract')
```

### Jenkins 아티팩트 → GitHub Actions 아티팩트

```groovy
// Jenkins
publishHTML([reportDir: 'BillingTest/report/', 
            reportFiles: 'reports_${BUILD_NUMBER}.html'])

# GitHub Actions
- uses: actions/upload-artifact@v4
  with:
    name: billing-test-report
    path: report/
```

## 장점

### 1. 유지보수 간소화
- 인프라 관리 불필요
- 자동 업데이트
- YAML 기반 간단한 설정

### 2. 더 나은 통합
- GitHub UI에 직접 통합
- PR 상태 체크 자동화
- 코드 리뷰와 함께 확인

### 3. 확장성
- 병렬 실행 용이
- 다양한 OS/환경 지원
- 마켓플레이스의 수천 개 Actions 활용

### 4. 비용 효율성
- Public 저장소는 무료
- Private 저장소도 매월 2,000분 무료
- 온디맨드 실행으로 리소스 절약

## 트러블슈팅

### 1. Docker 빌드 캐시

GitHub Actions는 기본적으로 Docker 레이어 캐싱 지원:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

### 2. 시크릿 관리

민감한 정보는 반드시 GitHub Secrets 사용:
```yaml
password: ${{ secrets.DOCKER_PASSWORD }}
```

### 3. 디버깅

SSH 접속이 필요한 경우:
```yaml
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
  if: ${{ github.event_name == 'workflow_dispatch' && inputs.debug_enabled }}
```

## 롤백 계획

GitHub Actions와 Jenkins를 병행 운영하며 점진적 마이그레이션:

1. 처음에는 GitHub Actions를 보조 CI로 운영
2. 안정성 확인 후 메인 CI로 전환
3. Jenkins는 백업으로 일정 기간 유지

## 모니터링

### GitHub Actions 대시보드
- Actions 탭에서 모든 워크플로우 실행 기록 확인
- 실시간 로그 스트리밍
- 실행 시간 및 비용 모니터링

### 알림 설정
- Slack 통합
- 이메일 알림
- GitHub 모바일 앱 푸시 알림

## 다음 단계

1. **성능 최적화**
   - 테스트 병렬화
   - 캐싱 전략 개선
   - 불필요한 단계 제거

2. **추가 자동화**
   - 릴리스 자동화
   - 문서 자동 생성
   - 성능 리포트 생성

3. **모니터링 강화**
   - 커스텀 메트릭 수집
   - 대시보드 구축
   - SLA 모니터링

---

## 참고 자료

- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)
- [Jenkins to GitHub Actions 마이그레이션 가이드](https://docs.github.com/en/actions/migrating-to-github-actions/migrating-from-jenkins-to-github-actions)
- [GitHub Actions 베스트 프랙티스](https://docs.github.com/en/actions/guides)
