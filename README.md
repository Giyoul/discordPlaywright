## 📝 구현 기능 목록

### 1. 핵심 로직 기능

- [ ]  로그인 쿠키 저장 기능
- [ ]  디스코드 로그인 자동화
- [ ]  채널 내 모든 메시지 스크롤링
- [ ]  스크롤된 메시지 객체화
- [ ]  객체화된 메시지 파싱
- [ ]  카테고리 자동 분류
- [ ]  CSV 변환
- [x]  가상환경 set import

```markdown
# basic structure
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>

# <type>
feat (feature)
fix (bug fix)
docs (documentation)
style (formatting, missing semi colons, …)
refactor
test (when adding missing tests)
chore (maintain)

# <scope>
console - I/O
domain - 핵심 로직
validation - 유효성검사
test - 테스트코드 추가
```