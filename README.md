## 📝 구현 기능 목록

### 1. 핵심 로직 기능

- [x]  플로우 컨트롤 코드 구현
- [x]  자동 로그인
- [x]  세션 토큰 확인
- [x]  디스코드 로그인 자동화
- [x]  채널 내 모든 메시지 스크롤링
- [x]  자동 로그인 기능 삭제
- [x]  유저가 로그인을 마치기까지 기다리기
- [x]  스크롤링 메시지 Playwright 방식으로 변경
- [x]  유저가 클릭한 데이터에 대한 스크래핑 진행
- [x]  URL 전체보기 페이지 URL로 변환
- [x]  전체보기로 이동 후 스크래핑하도록
- [x]  스크래핑이 끝나면 자동으로 글 목록으로 이동하도록
- [x]  스크롤된 메시지 객체화
- [x]  객체화된 메시지 파싱
- [x]  카테고리 자동 분류
- [x]  gemini 환경설정
- [ ]  CSV 변환
- [x]  가상환경 set import
- [x]  필요 lib 설치 (beautifulsoup4 pandas scikit-learn joblib)
- [x]  CLI 기반 앱 구동
- [x]  MVC 패턴 반영

### 2. I/O
- [x]  웰컴메시지 출력
- [x]  동작 선택 메시지 출력
- [x]  에러 출력 메시지
- [x]  종료시 종료 메시지
- [x]  잘못된 입력 메시지

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

### 2. 네이밍 규칙
파일명 - snake case