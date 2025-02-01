import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from reels_extraction import extract_reels_info, analyze_with_gpt4
import os
from dotenv import load_dotenv
from api_config import get_api_config
import requests
import openai
import re
import time
from urllib.parse import urlparse

# .env 파일 로드
load_dotenv()

# API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 페이지 기본 설정
st.set_page_config(
    page_title="✨ 릴스 벤치마킹 스튜디오",
    page_icon="🎥",
    layout="centered"
)

# 스타일 설정
st.markdown("""
    <style>
    /* 전체 페이지 스타일 */
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* 브랜드 로고 */
    .brand-logo {
        position: fixed;
        top: 20px;
        right: 20px;
        font-size: 14px;
        color: #1c1c1e;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    
    /* 메인 타이틀 */
    .title-container {
        text-align: left;
        margin: 1rem 0;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f1f1f1;
    }
    
    .title-container h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1c1c1e;
        margin-bottom: 0.5rem;
    }
    
    /* 섹션 헤더 */
    .section-header {
        color: #1E1E1E;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #F1F3F5;
        text-align: center;
    }
    
    .section-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        background: linear-gradient(45deg, #405DE6, #5851DB);
        color: white;
        border-radius: 50%;
        font-size: 14px;
        font-weight: 600;
        margin-right: 8px;
    }
    
    /* 입력 필드 스타일링 */
    .stTextInput > div > div {
        border-radius: 12px !important;
        border: 1px solid #e6e6e6 !important;
        padding: 0.5rem !important;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: #405DE6 !important;
        box-shadow: 0 0 0 1px #405DE6 !important;
    }
    
    /* 비디오 컨테이너 */
    .video-container {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 2rem 0;
    }
    
    .stVideo {
        width: 100%;
        max-width: 400px !important;
        margin: 0 auto;
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* 버튼 스타일링 */
    .stButton > button {
        background: linear-gradient(45deg, #405DE6, #5851DB) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.5rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(64,93,230,0.2) !important;
    }
    
    /* 확장 패널 스타일링 */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 12px !important;
        border: 1px solid #e6e6e6 !important;
    }
    
    /* 폼 컨테이너 */
    .form-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 2rem 0;
    }
    
    /* 분석 결과 섹션 스타일링 */
    .analysis-section {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .section-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1c1c1e;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .subsection-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #1c1c1e;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .info-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
    }
    
    .info-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
    }
    
    .info-title {
        font-weight: 600;
        color: #405DE6;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(45deg, #405DE6, #5851DB) !important;
    }
    .progress-label {
        text-align: center;
        color: #1c1c1e;
        font-weight: 500;
        margin-bottom: 5px;
    }
    .step-container {
        margin-bottom: 20px;
    }
    </style>
    
    <div class="brand-logo">HANSHIN GROUP</div>
""", unsafe_allow_html=True)

def normalize_instagram_url(url):
    """
    입력된 인스타그램 URL을 '/p/{ID}/' 형식으로 변환합니다.
    쿼리 파라미터와 기타 불필요한 부분을 제거합니다.
    """
    try:
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')

        if len(path_parts) >= 2:
            if path_parts[0] in ['reel', 'tv', 'p']:
                shortcode = path_parts[1]
                normalized_url = f"https://www.instagram.com/p/{shortcode}/"
                return normalized_url
        return url  # 변경이 필요 없는 다른 형식의 URL

    except Exception as e:
        st.error(f"URL 정규화 중 오류 발생: {str(e)}")
        return url

def is_valid_instagram_url(url):
    # Instagram URL 유효성 검사
    instagram_pattern = r'https?://(?:www\.)?instagram\.com/(?:p|reel)/[a-zA-Z0-9_-]+'
    return bool(re.match(instagram_pattern, url))

