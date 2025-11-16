import pandas as pd
from datetime import datetime

class SaveService:
    def __init__(self, scraper_service, view):
        self.scraper = scraper_service
        self.view = view
    
    def save_to_csv(self):
        """스크래핑된 데이터를 CSV 파일로 저장합니다."""
        posts = self.scraper.get_cached_posts()

        if not posts:
            self.view.show_error("저장할 데이터가 없습니다. 먼저 스크래핑을 진행해주세요.")
            return

        try:
            # CSV로 저장할 데이터 준비
            csv_data = []
            for post in posts:
                # 디버깅: 저장 전 데이터 확인
                title_value = post.get('title', '')
                description_value = post.get('description', '')
                print(f"[DEBUG] 저장할 데이터 - title: {title_value[:50]}, description: {description_value[:50]}")
                
                row = {
                    'title': title_value,
                    'description': description_value,
                    'link': post.get('link', ''),
                    'author': post.get('author', ''),
                    'post_id': post.get('post_id', ''),
                }
                csv_data.append(row)

            # DataFrame 생성
            df = pd.DataFrame(csv_data)

            # 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data_{timestamp}.csv"

            # CSV 파일로 저장
            df.to_csv(filename, index=False, encoding='utf-8-sig')

            self.view.show_message(f"CSV 파일 저장 완료! ({filename})")
            print(f"[INFO] 총 {len(posts)}개의 데이터가 저장되었습니다.")

        except Exception as e:
            self.view.show_error(f"CSV 저장 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()