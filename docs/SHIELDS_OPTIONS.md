# 📛 Shield.io Badge Options

img.shields.io를 사용하면 일관된 스타일의 배지를 만들 수 있습니다.

## 현재 사용 중인 배지

```markdown
# GitHub Actions 워크플로우 상태
[![CI](https://img.shields.io/github/actions/workflow/status/johanna-II/BillingTest/ci.yml?branch=main&label=CI&logo=github)](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml)

# Python 버전
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)

# 코드 스타일
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## 추가 가능한 배지 옵션

### 1. 코드 품질 & 커버리지

```markdown
# 코드 커버리지 (Codecov 연동 필요)
[![codecov](https://img.shields.io/codecov/c/github/johanna-II/BillingTest?logo=codecov)](https://codecov.io/gh/johanna-II/BillingTest)

# 코드 품질 (CodeClimate 연동 필요)
[![Maintainability](https://img.shields.io/codeclimate/maintainability/johanna-II/BillingTest)](https://codeclimate.com/github/johanna-II/BillingTest)

# 테스트 통과율
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/johanna-II/BillingTest/actions)
```

### 2. 프로젝트 정보

```markdown
# 최신 릴리즈 버전
[![Release](https://img.shields.io/github/v/release/johanna-II/BillingTest)](https://github.com/johanna-II/BillingTest/releases)

# 커밋 활동
[![Commit Activity](https://img.shields.io/github/commit-activity/m/johanna-II/BillingTest)](https://github.com/johanna-II/BillingTest/commits/main)

# 마지막 커밋
[![Last Commit](https://img.shields.io/github/last-commit/johanna-II/BillingTest)](https://github.com/johanna-II/BillingTest/commits/main)

# 이슈 상태
[![Issues](https://img.shields.io/github/issues/johanna-II/BillingTest)](https://github.com/johanna-II/BillingTest/issues)
```

### 3. 의존성 상태

```markdown
# 의존성 상태 (requires.io 연동 필요)
[![Requirements Status](https://img.shields.io/requires/github/johanna-II/BillingTest)](https://requires.io/github/johanna-II/BillingTest/requirements/)

# Vulnerabilities (Snyk 연동 필요)
[![Known Vulnerabilities](https://img.shields.io/snyk/vulnerabilities/github/johanna-II/BillingTest)](https://snyk.io/test/github/johanna-II/BillingTest)
```

### 4. 커뮤니티

```markdown
# Contributors
[![Contributors](https://img.shields.io/github/contributors/johanna-II/BillingTest)](https://github.com/johanna-II/BillingTest/graphs/contributors)

# Stars
[![Stars](https://img.shields.io/github/stars/johanna-II/BillingTest?style=social)](https://github.com/johanna-II/BillingTest)

# Forks
[![Forks](https://img.shields.io/github/forks/johanna-II/BillingTest?style=social)](https://github.com/johanna-II/BillingTest/network/members)
```

### 5. 다크 모드 지원 배지

```markdown
# 다크/라이트 모드 자동 전환
[![CI](https://img.shields.io/github/actions/workflow/status/johanna-II/BillingTest/ci.yml?branch=main&label=CI&logo=github&color=success&logoColor=white&labelColor=black)](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml)
```

## 배지 스타일 옵션

### 스타일 파라미터

```markdown
# flat (기본값)
?style=flat

# flat-square
?style=flat-square

# for-the-badge
?style=for-the-badge

# plastic
?style=plastic

# social
?style=social
```

### 색상 옵션

```markdown
# 미리 정의된 색상
?color=brightgreen
?color=green
?color=yellowgreen
?color=yellow
?color=orange
?color=red
?color=blue
?color=lightgrey

# 커스텀 색상 (hex)
?color=ff69b4
```

### 로고 옵션

```markdown
# 로고 추가
?logo=python

# 로고 색상
?logoColor=white

# 라벨 색상
?labelColor=black
```

## 동적 배지 예시

```markdown
# PR 환영 메시지
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

# 채팅/지원
[![Chat](https://img.shields.io/badge/chat-on%20slack-brightgreen.svg?logo=slack)](https://slack.com)

# 문서
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat)](https://johanna-II.github.io/BillingTest/)
```

## 배지 생성기

[Shields.io](https://shields.io/)에서 직접 배지를 커스터마이즈할 수 있습니다.

## 권장 사항

1. **일관성**: 모든 배지에 동일한 스타일 사용
2. **관련성**: 프로젝트에 실제로 유용한 정보만 표시
3. **유지보수**: 외부 서비스 연동이 필요한 배지는 신중히 선택
4. **가독성**: 너무 많은 배지는 오히려 혼란을 줄 수 있음
