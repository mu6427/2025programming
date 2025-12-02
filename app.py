import json
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import quote_plus

import requests
import streamlit as st
from openai import OpenAI


@dataclass
class SongRecommendation:
    title: str
    artist: str
    theme: str
    link: str
    highlight: str


def check_internet_connection(test_url: str = "https://www.google.com", timeout: int = 5) -> bool:
    """Return True when an HTTP GET to test_url completes successfully within timeout."""

    try:
        requests.get(test_url, timeout=timeout)
    except requests.RequestException:
        return False
    return True


def get_openai_client(api_key: str) -> Optional[OpenAI]:
    """Create an OpenAI client using the provided API key."""

    if not api_key or not api_key.strip():
        return None

    try:
        return OpenAI(api_key=api_key.strip())
    except Exception:
        return None


def build_prompt(mood_level: int, genre: str, theme: str) -> str:
    """Compose a system prompt for the GPT API to request song recommendations."""

    mood_description = (
        "매우 우울한"
        if mood_level <= 1
        else "조금 우울한"
        if mood_level <= 3
        else "보통의"
        if mood_level <= 5
        else "조금 신나는"
        if mood_level <= 7
        else "매우 신나는"
    )

    mood_instruction = (
        "사용자의 기분이 매우 우울하므로, 위로와 공감을 주는 감성적인 노래를 추천하세요."
        if mood_level <= 1
        else "사용자의 기분이 조금 우울하므로, 위로와 힐링을 주는 노래를 추천하세요."
        if mood_level <= 3
        else "사용자의 기분이 보통이므로, 테마에 맞는 평온한 노래를 추천하세요."
        if mood_level <= 5
        else "사용자의 기분이 좋으므로, 경쾌하고 신나는 노래를 추천하세요."
        if mood_level <= 7
        else "사용자의 기분이 매우 좋으므로, 매우 경쾌하고 에너지 넘치는 노래를 추천하세요."
    )
    
    return (
        "당신은 음악 큐레이터입니다."
        " 사용자에게 아래 조건에 맞는 노래 5곡을 추천하세요."
        "\n\n중요: 반드시 실제로 존재하는 유명한 노래만 추천하세요. 절대로 가상의 노래나 존재하지 않는 노래를 만들어내지 마세요."
        "\n\n반드시 다음 JSON 형식으로만 응답하세요:"
        '\n{"songs": [{"title": "노래 제목", "artist": "아티스트명", "theme_match": "테마 설명", "link": "URL", "key_lyrics": "가사 하이라이트"}, ...]}'
        "\n\n조건:"
        f"\n- 사용자의 기분 수준은 {mood_level}/10입니다. (1: 매우 우울, 10: 매우 신남)"
        f"\n- 사용자의 기분은 {mood_description} 상태입니다."
        f"\n- {mood_instruction}"
        f"\n- 사용자가 원하는 장르는 {genre} 입니다."
        f"\n- 가사의 테마는 '{theme}' 입니다."
        "\n- 반드시 실제로 존재하는 유명한 노래만 추천하세요. 한국 가요, 해외 팝송, 클래식 등 실제로 발매된 노래만 선택하세요."
        "\n- 제목과 아티스트명은 정확하게 작성하세요. 실제로 존재하는 노래의 정확한 제목과 아티스트를 사용하세요."
        "\n- link 필드는 YouTube 검색 링크 형식으로 제공하세요: https://www.youtube.com/results?search_query=노래제목+아티스트명"
        "\n- 또는 실제로 접근 가능한 YouTube Music, Spotify 등의 URL을 제공하세요."
        "\n- 링크가 없거나 유효하지 않으면 빈 문자열(\"\")로 두세요."
        "\n- theme_match에는 해당 노래가 테마와 분위기에 어떻게 맞는지 한국어 문장으로 작성하세요."
        "\n- key_lyrics는 사용자에게 어울릴 한 줄의 가사를 한국어로 요약하거나 번역해 주세요."
        "\n- 반드시 정확한 JSON 형식으로 응답하고, songs 배열에 정확히 5개의 노래를 포함하세요."
    )


