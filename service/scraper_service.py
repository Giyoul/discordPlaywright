import config
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class ScraperService:
    def __init__(self):
        self.cached_posts = []
        self.scraped_urls = set()  # 이미 스크래핑한 URL 추적
        self.should_stop = False  # 종료 플래그

    def scrape(self):
        url = config.CHANNEL_URL

        print("스크래핑 시작...")
        print(f"[INFO] 스크래핑 URL: {url}")
        print("[INFO] 브라우저에서 원하는 글을 클릭하면 자동으로 스크래핑됩니다.")
        print("[INFO] CLI에서 'end'를 입력하면 스크래핑을 종료합니다.\n")

        try:
            with sync_playwright() as p:
                # 브라우저 실행
                browser = p.chromium.launch(headless=False)
                
                # 브라우저 컨텍스트 생성
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                # 페이지 생성
                page = context.new_page()
                
                print("페이지 로딩 중...")
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # 메시지 로드 대기
                print("\n[INFO] 채널 페이지 로딩 대기 중...")
                try:
                    page.wait_for_selector('li[class*="message"], div[class*="message"]', timeout=30000)
                    print("[INFO] 페이지 로드 완료!")
                except PlaywrightTimeoutError:
                    print("[WARNING] 메시지 요소를 찾을 수 없습니다.")
                
                # CLI 입력을 받는 스레드 시작
                input_thread = threading.Thread(target=self._wait_for_end_command, daemon=True)
                input_thread.start()
                
                # 이전 URL 추적
                previous_url = page.url
                
                print("\n[INFO] 브라우저에서 글을 클릭하세요. 'end'를 입력하면 종료됩니다.\n")
                
                # URL 변경 감지 루프
                while not self.should_stop:
                    try:
                        current_url = page.url
                        
                        # URL이 변경되었고 스레드 URL인 경우 (/thread/ 또는 /threads/)
                        if current_url != previous_url and ('/thread/' in current_url or '/threads/' in current_url):
                            # 이미 스크래핑한 URL인지 확인
                            if current_url not in self.scraped_urls:
                                print(f"\n[INFO] 새로운 스레드 감지: {current_url}")
                                thread_data = self._scrape_thread(page, current_url)
                                if thread_data:
                                    self.cached_posts.append(thread_data)
                                    self.scraped_urls.add(current_url)
                                    print(f"[INFO] 스크래핑 완료! (총 {len(self.cached_posts)}개)")
                                    # 스크래핑 결과 출력
                                    self._print_thread_data(thread_data)
                            else:
                                print(f"\n[INFO] 이미 스크래핑한 글입니다: {current_url}")
                            
                            previous_url = current_url
                        
                        # 짧은 대기 시간
                        page.wait_for_timeout(500)
                        
                    except Exception as e:
                        print(f"[ERROR] 오류 발생: {e}")
                        page.wait_for_timeout(1000)
                
                browser.close()
                print(f"\n[INFO] 스크래핑 종료. 총 {len(self.cached_posts)}개의 스레드를 스크래핑했습니다.")
                
                return self.cached_posts
                
        except Exception as e:
            print(f"[ERROR] 스크래핑 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []

    # CLI에서 end 입력 기다림
    def _wait_for_end_command(self):
        while not self.should_stop:
            try:
                user_input = input().strip().lower()
                if user_input == 'end':
                    print("\n[INFO] 종료 명령을 받았습니다. 스크래핑을 종료합니다...")
                    self.should_stop = True
                    break
            except (EOFError, KeyboardInterrupt):
                break

    # 스레드 URL을 전체보기 URL로 변환합니다.
    # 원본 URL 형식: /{guild_id}/{channel_id}/threads/{thread_id}
    # 전체 URL 형식: /{guild_id}/{thread_id}
    def _convert_thread_url_to_full_view(self, thread_url):

        try:
            if '/thread' in thread_url:
                # URL 파싱
                parts = thread_url.split('/channels/')
                if len(parts) > 1:
                    channel_part = parts[1]
                    segments = channel_part.split('/')

                    if len(segments) >= 4 and (segments[2] == 'thread' or segments[2] == 'threads'):
                        guild_id = segments[0]
                        thread_id = segments[3]
                        full_view_url = f"https://discord.com/channels/{guild_id}/{thread_id}"
                        return full_view_url
                    else:
                        print(f"[WARNING] URL 형식이 예상과 다릅니다. segments[2]={segments[2] if len(segments) > 2 else 'N/A'}")

            print(f"[WARNING] URL 변환 실패, 원본 URL 반환: {thread_url}")
            return thread_url
        except Exception as e:
            print(f"[WARNING] URL 변환 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return thread_url

    # 스크롤 내려서 모든 데이터 가져오기
    def _scroll_to_load_all_comments(self, page):
        print("[INFO] 모든 댓글을 로드하기 위해 스크롤 중...")
        
        last_height = 0
        scroll_attempts = 0
        max_scroll_attempts = 20  # 최대 스크롤 시도 횟수
        
        while scroll_attempts < max_scroll_attempts:
            # 페이지 끝까지 스크롤
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)  # 새 콘텐츠 로드 대기
            
            # 현재 높이 확인
            current_height = page.evaluate("document.body.scrollHeight")
            
            # 높이가 변하지 않으면 더 이상 로드할 내용이 없음
            if current_height == last_height:
                scroll_attempts += 1
                if scroll_attempts >= 3:  # 3번 연속 높이가 같으면 종료
                    break
            else:
                scroll_attempts = 0
            
            last_height = current_height
        
        print(f"[INFO] 스크롤 완료. (시도 횟수: {scroll_attempts})")

    # 페이지에서 글 내용과 댓글 스크래핑
    def _scrape_thread(self, page, thread_url):
        try:
            # 스레드 URL을 전체보기 URL로 변환
            full_view_url = self._convert_thread_url_to_full_view(thread_url)
            print(f"[INFO] 전체보기 URL로 이동: {full_view_url}")
            
            # 전체보기 페이지로 이동
            page.goto(full_view_url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            
            # 메시지 로드 대기
            try:
                page.wait_for_selector('li[class*="message"], div[class*="message"]', timeout=10000)
            except PlaywrightTimeoutError:
                print(f"[WARNING] 메시지 요소를 찾을 수 없습니다.")
                return None
            
            # 모든 댓글을 로드하기 위해 스크롤
            self._scroll_to_load_all_comments(page)

            messages = []
            
            # 여러 선택자 시도
            selectors = [
                'article[class*="message"]',
                'div[class*="messageGroup"]',
                'li[class*="message"]',
                'div[class*="message"]'
            ]
            
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        messages = elements
                        break
                except Exception:
                    continue
            
            if not messages:
                print("[WARNING] 메시지를 찾을 수 없습니다.")
                return None
            
            print(f"[INFO] 총 {len(messages)}개의 메시지 발견")
            
            # 원본 글 찾기 (첫 번째 메시지 또는 특정 메시지)
            original_msg = messages[0]
            original_content = self._extract_message_content(original_msg)
            original_author = self._extract_author(original_msg)

            # 댓글들 (나머지 메시지들)
            comments = []
            for idx, msg in enumerate(messages[1:], 1):
                comment_content = self._extract_message_content(msg)
                comment_author = self._extract_author(msg)

                # 빈 내용이 아니고, 원본 글과 다른 경우만 댓글로 추가
                if comment_content.strip() and comment_content != original_content:
                    comments.append({
                        'content': comment_content,
                        'author': comment_author,
                    })
            
            print(f"[INFO] 댓글 {len(comments)}개 추출 완료")
            
            return {
                'thread_link': thread_url,
                'full_view_link': full_view_url,
                'original_post': {
                    'content': original_content,
                    'author': original_author,
                },
                'comments': comments,
                'comment_count': len(comments)
            }
            
        except Exception as e:
            print(f"[ERROR] 스레드 스크래핑 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_message_content(self, msg_element):
        """메시지 요소에서 내용을 추출합니다."""
        try:
            # 더 구체적인 선택자들 시도
            content_selectors = [
                '[class*="messageContent"]',
                '[class*="content"]',
                '[class*="textContainer"]',
                '[class*="markup"]',
                'div[class*="message"]'
            ]
            
            for selector in content_selectors:
                try:
                    content_elem = msg_element.query_selector(selector)
                    if content_elem:
                        text = content_elem.inner_text()
                        if text.strip():
                            return text
                except Exception:
                    continue
            
            # 모든 선택자가 실패하면 전체 텍스트에서 추출
            full_text = msg_element.inner_text()
            # 너무 긴 경우 (다른 메시지 포함 가능) 첫 부분만 반환
            if len(full_text) > 1000:
                return full_text[:1000]
            return full_text
        except Exception:
            return ""
    
    def _extract_author(self, msg_element):
        """메시지 요소에서 작성자를 추출합니다."""
        try:
            author_elem = msg_element.query_selector('[class*="username"], [class*="author"], [class*="name"]')
            if author_elem:
                return author_elem.inner_text()
            return "Unknown"
        except Exception:
            return "Unknown"

    # CLI에 스크랩된 데이터 출력
    def _print_thread_data(self, thread_data):
        print("\n" + "="*80)
        print("스크래핑 결과")
        print("="*80)
        
        print(f"\n[스레드 링크] {thread_data.get('thread_link', 'N/A')}")
        if 'full_view_link' in thread_data:
            print(f"[전체보기 링크] {thread_data.get('full_view_link', 'N/A')}")
        
        # 원본 글
        original = thread_data.get('original_post', {})
        print(f"\n[원본 글]")
        print(f"  작성자: {original.get('author', 'Unknown')}")
        print(f"  내용:")
        content = original.get('content', '')
        if content:
            for line in content.split('\n')[:10]:
                print(f"    {line}")
            if len(content.split('\n')) > 10:
                print(f"    ... (총 {len(content.split('\n'))}줄)")
        else:
            print(f"    (내용 없음)")
        
        # 댓글들
        comments = thread_data.get('comments', [])
        comment_count = thread_data.get('comment_count', 0)
        print(f"\n[댓글] 총 {comment_count}개")
        
        for i, comment in enumerate(comments[:5], 1):
            print(f"\n  댓글 #{i}:")
            print(f"    작성자: {comment.get('author', 'Unknown')}")
            comment_content = comment.get('content', '')
            if comment_content:
                for line in comment_content.split('\n')[:3]:
                    print(f"    {line}")
                if len(comment_content.split('\n')) > 3:
                    print(f"    ...")
            else:
                print(f"    (내용 없음)")
        
        if comment_count > 5:
            print(f"\n  ... 외 {comment_count - 5}개의 댓글 더 있음")
        
        print("="*80 + "\n")
