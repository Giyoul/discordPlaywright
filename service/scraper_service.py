import config
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from service.classification_service import ClassificationService

class ScraperService:
    def __init__(self):
        self.cached_posts = []  # 분류된 posts
        self.raw_scraped_data = []  # 분류되지 않은 원본 데이터
        self.scraped_urls = set()  # 이미 스크래핑한 URL 추적
        self.should_stop = False  # 종료 플래그
        self.classifier = ClassificationService()  # 분류 서비스 초기화
        self.auto_classify = False  # 스크래핑 시 자동 분류 여부

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
                                    if self.auto_classify:
                                        # 자동 분류 모드: 즉시 분류
                                        classified_post = self._classify_thread(thread_data)
                                        if classified_post:
                                            # post_id가 null인 경우 알림
                                            if classified_post.get('post_id') is None:
                                                self._print_unclassified_notification(classified_post)
                                            
                                            self.cached_posts.append(classified_post)
                                            self.scraped_urls.add(current_url)
                                            print(f"[INFO] 스크래핑 및 분류 완료! (총 {len(self.cached_posts)}개)")
                                            # 분류된 결과 출력
                                            self._print_classified_post(classified_post)
                                        else:
                                            print("[WARNING] 분류 실패, 원본 데이터만 저장")
                                            self.raw_scraped_data.append(thread_data)
                                            self.scraped_urls.add(current_url)
                                    else:
                                        # 배치 분류 모드: 원본 데이터만 저장
                                        self.raw_scraped_data.append(thread_data)
                                        self.scraped_urls.add(current_url)
                                        print(f"[INFO] 스크래핑 완료! (원본 데이터 저장, 총 {len(self.raw_scraped_data)}개)")
                            else:
                                print(f"\n[INFO] 이미 스크래핑한 글입니다: {current_url}")
                            
                            previous_url = current_url
                        
                        # 짧은 대기 시간
                        page.wait_for_timeout(500)
                        
                    except Exception as e:
                        print(f"[ERROR] 오류 발생: {e}")
                        page.wait_for_timeout(1000)
                
                browser.close()

                return self.cached_posts
                
        except Exception as e:
            print(f"[ERROR] 스크래핑 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_cached_posts(self):
        """분류된 posts를 반환합니다."""
        return self.cached_posts
    
    def get_raw_scraped_data(self):
        """분류되지 않은 원본 데이터를 반환합니다."""
        return self.raw_scraped_data
    
    def set_auto_classify(self, auto_classify):
        """자동 분류 모드 설정"""
        self.auto_classify = auto_classify
    
    def batch_classify(self):
        """분류되지 않은 모든 데이터를 배치로 분류합니다."""
        if not self.raw_scraped_data:
            print("[INFO] 분류할 데이터가 없습니다.")
            return
        
        print(f"\n[INFO] 배치 분류 시작... (총 {len(self.raw_scraped_data)}개)")
        
        classified_count = 0
        failed_count = 0
        
        for idx, thread_data in enumerate(self.raw_scraped_data, 1):
            print(f"\n[{idx}/{len(self.raw_scraped_data)}] 분류 중...")
            classified_post = self._classify_thread(thread_data)
            
            if classified_post:
                # post_id가 null인 경우 알림
                if classified_post.get('post_id') is None:
                    self._print_unclassified_notification(classified_post)
                
                self.cached_posts.append(classified_post)
                classified_count += 1
                print(f"[INFO] 분류 완료! (Post ID: {classified_post.get('post_id', 'null')})")
            else:
                failed_count += 1
                print(f"[WARNING] 분류 실패")
        
        # 분류 완료된 데이터는 원본 리스트에서 제거
        self.raw_scraped_data = []
        
        print(f"\n[INFO] 배치 분류 완료!")
        print(f"  - 성공: {classified_count}개")
        print(f"  - 실패: {failed_count}개")
        print(f"  - 총 분류된 posts: {len(self.cached_posts)}개")
    
    def show_scraped_data_summary(self):
        """스크래핑된 데이터를 약식으로 출력합니다."""
        print("\n" + "="*80)
        print("스크래핑된 데이터 요약")
        print("="*80)
        
        # 분류된 데이터
        print(f"\n[분류된 데이터] 총 {len(self.cached_posts)}개")
        if self.cached_posts:
            for idx, post in enumerate(self.cached_posts, 1):
                title = post.get('title', 'N/A')[:50]
                description = post.get('description', 'N/A')[:30]
                post_id = post.get('post_id', 'null')
                print(f"\n  {idx}. {title}")
                print(f"     설명: {description}")
                print(f"     Post ID: {post_id}")
        else:
            print("  (없음)")
        
        # 원본 데이터 (분류되지 않은)
        print(f"\n[원본 데이터 (미분류)] 총 {len(self.raw_scraped_data)}개")
        if self.raw_scraped_data:
            for idx, data in enumerate(self.raw_scraped_data, 1):
                title = data.get('title', 'N/A')[:50]
                author = data.get('author', 'N/A')
                comment_count = data.get('comment_count', 0)
                print(f"\n  {idx}. {title}")
                print(f"     작성자: {author}")
                print(f"     댓글 수: {comment_count}개")
        else:
            print("  (없음)")
        
        print("\n" + "="*80)

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
            
            # Discord 스레드 제목 추출 시도
            title = self._extract_thread_title(page)
            if not title or not title.strip():
                # 제목을 찾을 수 없으면 원본 글의 첫 부분을 title로 사용
                title = original_content[:50] if len(original_content) > 50 else original_content
                if not title.strip():
                    title = "제목 없음"
            
            return {
                'title': title,
                'thread_link': thread_url,
                'full_view_link': full_view_url,
                'author': original_author,
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

    # 내용 추출
    def _extract_message_content(self, msg_element):
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

    # 사용자 추출
    def _extract_author(self, msg_element):
        try:
            author_elem = msg_element.query_selector('[class*="username"], [class*="author"], [class*="name"]')
            if author_elem:
                return author_elem.inner_text()
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def _extract_thread_title(self, page):
        """Discord 스레드 제목을 추출합니다."""
        try:
            # Discord 스레드 제목을 찾기 위한 다양한 선택자 시도
            title_selectors = [
                'h1[class*="title"]',
                'div[class*="title"]',
                '[class*="threadTitle"]',
                '[class*="thread-title"]',
                'h1',
                '[aria-label*="thread"]',
                '[data-list-id*="thread"] h1',
                '[class*="header"] h1',
                '[class*="header"] [class*="title"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = page.query_selector(selector)
                    if title_elem:
                        title_text = title_elem.inner_text().strip()
                        if title_text and len(title_text) > 0:
                            return title_text
                except Exception:
                    continue
            
            # 페이지 제목에서 추출 시도
            try:
                page_title = page.title()
                if page_title and 'Discord' not in page_title:
                    return page_title
            except Exception:
                pass
            
            return None
        except Exception:
            return None

    def _classify_thread(self, thread_data):
        """스크래핑된 스레드 데이터를 AI로 분류합니다."""
        try:
            classified_post = self.classifier.classify(thread_data)
            return classified_post
        except Exception as e:
            print(f"[ERROR] 분류 중 오류: {e}")
            return None
    
    def _print_classified_post(self, classified_post):
        """분류된 Post 객체를 출력합니다."""
        print("\n" + "="*80)
        print("분류 결과")
        print("="*80)
        
        print(f"\n[제목] {classified_post.get('title', 'N/A')}")
        print(f"[설명] {classified_post.get('description', 'N/A')}")
        print(f"[링크] {classified_post.get('link', 'N/A')}")
        print(f"[작성자] {classified_post.get('author', 'N/A')}")
        
        post_id = classified_post.get('post_id')
        if post_id:
            post_title = self.classifier.get_post_title(post_id)
            print(f"[Post ID] {post_id} - {post_title}")
        else:
            print(f"[Post ID] null (적합한 카테고리 없음)")
            # 새로운 post 제안이 있으면 출력
            new_title = classified_post.get('new_post_title')
            new_desc = classified_post.get('new_post_description')
            if new_title or new_desc:
                print(f"\n[새로운 Post 제안]")
                if new_title:
                    print(f"  제목: {new_title}")
                if new_desc:
                    print(f"  설명: {new_desc}")
        
        print("="*80 + "\n")
    
    def _print_unclassified_notification(self, classified_post):
        """post_id가 null인 경우 알림을 출력합니다."""
        print("\n" + "="*80)
        print("[알림] 적합한 카테고리가 없는 글 발견!")
        print("="*80)
        print(f"링크: {classified_post.get('link', 'N/A')}")
        
        new_title = classified_post.get('new_post_title')
        new_desc = classified_post.get('new_post_description')
        
        if new_title:
            print(f"제안된 제목: {new_title}")
        if new_desc:
            print(f"제안된 설명: {new_desc}")
        
        print("="*80 + "\n")