def get_video_url(url, username=None, password=None):
    try:
        ydl_opts = {
            'format': 'best',
            'extract_flat': True,
        }
        
        # 로그인 정보가 있으면 추가
        if username and password:
            ydl_opts.update({
                'username': username,
                'password': password,
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def create_input_form():
    # 타이틀 섹션
    st.markdown('<div class="title-container"><h1>✨ 릴스 벤치마킹 스튜디오</h1></div>', unsafe_allow_html=True)
    
    # 1. 벤치마킹 섹션
    st.markdown("""
        <div class="section-header">
            <span class="section-number">1</span>
            벤치마킹 정보 입력
        </div>
    """, unsafe_allow_html=True)
    
    # URL을 세션 상태로 관리
    if 'url' not in st.session_state:
        st.session_state.url = ''
    
    # URL 입력 필드 (불필요한 컨테이너 제거)
    url = st.text_input("✨ 릴스 URL을 입력해주세요", value=st.session_state.url)
    
    # URL 입력 버튼 추가
    url_submit = st.button("URL 입력")
    
    # 폼 데이터를 세션 상태로 관리
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'video_intro_copy': '',
            'video_intro_structure': '',
            'narration': '',
            'music': '',
            'font': ''
        }
    
    # URL이 입력되었거나 URL 입력 버튼이 클릭되었을 때 처리
    if url and (url_submit or True):
        video_url = get_video_url(url)
        if video_url:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                try:
                    st.video(video_url)
                except:
                    st.error("동영상을 불러올 수 없습니다.")
            
            with col2:
                # 폼 추가
                with st.form(key='video_analysis_form'):
                    st.markdown("""
                        <style>
                        /* 영상 분석 섹션 헤더 스타일링 */
                        .analysis-header {
                            margin: 1rem 0 1rem 0 !important;  /* 상하 여백 최소화 */
                            padding: 0 !important;
                            color: #1c1c1e;
                            font-size: 1.5rem;
                            font-weight: 600;
                            display: flex;
                            align-items: center;
                        }
                        
                        /* 폼 스타일링 */
                        .stForm {
                            margin-top: 0 !important;
                            padding-top: 0 !important;
                        }
                        
                        /* 폼 제출 버튼 */
                        .stForm [data-testid="stFormSubmitButton"] > button {
                            background: linear-gradient(45deg, #405DE6, #5851DB) !important;
                            color: white !important;
                            border: none !important;
                            border-radius: 12px !important;
                            padding: 0.5rem 2rem !important;
                            font-weight: 600 !important;
                            width: 100% !important;
                            transition: all 0.3s ease !important;
                        }
                        
                        .stForm [data-testid="stFormSubmitButton"] > button:hover {
                            transform: translateY(-2px) !important;
                            box-shadow: 0 4px 12px rgba(64,93,230,0.2) !important;
                        }
                        </style>
                        
                        <div class="analysis-header">
                            <span class="section-number">📊</span>
                            영상 분석
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 새로 추가: 스크립트와 캡션 입력란
                    st.text_area(
                        "**스크립트 입력**",
                        value=st.session_state.form_data.get('transcript', ''),
                        height=100,
                        help="영상의 스크립트를 입력해주세요"
                    )
                    
                    st.text_area(
                        "**캡션 입력**",
                        value=st.session_state.form_data.get('caption', ''),
                        height=100,
                        help="영상의 캡션을 입력해주세요"
                    )
                    
                    # 기존 입력란 유지
                    intro_copy = st.text_area(
                        "카피라이팅",
                        value=st.session_state.form_data['video_intro_copy'],
                        height=100,
                        help="1. 🎯 구체적 수치 ('월 500만원', '3일 만에' 등)\n"
                             "2. 🧠 뇌 충격 ('망하는 과정', '실패한 이유' 등)\n"
                             "3. 💡 이익/손해 강조 ('놓치면 후회', '꼭 알아야 할' 등)\n"
                             "4. 👑 권위 강조 ('현직 대기업 임원', '10년 경력' 등)\n"
                             "5. ✨ 예시: '현직 인사팀장이 알려주는 연봉 3천 협상법'",
                        key="intro_copy"
                    )
                    
                    intro_structure = st.text_area(
                        "영상 구성",
                        value=st.session_state.form_data['video_intro_structure'],
                        height=100,
                        help="1. 💥 상식 파괴 (예상 밖의 장면)\n"
                             "2. 🎬 결과 먼저 보여주기 (Before & After)\n"
                             "3. ⚠️ 부정적 상황 강조\n"
                             "4. 🤝 공감 유도 (일상적 고민/불편함)\n"
                             "5. 📱 예시: '출근 시간에 편하게 누워서 일하는 직원들 모습'",
                        key="intro_structure"
                    )
                    
                    narration = st.text_input(
                        "나레이션",
                        value=st.session_state.form_data['narration'],
                        help="1. 🎤 목소리 특징 (성별, 연령대, 톤)\n"
                             "2. 💬 말하기 스타일 (전문적/친근한)\n"
                             "3. 🎵 음질 상태 (노이즈 없는 깨끗한 음질)\n"
                             "4. ✅️ 예시: '20대 여성의 친근한 톤, 깨끗한 마이크 음질'",
                        key="narration"
                    )
                    
                    music = st.text_input(
                        "배경음악",
                        value=st.session_state.form_data['music'],
                        help="1. 🎵 트렌디한 정도 (최신 유행 BGM)\n"
                             "2. 🎶 영상과의 조화 (리듬감, 분위기)\n"
                             "3. 🎼 장르 및 템포\n"
                             "4. 🎧 예시: '트렌디한 K-pop, 영상의 템포와 잘 맞는 리듬'",
                        key="music"
                    )
                    
                    font = st.text_input(
                        "사용 폰트",
                        value=st.session_state.form_data['font'],
                        help="1. 📝 폰트 종류 (고딕체, 손글씨체 등)\n"
                             "2. ✒️ 강조 요소 (굵기, 크기, 테두리)\n"
                             "3. 👀 가독성 정도\n"
                             "4. 💫 예시: '눈에 띄는 굵은 글씨, 흰색 테두리, 노란색 배경'",
                        key="font"
                    )
                    
                    # 폼 제출 버튼
                    if st.form_submit_button("분석 내용 저장"):
                        st.session_state.form_data.update({
                            'transcript': st.session_state.form_data.get('transcript', ''),
                            'caption': st.session_state.form_data.get('caption', ''),
                            'video_intro_copy': st.session_state.form_data['video_intro_copy'],
                            'video_intro_structure': st.session_state.form_data['video_intro_structure'],
                            'narration': st.session_state.form_data['narration'],
                            'music': st.session_state.form_data['music'],
                            'font': st.session_state.form_data['font']
                        })
                        st.success("분석 내용이 저장되었습니다!")
            
            # URL이 입력되고 동영상이 성공적으로 로드된 경우에만 나머지 섹션 표시
            st.markdown("""
                <div class="section-header">
                    <span class="section-number">2</span>
                    내 콘텐츠 정보 입력
                </div>
            """, unsafe_allow_html=True)
            topic = st.text_area("제작할 콘텐츠에 대해 자유롭게 입력해주세요", height=68)
            
            # 분석 시작 버튼
            st.markdown("""
                <style>
                div.stButton > button {
                    width: 100%;
                    background: linear-gradient(45deg, #405DE6, #5851DB) !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 12px !important;
                    padding: 0.5rem 2rem !important;
                    font-weight: 600 !important;
                    transition: all 0.3s ease !important;
                }
                
                div.stButton > button:hover {
                    transform: translateY(-2px) !important;
                    box-shadow: 0 4px 12px rgba(64,93,230,0.2) !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("✨ 벤치마킹 분석 시작", key="analyze_button"):
                with st.spinner("분석 중... (약 30초 소요)"):
                    results = get_cached_analysis(url, {
                        "url": url,
                        "video_analysis": {
                            "intro_copy": st.session_state.form_data['video_intro_copy'],
                            "intro_structure": st.session_state.form_data['video_intro_structure'],
                            "narration": st.session_state.form_data['narration'],
                            "music": st.session_state.form_data['music'],
                            "font": st.session_state.form_data['font']
                        },
                        "content_info": {
                            "topic": topic
                        }
                    })
                    
                    if results:
                        display_analysis_results(results["analysis"], results["reels_info"])
                    
                    return None
        else:
            st.error("Instagram URL에서 동영상을 찾을 수 없습니다.")
    
    return {
        "url": url,
        "video_analysis": {
            "intro_copy": st.session_state.form_data['video_intro_copy'],
            "intro_structure": st.session_state.form_data['video_intro_structure'],
            "narration": st.session_state.form_data['narration'],
            "music": st.session_state.form_data['music'],
            "font": st.session_state.form_data['font']
        },
        "content_info": {
            "topic": topic if 'topic' in locals() else ""
        }
    }

@st.cache_data(ttl=3600, show_spinner=True)
def get_cached_analysis(url, input_data):
    try:
        reels_info = extract_reels_info(url, input_data['video_analysis'])
        if isinstance(reels_info, str):
            st.error(f"정보 추출 실패: {reels_info}")
            return None
        
        analysis = analyze_with_gpt4(reels_info, input_data)
        if "error" in str(analysis).lower():
            st.error(f"AI 분석 실패: {analysis}")
            return None
        
        return {
            "analysis": analysis,
            "reels_info": reels_info
        }
        
    except Exception as e:
        st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
        return None

def display_analysis_results(results, reels_info):
    st.markdown("""
        <style>
        .benchmark-analysis-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #405DE6;
            text-align: center;
            margin: 2.5rem auto;
            padding: 1rem 0;
            border-bottom: 3px solid #405DE6;
            width: 100%;
            background: linear-gradient(to right, transparent, #F0F2FF, transparent);
        }
        </style>
    """, unsafe_allow_html=True)

    # 분석 결과 타이틀
    st.markdown('<div class="benchmark-analysis-title">📊 분석 결과</div>', unsafe_allow_html=True)
    
    # GPT 분석 결과
    analysis_parts = results.split("# 6. 벤치마킹 적용 기획:")
    main_analysis = analysis_parts[0]
    
    # GPT 분석 결과를 마크다운으로 변환하여 이모티콘 추가
    analysis_text = main_analysis.replace("# 1. 주제:", "# 🎯 1. 주제:")
    analysis_text = analysis_text.replace("# 2. 초반 3초", "# ⚡ 2. 초반 3초")
    analysis_text = analysis_text.replace("## 카피라이팅 :", "## ✍️ 카피라이팅 :")
    analysis_text = analysis_text.replace("## 영상 구성 :", "## 🎬 영상 구성 :")
    analysis_text = analysis_text.replace("# 3. 내용 구성:", "# 📋 3. 내용 구성:")
    analysis_text = analysis_text.replace("# 4. 개선할 점:", "# 🔍 4. 개선할 점:")
    analysis_text = analysis_text.replace("# 5. 적용할 점:", "# ✨ 5. 적용할 점:")
    
    # 메인 분석 결과 표시
    st.markdown(analysis_text)
    
    # 벤치마킹 기획 섹션 표시 (있는 경우에만)
    if len(analysis_parts) > 1:
        st.markdown('<div class="benchmark-analysis-title">📝 벤치마킹 기획</div>', unsafe_allow_html=True)
        planning_section = analysis_parts[1].strip()
        st.markdown(planning_section)

def main():
    st.markdown("""
        <style>
        /* 전체 컨테이너 스타일 */
        .main {
            background-color: #FFFFFF;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* 메인 타이틀 스타일 수정 */
        .main-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            color: #1c1c1e;
            margin: 2rem 0;
            padding: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # 타이틀을 중앙 정렬된 div로 감싸기
    st.markdown('<div class="main-title">✨ 릴스 벤치마킹 스튜디오</div>', unsafe_allow_html=True)

    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'transcript': '',
            'caption': '',
            'video_intro_copy': '',
            'video_intro_structure': '',
            'narration': '',
            'music': '',
            'font': ''
        }

    # 간격 추가
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    # 메인 분석 섹션
    st.markdown('<div class="section-header" style="text-align: center;">📊 영상 분석</div>', unsafe_allow_html=True)
    
    # 캡션과 나레이션 섹션
    st.markdown('<div class="input-label" style="font-weight: bold;">📝 캡션과 나레이션</div>', unsafe_allow_html=True)
    

    caption = st.text_area(
        "캡션",
        value=st.session_state.form_data.get('caption', ''),
        height=100,
        help="1. 📝 게시물 하단에 작성된 설명글\n"
             "2. #️⃣ 해시태그 포함\n"
             "3. 📌 핵심 내용 요약\n"
             "4. ✨ 예시: '직장인 부업으로 월 500 벌기 꿀팁 대방출 🔥\n\n이것만 알면 누구나 가능합니다.\n\n#부업 #투잡 #재테크'",
        key="caption"
    )
    
    narration = st.text_area(
        "나레이션",
        value=st.session_state.form_data.get('transcript', ''),
        height=100,
        help="1. 🎙️ 영상에서 말하는 내용을 그대로 작성\n"
             "2. 💬 나레이션, 자막 모두 포함\n"
             "3. 🔄 시간 순서대로 작성\n"
             "4. ✨ 예시: '안녕하세요. 오늘은 직장인 부업으로 \n\n월 500만원 버는 방법을 알려드립니다.'",
        key="transcript"
    )
    
    # 초반 3초 분석 섹션
    st.markdown('<div class="input-label" style="font-weight: bold;">⚡ 초반 3초 분석</div>', unsafe_allow_html=True)
    

    intro_copy = st.text_area(
        "카피라이팅",
        value=st.session_state.form_data['video_intro_copy'],
        height=68,
        help="1. 🎯 구체적 수치 ('월 500만원', '3일 만에' 등)\n"
             "2. 🧠 뇌 충격 ('망하는 과정', '실패한 이유' 등)\n"
             "3. 💡 이익/손해 강조 ('놓치면 후회', '꼭 알아야 할' 등)\n"
             "4. 👑 권위 강조 ('현직 대기업 임원', '10년 경력' 등)\n"
             "5. ✨ 예시: '현직 인사팀장이 알려주는 연봉 3천 협상법'",
        key="intro_copy"
    )
    
    intro_structure = st.text_area(
        "영상 구성",
        value=st.session_state.form_data['video_intro_structure'],
        height=68,
        help="1. 💥 상식 파괴 (예상 밖의 장면)\n"
             "2. 🎬 결과 먼저 보여주기 (Before & After)\n"
             "3. ⚠️ 부정적 상황 강조\n"
             "4. 🤝 공감 유도 (일상적 고민/불편함)\n"
             "5. 📱 예시: '출근 시간에 편하게 누워서 일하는 직원들 모습'",
        key="intro_structure"
    )

    # 스타일 분석 섹션 (전체 너비 사용)
    st.markdown('<div class="input-label" style="font-weight: bold;">🎨 스타일 분석</div>', unsafe_allow_html=True)
    

    narration_style = st.text_input(
        "나레이션 스타일",
        value=st.session_state.form_data['narration'],
        help="1. 🎤 목소리 특징 (성별, 연령대, 톤)\n"
             "2. 💬 말하기 스타일 (전문적/친근한)\n"
             "3. 🎵 음질 상태 (노이즈 없는 깨끗한 음질)\n"
             "4. ✅️ 예시: '20대 여성의 친근한 톤, 깨끗한 마이크 음질'",
        key="narration"
    )
    
    music = st.text_input(
        "배경음악",
        value=st.session_state.form_data['music'],
        help="1. 🎵 트렌디한 정도 (최신 유행 BGM)\n"
             "2. 🎶 영상과의 조화 (리듬감, 분위기)\n"
             "3. 🎼 장르 및 템포\n"
             "4. 🎧 예시: '트렌디한 K-pop, 영상의 템포와 잘 맞는 리듬'",
        key="music"
    )
    
    font = st.text_input(
        "사용 폰트",
        value=st.session_state.form_data['font'],
        help="1. 📝 폰트 종류 (고딕체, 손글씨체 등)\n"
             "2. ✒️ 강조 요소 (굵기, 크기, 테두리)\n"
             "3. 👀 가독성 정도\n"
             "4. 💫 예시: '눈에 띄는 굵은 글씨, 흰색 테두리, 노란색 배경'",
        key="font"
    )
    
    # 간격 추가
    st.markdown("<div style='margin-top: 70px;'></div>", unsafe_allow_html=True)

    # 내 콘텐츠 정보 입력 섹션
    st.markdown('<div class="section-header" style="text-align: center;">✏️ 내 콘텐츠 정보</div>', unsafe_allow_html=True)
    topic = st.text_area(
        "제작할 콘텐츠 주제",
        height=100,
        help="벤치마킹하여 제작하고 싶은 콘텐츠의 주제나 내용을 자유롭게 입력해주세요",
        key="topic"
    )
    
    # 분석 시작 버튼
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100%;
            background: linear-gradient(45deg, #405DE6, #5851DB) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.5rem 2rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(64,93,230,0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("✨ 벤치마킹 분석 시작", key="analyze_button"):
        with st.spinner("분석 중... (약 2분 소요)"):
            results = get_cached_analysis("", {
                "video_analysis": {
                    "transcript": narration,
                    "caption": caption,
                    "intro_copy": intro_copy,
                    "intro_structure": intro_structure,
                    "narration": narration,
                    "music": music,
                    "font": font
                },
                "content_info": {
                    "topic": topic
                }
            })
            
            if results:
                display_analysis_results(results["analysis"], results["reels_info"])

if __name__ == "__main__":
    main()