def verify_song_exists(title: str, artist: str) -> bool:
    """Check if a song exists on YouTube and verify that the title and artist match."""
    try:
        # 정확한 매칭을 위해 제목과 아티스트로 검색
        search_query = f"{title} {artist}"
        encoded_query = quote_plus(search_query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # YouTube 검색 페이지에 요청
        response = requests.get(search_url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            content = response.text.lower()
            title_lower = title.lower().strip()
            artist_lower = artist.lower().strip()
            
            # 제목과 아티스트가 모두 검색 결과에 나타나는지 확인
            title_found = title_lower in content
            artist_found = artist_lower in content
            
            # 제목과 아티스트가 모두 있어야 함
            if title_found and artist_found:
                # 더 정확한 검증: 제목과 아티스트가 가까이 있는지 확인
                # YouTube 검색 결과에서 보통 제목과 아티스트가 함께 나타남
                # 간단한 검증: 제목과 아티스트가 모두 존재하는지만 확인
                return True
            
            # 제목만 있거나 아티스트만 있으면 매칭 실패로 간주
            return False
        
        return False
    except Exception:
        # 검증 실패 시 일단 True 반환 (네트워크 문제 등)
        return True


def verify_song_artist_match(title: str, artist: str) -> Tuple[bool, str]:
    """
    Verify that the song title and artist are correctly matched.
    Returns (is_valid, corrected_artist) tuple.
    """
    try:
        # 제목만으로 검색해서 실제 아티스트 확인
        title_query = quote_plus(title)
        search_url = f"https://www.youtube.com/results?search_query={title_query}"
        
        response = requests.get(search_url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            content = response.text.lower()
            title_lower = title.lower().strip()
            artist_lower = artist.lower().strip()
            
            # 제목이 검색 결과에 있는지 확인
            if title_lower in content:
                # 아티스트도 검색 결과에 있는지 확인
                if artist_lower in content:
                    # 제목과 아티스트가 함께 나타나는지 확인
                    # YouTube 검색 결과에서 보통 "제목 - 아티스트" 형식으로 나타남
                    combined_pattern = f"{title_lower} - {artist_lower}"
                    if combined_pattern in content or f"{artist_lower} - {title_lower}" in content:
                        return (True, artist)
                    # 또는 제목과 아티스트가 가까이 있는지 확인
                    title_pos = content.find(title_lower)
                    artist_pos = content.find(artist_lower)
                    if title_pos != -1 and artist_pos != -1:
                        # 제목과 아티스트가 500자 이내에 있으면 매칭된 것으로 간주
                        if abs(title_pos - artist_pos) < 500:
                            return (True, artist)
            
            # 매칭 실패
            return (False, artist)
        
        return (True, artist)  # 검증 실패 시 일단 통과
    except Exception:
        return (True, artist)  # 검증 실패 시 일단 통과


def request_recommendations(
    client: OpenAI, mood_level: int, genre: str, theme: str
) -> List[SongRecommendation]:
    """Call the GPT API and parse the response into SongRecommendation items."""

    prompt = build_prompt(mood_level, genre, theme)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful music recommendation assistant."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    
    # JSON 코드 블록이 있으면 추출
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI 응답을 JSON으로 해석할 수 없습니다: {str(exc)}") from exc

    songs = []
    
    # songs 필드가 있는 경우
    if "songs" in payload and isinstance(payload["songs"], list):
        items = payload["songs"]
    # payload 자체가 리스트인 경우
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("응답에서 노래 목록을 찾을 수 없습니다. JSON 형식을 확인해주세요.")

    verified_songs = []
    
    for item in items:
        if not isinstance(item, dict):
            continue
        
        title = item.get("title", "제목 미상")
        artist = item.get("artist", "아티스트 미상")
        
        # 제목이나 아티스트가 기본값이면 건너뛰기
        if title == "제목 미상" or artist == "아티스트 미상":
            continue
        
        # 노래가 실제로 존재하는지 확인
        if verify_song_exists(title, artist):
            # 가수와 노래가 제대로 매칭되는지 추가 검증
            is_valid_match, verified_artist = verify_song_artist_match(title, artist)
            
            if is_valid_match:
                verified_songs.append(
                    SongRecommendation(
                        title=title,
                        artist=verified_artist,  # 검증된 아티스트 사용
                        theme=item.get("theme_match", item.get("theme", "")),
                        link=item.get("link", ""),
                        highlight=item.get("key_lyrics", item.get("highlight", "")),
                    )
                )
    
    # 검증된 노래가 3개 미만이면 재시도
    if len(verified_songs) < 3:
        # 존재하지 않는 노래를 필터링했는데 결과가 부족하면 다시 요청
        # 하지만 무한 루프를 방지하기 위해 최대 2번만 재시도
        if len(verified_songs) == 0:
            raise ValueError("실제로 존재하는 노래를 찾을 수 없습니다. 다른 조건으로 다시 시도해 주세요.")
    
    if not verified_songs:
        raise ValueError("추천 결과를 찾을 수 없습니다. 입력을 다시 확인해 주세요.")

    return verified_songs


def get_youtube_search_url(title: str, artist: str) -> str:
    """Generate a YouTube search URL for the song."""
    search_query = f"{title} {artist}"
    encoded_query = quote_plus(search_query)
    return f"https://www.youtube.com/results?search_query={encoded_query}"


def render_song_card(song: SongRecommendation) -> None:
    """Render a single song recommendation card."""

    st.markdown(f"### {song.title} — {song.artist}")
    if song.theme:
        st.write(song.theme)
    if song.highlight:
        st.caption(f"가사 하이라이트: {song.highlight}")
    
    # 링크가 있고 유효한 URL 형식인 경우 사용, 아니면 YouTube 검색 링크 생성
    if song.link and song.link.startswith(("http://", "https://")):
        music_link = song.link
    else:
        music_link = get_youtube_search_url(song.title, song.artist)
    
    st.link_button("음악 듣기", music_link)
    st.divider()


def main() -> None:
    st.set_page_config(page_title="AI 음악 추천", page_icon="🎵", layout="centered")

    st.title("내 기분 맞춤 AI 음악 추천")
    st.write(
        "기분, 원하는 장르, 가사의 테마를 입력하면 AI가 맞춤 음악을 추천해 드립니다."
    )

    if not check_internet_connection():
        st.error("인터넷 연결이 필요합니다. 연결 상태를 확인하고 다시 시도해 주세요.")
        if st.button("다시 시도"):
            st.rerun()
        st.stop()

    # API 키 입력 섹션
    with st.expander("🔑 OpenAI API 키 설정", expanded=True):
        api_key = st.text_input(
            "OpenAI API 키를 입력하세요",
            type="password",
            help="OpenAI 웹사이트(https://platform.openai.com/api-keys)에서 API 키를 발급받을 수 있습니다.",
            placeholder="sk-..."
        )
        
        # 세션 상태에 API 키 저장
        if api_key:
            st.session_state['openai_api_key'] = api_key
        elif 'openai_api_key' not in st.session_state:
            st.session_state['openai_api_key'] = ""

    # API 키 확인
    current_api_key = st.session_state.get('openai_api_key', '')
    if not current_api_key:
        st.warning("⚠️ OpenAI API 키를 입력해주세요. 위의 'OpenAI API 키 설정' 섹션을 열어 키를 입력하세요.")
        st.info("💡 API 키는 세션 동안 메모리에만 저장되며, 페이지를 새로고침하면 다시 입력해야 합니다.")
        st.stop()

    client = get_openai_client(current_api_key)
    if client is None:
        st.error("❌ API 키가 유효하지 않습니다. 올바른 OpenAI API 키를 입력해주세요.")
        st.stop()

    genre_selection = st.selectbox(
        "듣고 싶은 노래의 장르를 선택하세요",
        [
            "발라드",
            "팝",
            "힙합",
            "R&B",
            "록",
            "재즈",
            "EDM",
            "클래식",
            "인디",
            "직접 입력",
        ],
        index=0,
    )
    
    if genre_selection == "직접 입력":
        genre = st.text_input("장르를 직접 입력해주세요", key="custom_genre_input")
    else:
        genre = genre_selection

    st.write("지금 기분은 어떤가요?")
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.caption("1<br>매우 우울", unsafe_allow_html=True)
    with col2:
        mood_level = st.slider("", min_value=1, max_value=10, value=5, label_visibility="collapsed")
    with col3:
        st.caption("10<br>매우 신남", unsafe_allow_html=True)
    theme = st.text_input("가사의 테마를 적어주세요", placeholder="예: 위로, 여름밤, 우정")

    st.markdown("---")
    recommend_clicked = st.button("노래 추천 받기", type="primary")

    if recommend_clicked:
        if genre_selection == "직접 입력":
            if not genre or not genre.strip():
                st.warning("장르를 입력해 주세요.")
                st.stop()
            genre = genre.strip()
        
        if not theme.strip():
            st.warning("가사의 테마를 입력해 주세요.")
            st.stop()

        with st.spinner("AI가 노래를 고르는 중입니다..."):
            try:
                songs = request_recommendations(client, mood_level, genre, theme)
            except Exception as exc:  # pylint: disable=broad-except
                st.error(f"추천에 실패했습니다: {exc}")
                st.button("다시 시도", on_click=st.rerun)
                st.stop()

        st.success("추천된 노래를 확인해 보세요!")
        for song in songs:
            render_song_card(song)

    with st.sidebar:
        st.header("도움말")
        st.write("**API 키 발급 방법:**")
        st.write("1. [OpenAI Platform](https://platform.openai.com/api-keys)에 접속")
        st.write("2. 로그인 후 'Create new secret key' 클릭")
        st.write("3. 생성된 키를 복사하여 위의 입력란에 붙여넣기")
        st.write("")
        st.write("**참고:**")
        st.write("- API 키는 세션 동안만 저장됩니다")
        st.write("- 페이지를 새로고침하면 다시 입력해야 합니다")
        st.write("- 추천이 마음에 들지 않으면 조건을 바꾸고 다시 시도해 보세요")


if __name__ == "__main__":
    main()


