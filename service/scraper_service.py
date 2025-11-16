import config
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class ScraperService:
    def __init__(self):
        self.cached_posts = []

    def scrape(self):
        url = config.CHANNEL_URL

        print("스크래핑 시작...")
        print(f"[INFO] 스크래핑 URL: {url}")

        try:
            with sync_playwright() as p:
                # 브라우저 실행 (headless=False로 하면 브라우저가 보임)
                browser = p.chromium.launch(headless=False)
                
                # 브라우저 컨텍스트 생성
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                # 페이지 생성
                page = context.new_page()
                
                print("페이지 로딩 중...")
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # 채널 페이지가 완전히 로드되고 메시지가 나타날 때까지 대기
                print("\n[INFO] 채널 페이지 및 메시지 로딩 대기 중...")
                try:
                    # 메시지 컨테이너가 나타날 때까지 대기 (최대 30초)
                    page.wait_for_selector('li[class*="message"], div[class*="message"]', timeout=30000)
                    print("[INFO] 메시지 로드 완료!")
                except PlaywrightTimeoutError:
                    print("[WARNING] 메시지 요소를 찾을 수 없습니다. 페이지가 완전히 로드되지 않았을 수 있습니다.")
                    print("[INFO] 계속 진행합니다...")
                
                # 페이지 내용 가져오기
                print("메시지 스크래핑 중...")
                posts = []
                
                # 디스코드 메시지 선택자들 시도
                selectors = [
                    'li[class*="message"]',
                    'div[class*="message"]',
                    '[class*="messageContainer"]',
                    '[class*="messageContent"]'
                ]
                
                messages = []
                for selector in selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        if elements:
                            messages = elements
                            print(f"[DEBUG] {selector} 선택자로 {len(elements)}개 요소 발견")
                            break
                    except Exception as e:
                        continue
                
                if not messages:
                    # 대체 방법: 모든 텍스트가 있는 요소 찾기
                    print("[INFO] 메시지 선택자를 찾지 못했습니다. 페이지 구조를 확인합니다...")
                    # 페이지의 텍스트 내용 일부 출력 (디버깅용)
                    page_content = page.content()
                    print(f"[DEBUG] 페이지 HTML 길이: {len(page_content)}")
                
                # 메시지 파싱
                for i, msg_element in enumerate(messages[:50]):  # 최대 50개만 가져오기
                    try:
                        # 메시지 내용 추출
                        content_elem = msg_element.query_selector('[class*="messageContent"], [class*="content"]')
                        if not content_elem:
                            content_elem = msg_element
                        
                        content = content_elem.inner_text() if content_elem else msg_element.inner_text()
                        
                        # 사용자 이름 추출
                        username_elem = msg_element.query_selector('[class*="username"], [class*="author"], [class*="name"]')
                        username = username_elem.inner_text() if username_elem else "Unknown"
                        
                        # 시간 추출
                        time_elem = msg_element.query_selector('time, [class*="timestamp"]')
                        timestamp = time_elem.get_attribute('datetime') if time_elem else None
                        
                        if content.strip():  # 내용이 있는 경우만 추가
                            posts.append({
                                'title': content[:50] if len(content) > 50 else content,
                                'content': content,
                                'author': username,
                                'timestamp': timestamp,
                                'link': url
                            })
                    except Exception as e:
                        print(f"[WARNING] 메시지 {i+1} 파싱 중 오류: {e}")
                        continue
                
                browser.close()
                
                print(f"[INFO] {len(posts)}개의 메시지를 스크래핑했습니다.")
                return posts
                
        except Exception as e:
            print(f"[ERROR] 스크래핑 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []

