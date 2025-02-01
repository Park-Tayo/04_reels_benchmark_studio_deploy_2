import yt_dlp
import tempfile
import os
from pathlib import Path
import subprocess
import openai
from api_config import get_api_config
import time
from functools import wraps
import requests
from datetime import datetime
import json

# 상대 경로로 변경 (스트림릿 클라우드 호환)
BASE_DIR = Path(__file__).parent.parent

# 임시 파일 디렉토리 설정
TEMP_DIR = Path(tempfile.gettempdir()) / "reels_benchmark"
os.makedirs(TEMP_DIR, exist_ok=True)

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[Timer] {func.__name__}: {end_time - start_time:.2f}초")
        return result
    return wrapper

@timer_decorator
def extract_reels_info(url, video_analysis):
    """
    사용자 입력 기반으로 릴스 정보를 구성합니다.
    """
    try:
        # 사용자가 입력한 정보를 그대로 활용
        reels_info = {
            'caption': video_analysis.get('caption', ''),
            'refined_transcript': video_analysis.get('transcript', '')
        }
        
        return reels_info
            
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        return f"Error: {str(e)}"

def analyze_with_gpt4(info, input_data):
    """GPT를 사용하여 릴스 분석을 수행합니다."""
    try:
        api_config = get_api_config()
        client = openai.OpenAI(api_key=api_config["api_key"])
        
        messages = [
            {
                "role": "system",
                "content": """당신은 릴스 분석 전문가입니다..."""  # 기존 프롬프트 유지
            },
            {
                "role": "user",
                "content": f"""
                다음 릴스를 분석하고, 입력된 주제에 맞게 벤치마킹 기획을 해주세요:
                
                스크립트: {info['refined_transcript']}
                캡션: {info['caption']}
                
                사용자 입력 정보:
                - 초반 3초 카피라이팅: {input_data['video_analysis'].get('intro_copy', '')}
                - 초반 3초 영상 구성: {input_data['video_analysis'].get('intro_structure', '')}
                - 나레이션: {input_data['video_analysis'].get('narration', '')}
                - 음악: {input_data['video_analysis'].get('music', '')}
                - 폰트: {input_data['video_analysis'].get('font', '')}
                
                벤치마킹할 새로운 주제: {input_data['content_info'].get('topic', '')}
                """
            }
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"분석 중 오류 발생: {str(e)}"