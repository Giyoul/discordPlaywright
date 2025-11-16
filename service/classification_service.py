import json
import os
import google.generativeai as genai
import config

class ClassificationService:
    def __init__(self):
        # Gemini API 설정
        genai.configure(api_key=config.GENAI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Post 데이터 로드
        self.posts_data = self._load_posts_data()
        print(f"[INFO] {len(self.posts_data)}개의 Post 데이터를 로드했습니다.")
    
    def _load_posts_data(self):
        """Post 데이터를 JSON 파일에서 로드합니다."""
        try:
            # 현재 파일의 디렉토리 기준으로 data/posts.json 경로 찾기
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            posts_file = os.path.join(project_root, 'data', 'posts.json')
            
            with open(posts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Post 데이터 로드 실패: {e}")
            return []
    
    def classify(self, scraped_data):
        try:
            # 프롬프트 생성
            prompt = self._create_prompt(scraped_data)

            print("[INFO] AI 분류 중...")
            response = self.model.generate_content(prompt)
            
            # JSON 응답 파싱
            result = self._parse_response(response.text)

            # 객체 생성
            post_object = self._create_post_object(result, scraped_data)
            
            return post_object
            
        except Exception as e:
            print(f"[ERROR] 분류 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_prompt(self, scraped_data):
        """분류 및 요약을 위한 프롬프트 생성"""
        
        # Post 목록 문자열 생성
        posts_list = ""
        for post in self.posts_data:
            # description에서 \n 제거
            description = post['description'].replace('\\n', ' ')
            posts_list += f"id: {post['id']}, title: \"{post['title']}\", description: \"{description}\"\n"
        
        # 스크랩된 내용 준비
        original_content = scraped_data.get('original_post', {}).get('content', '')
        comments = scraped_data.get('comments', [])
        
        scraped_text = f"원본 글:\n{original_content}\n\n"
        if comments:
            scraped_text += "댓글들:\n"
            for i, comment in enumerate(comments, 1):
                comment_content = comment.get('content', '')
                scraped_text += f"{i}. {comment_content}\n"
        
        prompt = f"""당신은 IT/개발 분야의 전문가입니다. 제공된 아티클 내용을 분석하여, 가장 적합한 카테고리 ID를 찾고 아티클 내용을 핵심적으로 요약하세요.

[카테고리 목록]
{posts_list}

[분석할 글]
{scraped_text}

[요구사항]
1. 위 카테고리 목록 중 가장 적합한 post_id를 찾아주세요.
2. 글 내용을 30자 정도로 요약해주세요 (정확히 30자일 필요는 없지만, 30자 전후로).
3. 만약 적합한 카테고리가 없다면 post_id를 null로 설정하고, 새로운 post의 title과 description을 제안해주세요.

[응답 형식]
반드시 다음 JSON 형식으로만 응답하세요. 다른 설명이나 텍스트 없이 순수 JSON만 응답하세요:
{{
  "post_id": 숫자 또는 null,
  "description": "30자 정도 요약",
  "new_post_title": "post_id가 null일 때만 제시, 아니면 null",
  "new_post_description": "post_id가 null일 때만 제시, 아니면 null"
}}

중요: 응답은 반드시 JSON 형식이어야 하며, 다른 설명이나 마크다운 코드 블록 없이 순수 JSON만 응답하세요."""
        
        return prompt
    
    def _parse_response(self, response_text):
        """AI 응답을 JSON으로 파싱합니다."""
        try:
            # JSON 부분만 추출 (마크다운 코드 블록 제거)
            text = response_text.strip()
            
            # ```json 또는 ```로 감싸진 경우 제거
            if text.startswith('```'):
                lines = text.split('\n')
                # 첫 줄과 마지막 줄 제거
                text = '\n'.join(lines[1:-1])
            
            # JSON 파싱
            result = json.loads(text)
            
            # 필수 필드 검증
            if 'post_id' not in result or 'description' not in result:
                print("[WARNING] 응답에 필수 필드가 없습니다.")
                return None
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 실패: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] 응답 파싱 중 오류: {e}")
            return None
    
    def _create_post_object(self, ai_result, scraped_data):
        """AI 결과와 스크랩 데이터를 합쳐서 최종 객체를 생성합니다."""
        
        # post_id 처리 (null이면 None으로 변환)
        post_id = ai_result.get('post_id')
        if post_id == 'null' or post_id is None:
            post_id = None
        else:
            try:
                post_id = int(post_id)
            except (ValueError, TypeError):
                post_id = None
        
        # description 가져오기 (AI가 생성한 그대로 사용, 최대 100자로 제한)
        description = ai_result.get('description', '')
        if len(description) > 100:
            description = description[:100] + "..."
        
        result = {
            'title': scraped_data.get('title', ''),
            'description': description,
            'link': scraped_data.get('full_view_link', ''),
            'author': scraped_data.get('author', ''),
            'post_id': post_id
        }
        
        # post_id가 null인 경우 새로운 post 제안 정보 추가
        if post_id is None:
            result['new_post_title'] = ai_result.get('new_post_title')
            result['new_post_description'] = ai_result.get('new_post_description')
        
        return result
    
    def get_post_title(self, post_id):
        """post_id로 post의 title을 가져옵니다."""
        for post in self.posts_data:
            if post['id'] == post_id:
                return post['title']
        return None

