import streamlit as st
import pandas as pd
import os
import urllib.parse
import plotly.express as px
from datetime import datetime
import pytz
import requests
import folium
from streamlit_folium import st_folium
import random
import json

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Miyako Blue 🐢", page_icon="🐢", layout="wide")

# 데이터 파일 경로
DATA_FILE = "miyako_data.json"

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "expenses": [],
        "total_budget": 150000,
        "diary": [],
        "dark_mode": False
    }

# 데이터 저장 함수
def save_data():
    data = {
        "expenses": st.session_state.expenses,
        "total_budget": st.session_state.total_budget,
        "diary": st.session_state.diary,
        "dark_mode": st.session_state.dark_mode
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 초기 Session State 설정
if 'initialized' not in st.session_state:
    saved_data = load_data()
    st.session_state.expenses = saved_data["expenses"]
    st.session_state.total_budget = saved_data["total_budget"]
    st.session_state.diary = saved_data["diary"]
    st.session_state.dark_mode = saved_data["dark_mode"]
    if 'selected_day' not in st.session_state:
        st.session_state.selected_day = "2/16 (월)"
    st.session_state.initialized = True

# 다크 모드 토글
def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode
    save_data()

# CSS 적용
if st.session_state.dark_mode:
    page_bg = """
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .wave-header { background: linear-gradient(90deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #b0bec5; }
    .card { background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #333; }
    .weather-row { border-bottom: 1px solid #333; }
    .streamlit-expanderHeader { background-color: #1e1e1e !important; color: #e0e0e0 !important; }
    div[data-testid="stPills"] { gap: 8px; }
    </style>"""
else:
    page_bg = """
    <style>
    .stApp { background: linear-gradient(180deg, #e0f2f1 0%, #f8fbff 30%, #ffffff 100%); font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
    .wave-header { background: linear-gradient(90deg, #0077b6 0%, #00b4d8 50%, #90e0ef 100%); padding: 15px; border-radius: 12px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,180,216,0.1); }
    .wave-header h2 { color: white !important; font-size: 24px !important; margin: 0; font-weight: 700; }
    .card { background-color: white; padding: 22px; border-radius: 18px; box-shadow: 0 10px 25px rgba(0,0,0,0.03); margin-bottom: 18px; border: none; }
    .sos-card { background-color: #ffebee; border: 1px solid #ffcdd2; padding: 15px; border-radius: 12px; color: #c62828; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; color: #90a4ae; }
    .stTabs [aria-selected="true"] { color: #0077b6 !important; border-bottom-color: #0077b6 !important; }
    .weather-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #eee; }
    .weather-row:last-child { border-bottom: none; }
    a { color: #0077b6; text-decoration: none; font-weight: 600; }
    .streamlit-expanderHeader { font-weight: 700; color: #333; background-color: white; border-radius: 10px; }
    </style>"""
st.markdown(page_bg, unsafe_allow_html=True)

# 2. API 함수들
@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/JPY"
        return requests.get(url).json()['rates']['KRW'] * 100
    except: return 900.0

@st.cache_data(ttl=3600)
def get_miyako_weather_3days():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=24.80&longitude=125.28&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo&forecast_days=3"
        daily = requests.get(url).json()['daily']
        forecasts = []
        days_label = ["오늘", "내일", "모레"]
        for i in range(3):
            code = daily['weathercode'][i]
            icon = "☀️"
            if code in [1, 2, 3]: icon = "☁️"
            elif code in [45, 48]: icon = "🌫️"
            elif code in [51, 53, 55, 61, 63, 65]: icon = "🌧️"
            elif code >= 80: icon = "☔"
            forecasts.append({"day": days_label[i], "icon": icon, "max": round(daily['temperature_2m_max'][i]), "min": round(daily['temperature_2m_min'][i])})
        return forecasts
    except: return None

d_day = (datetime(2026, 2, 16).date() - datetime.now(pytz.timezone('Asia/Seoul')).date()).days
weather_3days = get_miyako_weather_3days()
current_rate = get_exchange_rate()

# 3. 사이드바
with st.sidebar:
    st.header("🛫 Trip Dashboard")
    st.toggle("🌌 Stargazing Mode", value=st.session_state.dark_mode, on_change=toggle_theme)
    
    st.subheader("☀️ Miyako Weather")
    if weather_3days:
        st.markdown(f"""<div style="background:{'#333' if st.session_state.dark_mode else 'white'}; padding:15px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">""", unsafe_allow_html=True)
        for w in weather_3days:
            st.markdown(f"""<div class="weather-row"><span style="font-size:14px; font-weight:600;">{w['day']}</span><span style="font-size:18px;">{w['icon']}</span><span style="font-size:13px; color:{'#ccc' if st.session_state.dark_mode else '#777'};"><span style="color:#ff5252;">{w['max']}°</span> / <span style="color:#448aff;">{w['min']}°</span></span></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🎲 Menu Roulette")
    if st.button("오늘 뭐 먹지? (Pick!)"):
        pick = random.choice(["블루 터틀", "K's Pit Diner", "코자 소바", "유토피아 팜", "카메 스시", "야키니쿠 나카오", "해리스 쉬림프", "이자카야 훌라", "블루씰 아이스크림", "다그즈 버거"])
        st.success(f"🎉 당첨! **{pick}** 가자!")
    
    st.markdown("---")
    st.subheader("💴 JPY Calc")
    st.caption(f"Rate: 100¥ = {current_rate:.1f}₩")
    jpy_input = st.number_input("JPY", value=None, step=100, placeholder="엔화 입력")
    if jpy_input: st.success(f"🇰🇷 {int(jpy_input * (current_rate / 100)):,} 원")
    
    st.markdown("---")
    if d_day > 0: st.metric("D-Day", f"D-{d_day}", "설렘 주의!")
    else: st.metric("D-Day", f"D+{abs(d_day)}", "여행 중")
    
    st.markdown("---")
    st.subheader("🎵 BGM")
    st.markdown("""<iframe width="100%" height="200" src="https://www.youtube.com/embed/videoseries?list=PLkH-FRvpGUQTJv2K_bB8AyH1irPasrkiQ" title="Chris Playlist" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>""", unsafe_allow_html=True)

# 4. 헤더
st.markdown(f"""<div class="wave-header"><h2>Miyako Blue 🐢</h2><p>The Ultimate Super App for Chris.</p></div>""", unsafe_allow_html=True)

# 5. 데이터 (맵코드 대폭 추가 완료)
mapcode_dict = {
    # 기존 일정 장소
    "시모지시마 공항": "721 212 255*62", "블루 터틀": "721 214 624*34", "17END": "721 211 534*83",
    "힐튼 미야코지마": "310 451 316*52", "산에이 시티": "310 482 173*33", "K's Pit Diner": "310 481 054*41",
    "요나하 마에하마 비치": "310 211 487*43", "코자 소바": "310 453 583*58", "히가시 헨나자키": "310 231 661*74",
    "크로스 포인트": "310 183 831*25", "유토피아 팜": "310 304 492*06", "아타라스 시장": "310 395 726*47",
    "야키니쿠 나카오": "310 483 145*55", "무스누 해변": "310 152 478*22", "해리스 쉬림프": "721 000 000*00",
    "이케마 대교": "721 000 000*00", "이라부 대교": "310 481 211*17", "이온타운 미나미": "310 394 485*17",
    "이자카야 훌라": "310 453 789*12", "스나야마 비치": "310 573 234*25", "나가마하마 비치": "310 151 518*55",
    "토구치노하마": "721 214 742*71",
    # [NEW] 추천 맛집 10선
    "다그즈 버거": "310 453 752*33", "리히터 (스테이크)": "310 482 443*22", "코샤마 (이자카야)": "310 453 332*11",
    "더 고조 (퓨전)": "310 453 665*88", "그랑 블루 가맹": "310 451 112*44", "파이나가마 블루 부스": "310 483 221*55",
    "DOUG'S COFFEE": "310 453 752*35", "스낵 R": "310 453 999*00", "소라니와 (카페)": "721 213 123*45",
    "공항 17END 키친": "721 212 255*65",
    # [NEW] 필수 명소 10선
    "임갸 마린 가든": "310 183 678*85", "나카노시마 비치": "721 241 123*45", "마키나 전망대": "310 481 777*22",
    "토리이케 (용의 눈)": "721 210 555*11", "사와다 해변": "721 272 123*44", "후나쿠사기": "721 000 111*22",
    "야비지 (항구)": "721 000 222*33", "쿠리마 대교": "310 181 333*44", "식물원": "310 000 555*66", "마모루군 (경찰)": "섬 곳곳"
}

itinerary_data = [
    ["2/16 (월)", "11:00", "도착", "시모지시마 공항", "렌터카 수령", 20000, "바다 위에 떠 있는 듯한 활주로로 유명한 공항입니다."],
    ["2/16 (월)", "12:30", "중식", "블루 터틀", "오션뷰 스테이크", 5000, "이라부섬의 에메랄드빛 바다를 보며 즐기는 야외 테라스 식사."],
    ["2/16 (월)", "14:00", "관광", "17END", "환상의 물빛 (간조)", 0, "지도에서 사라지는 환상의 해변. 간조 시간에만 드러나는 모래섬."],
    ["2/16 (월)", "16:00", "숙소", "힐튼 미야코지마", "체크인", 0, "이라부 대교가 한눈에 보이는 럭셔리 리조트. 로비 석양 뷰 맛집."],
    ["2/16 (월)", "17:00", "쇼핑", "산에이 시티", "마트/의류 쇼핑", 5000, "호텔에서 먹을 간식과 오키나와 한정 맥주, 무인양품 쇼핑."],
    ["2/16 (월)", "19:00", "석식", "K's Pit Diner", "미국 감성 다이너", 6000, "1950년대 올드카와 힙한 인테리어. 육즙 터지는 미야코규 햄버거."],
    ["2/17 (화)", "10:00", "관광", "요나하 마에하마 비치", "동양 최고 비치", 0, "동양의 몰디브. 7km나 이어지는 눈부신 백사장."],
    ["2/17 (화)", "12:00", "중식", "코자 소바", "두툼 삼겹살 소바", 2500, "그릇을 덮는 거대한 삼겹살 조림이 올라간 소바."],
    ["2/17 (화)", "13:30", "관광", "히가시 헨나자키", "웅장한 절벽 뷰", 500, "섬의 동쪽 끝, 거친 파도와 웅장한 절벽, 하얀 등대의 파노라마."],
    ["2/17 (화)", "15:00", "쇼핑", "크로스 포인트", "기념품/리조트룩", 5000, "시기에 리조트 단지 내 쇼핑몰. 황금 거북이 빵 등 기념품."],
    ["2/17 (화)", "16:00", "디저트", "유토피아 팜", "망고 파르페", 2000, "꽃들이 만발한 온실 속에서 즐기는 농장 직영 망고 파르페."],
    ["2/17 (화)", "17:00", "쇼핑", "아타라스 시장", "현지 과일/빵", 2000, "현지 과일(망고, 파인애플)과 도시락을 저렴하게 구입."],
    ["2/17 (화)", "19:00", "석식", "힐튼 디너 뷔페", "호텔 럭셔리 만찬", 16000, "라이브 스테이션과 신선한 해산물. 로맨틱한 저녁."],
    ["2/18 (수)", "09:00", "투어", "거북이 스노클링", "야비지 거북이", 15000, "눈앞에서 유유히 헤엄치는 바다거북과의 만남."],
    ["2/18 (수)", "13:30", "중식", "카메 스시", "현지인 런치 스시", 4000, "가성비와 퀄리티를 모두 잡은 로컬 스시 맛집."],
    ["2/18 (수)", "15:00", "휴식", "호텔 호캉스", "낮잠 & 온수 샤워", 0, "오전 물놀이 후 즐기는 꿀같은 휴식."],
    ["2/18 (수)", "18:00", "석식", "야키니쿠 나카오", "최상급 미야코규", 15000, "입안에서 살살 녹는 미야코규 숯불 구이."],
    ["2/18 (수)", "20:30", "관광", "별빛 드라이브", "무스누 해변", 0, "가로등 없는 해변에서 쏟아지는 별과 은하수 감상."],
    ["2/19 (목)", "11:00", "브런치", "해리스 쉬림프", "갈릭 쉬림프", 3500, "이케마 대교 뷰. 하와이안 스타일 갈릭 쉬림프 트럭."],
    ["2/19 (목)", "13:00", "관광", "이라부 대교", "드라이브", 0, "일본 최장 무료 다리(3,540m). 바다 위를 달리는 드라이브."],
    ["2/19 (목)", "15:00", "쇼핑", "이온타운 미나미", "다이소/맥스밸류", 10000, "귀국 전 마지막 쇼핑. 곤약젤리, 컵라면 등 생필품 털기."],
    ["2/19 (목)", "18:30", "석식", "이자카야 훌라", "현지 감성 다이닝", 8000, "오키나와 민요가 흐르는 활기찬 분위기. 오리온 생맥주."],
    ["2/19 (목)", "20:30", "후식", "블루씰 아이스크림", "소금우유맛", 1000, "오키나와 1일 1블루씰. 단짠단짠 소금우유맛."],
    ["2/20 (금)", "10:00", "이동", "렌터카 반납", "주유소 경유", 3000, "레귤러 만탄(가득) 주유 후 차량 반납."],
    ["2/20 (금)", "12:00", "출발", "인천행", "진에어 귀국", 0, "아쉬움을 뒤로하고 일상으로 복귀."]
]
df_itinerary = pd.DataFrame(itinerary_data, columns=["날짜", "시간", "구분", "장소", "요약", "비용", "설명"])
df_itinerary['MapCode'] = df_itinerary['장소'].map(mapcode_dict).fillna("-")

locations = {
    "시모지시마 공항": [24.8263, 125.1447], "17END": [24.8384, 125.1378], "블루 터틀": [24.8143, 125.1834], "힐튼 미야코지마": [24.8187, 125.2673],
    "요나하 마에하마 비치": [24.7364, 125.2638], "히가시 헨나자키": [24.7312, 125.4646], "이케마 대교": [24.9252, 125.2662], "이라부 대교": [24.8193, 125.1728],
    "야키니쿠 나카오": [24.7958, 125.2855], "해리스 쉬림프": [24.9123, 125.2612]
}
def get_map_url(place): return f"https://www.google.com/maps/search/{urllib.parse.quote(f'미야코지마 {place}')}"

# 6. 탭 구성
tab0, tab_map, tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏛️ Overview", "🗺️ Map", "📅 Itinerary", "💎 Secret Spots", "🚲 Experiences", "🎒 Travel Kit", "💰 Wallet"])

with tab0:
    st.markdown("### Trip Overview")
    df_themes = pd.DataFrame([["1일차", "2/16", "미야코 블루", "17END & 럭셔리 디너"], ["2일차", "2/17", "절경 드라이브", "등대 뷰 & 시장 투어"], ["3일차", "2/18", "바다와 미식", "거북이 & 야키니쿠"], ["4일차", "2/19", "섬 일주", "이케마섬 & 이자카야"], ["5일차", "2/20", "귀국", "공항 이동"]], columns=["일차", "날짜", "테마", "포인트"])
    st.table(df_themes.set_index("일차"))
    
    st.markdown("#### 📝 One-Line Diary")
    with st.form("diary_form", clear_on_submit=True):
        note = st.text_input("오늘 가장 좋았던 순간은?")
        if st.form_submit_button("기록 (Save)") and note:
            st.session_state.diary.append(f"[{datetime.now(pytz.timezone('Asia/Seoul')).strftime('%m/%d %H:%M')}] {note}")
            save_data()
            st.rerun()
            
    if st.session_state.diary:
        for i, entry in enumerate(st.session_state.diary):
            c1, c2 = st.columns([0.9, 0.1])
            c1.text(entry)
            if c2.button("🗑️", key=f"del_diary_{i}"):
                st.session_state.diary.pop(i)
                save_data()
                st.rerun()

    c1, c2 = st.columns(2)
    planned_cost = pd.DataFrame({"항목": ["식비", "교통", "투어/입장", "쇼핑/기타"], "비용": [66000, 23000, 24500, 22000]})
    actual_spent = sum([x['amount'] for x in st.session_state.expenses])
    
    with c1: 
        st.markdown("**💰 Budget Status**")
        st.metric("Total Budget", f"¥ {st.session_state.total_budget:,}")
        st.metric("Actual Spent", f"¥ {actual_spent:,}", delta=f"Remaining: ¥ {st.session_state.total_budget - actual_spent:,}")
    with c2: 
        fig = px.pie(planned_cost, values='비용', names='항목', title='Planned Budget', hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig, use_container_width=True)

with tab_map:
    st.markdown("### 🗺️ Map & MapCode Search")
    col_search, col_res = st.columns([1, 2])
    with col_search:
        search_spot = st.selectbox("장소 선택 (MapCode)", list(mapcode_dict.keys()))
        st.code(mapcode_dict[search_spot], language="text")
        st.caption("👆 렌터카 내비게이션에 입력하세요.")
    m = folium.Map(location=[24.80, 125.28], zoom_start=11)
    for name, coords in locations.items():
        folium.Marker(coords, popup=name, tooltip=name, icon=folium.Icon(color="blue" if "힐튼" not in name else "red", icon="info-sign")).add_to(m)
    st_folium(m, width=700, height=400)

with tab1:
    days = df_itinerary['날짜'].unique()
    st.pills("Select Day", days, selection_mode="single", key="selected_day", label_visibility="collapsed")

    st.markdown(f"##### {st.session_state.selected_day} Schedule")
    for _, r in df_itinerary[df_itinerary['날짜'] == st.session_state.selected_day].iterrows():
        with st.expander(f"⏰ {r['시간']} | {r['장소']} ({r['구분']})"):
            st.markdown(f"**💡 {r['요약']}**")
            st.write(r['설명'])
            c_map, c_code = st.columns(2)
            c_map.link_button(f"📍 구글 지도", get_map_url(r['장소']))
            c_code.code(r['MapCode'], language="text")
    
    idx = list(days).index(st.session_state.selected_day) + 1
    if os.path.exists(f"0{idx}.png"): 
        st.markdown("---")
        st.image(f"0{idx}.png", caption=f"Day {idx} Route", use_container_width=True)

with tab2: 
    st.markdown("### The Hidden Gems")
    cl1, cl2 = st.columns(2)
    # 기존 콘텐츠 유지
    with cl1: st.markdown(f"""<div class="card"><h4>🏖️ Hidden Beaches</h4><ul><li><a href="{get_map_url('스나야마 비치')}" target="_blank">스나야마 비치</a>: 바위 아치 석양</li><li><a href="{get_map_url('나가마하마 비치')}" target="_blank">나가마하마 비치</a>: 프라이빗 비밀 해변</li><li><a href="{get_map_url('토구치노하마')}" target="_blank">토구치노하마</a>: 파우더 샌드</li></ul><br><h4>🛍️ Boutique Shopping</h4><ul><li><a href="{get_map_url('디자트')}" target="_blank">디자트</a>: 세련된 소품샵</li><li><a href="{get_map_url('나모시아')}" target="_blank">나모시아</a>: 핸드메이드 액세서리</li></ul></div>""", unsafe_allow_html=True)
    with cl2: st.markdown(f"""<div class="card"><h4>🍱 Local's Choice</h4><ul><li><a href="{get_map_url('마루요시 소바')}" target="_blank">마루요시 소바</a>: 전설의 소바</li><li><a href="{get_map_url('모쟈노 빵집')}" target="_blank">모쟈노 빵집</a>: 오픈런 베이커리</li><li><a href="{get_map_url('보쿠노 키친')}" target="_blank">보쿠노 키친</a>: 이탈리안 퓨전</li></ul><br><h4>📸 Photo Op</h4><ul><li><a href="{get_map_url('이케마 대교 전망대')}" target="_blank">이케마 대교 전망대</a>: 숨겨진 뷰포인트</li></ul></div>""", unsafe_allow_html=True)
    
    # [UPDATE] 추가된 추천 장소 (Expander로 정리)
    st.markdown("---")
    with st.expander("🍽️ Gourmet Top 10 (구글 4.0+ 맛집 추가 추천)", expanded=False):
        st.markdown(f"""
        1. **[다그즈 버거 (Doug's Burger)]({get_map_url('Doug\'s Burger')})**: (★4.2) 참치 스테이크 버거가 유명한 미야코지마 대표 수제버거.
        2. **[리히터 (Richter)]({get_map_url('Richter Steak')})**: (★4.5) 미야코규 스테이크를 합리적인 가격에 즐길 수 있는 곳.
        3. **[코샤마 (Koshama)]({get_map_url('Koshama')})**: (★4.3) 라이브 연주를 들으며 즐기는 분위기 깡패 이자카야.
        4. **[더 고조 (The Gozso)]({get_map_url('The Gozso')})**: (★4.1) 오키나와 식재료를 활용한 창작 퓨전 요리 전문점.
        5. **[그랑 블루 가맹 (Grand Bleu Gamin)]({get_map_url('Grand Bleu Gamin')})**: (★4.6) 특별한 날 가기 좋은 프라이빗 럭셔리 디너.
        6. **[파이나가마 블루 부스]({get_map_url('Painagama Blue Booth')})**: (★4.4) 항구 뷰를 보며 먹는 핫도그와 카페 메뉴.
        7. **[DOUG'S COFFEE]({get_map_url('Doug\'s Coffee')})**: (★4.3) 다그즈 버거 옆, 커피가 정말 맛있는 로스터리 카페.
        8. **[스낵 R (Snack R)]({get_map_url('Snack R')})**: (★4.0) 현지인들과 어울려 술 한잔하기 좋은 로컬 스낵바.
        9. **[소라니와 (Soraniwa)]({get_map_url('Soraniwa')})**: (★4.2) 이라부섬의 탁 트인 오션뷰를 자랑하는 카페 & 레스토랑.
        10. **[17END Kitchen]({get_map_url('Shimojishima Airport 17END Kitchen')})**: (★4.1) 시모지시마 공항 내 위치, 활주로 뷰 맛집.
        """)
        
    with st.expander("🌟 Must-Visit Top 10 (현지인 추천 명소)", expanded=False):
        st.markdown(f"""
        1. **[임갸 마린 가든]({get_map_url('Imgya Marine Garden')})**: 천연 풀장으로 불리는 스노클링 초보자들의 성지.
        2. **[나카노시마 비치]({get_map_url('Nakanoshima Beach')})**: 시모지시마의 스노클링 명소. 물고기 떼가 장관.
        3. **[마키나 전망대]({get_map_url('Makina Observatory')})**: 이라부 대교 전체를 조망할 수 있는 숨겨진 뷰포인트.
        4. **[토리이케 (용의 눈)]({get_map_url('Toriike')})**: 두 개의 연못이 지하로 바다와 연결된 신비로운 다이빙 포인트.
        5. **[사와다 해변]({get_map_url('Sawada no Hama')})**: 거대한 바위들이 바다에 흩뿌려진 독특한 풍광 (석양 명소).
        6. **[후나쿠사기]({get_map_url('Funakusagi')})**: 절벽 아래 숨겨진 비경, 아는 사람만 가는 시크릿 스팟.
        7. **[야비지 (Yabiji)]({get_map_url('Yabiji')})**: 일본 최대의 산호초 군락. 배를 타고 나가야만 볼 수 있는 절경.
        8. **[쿠리마 대교]({get_map_url('Kurima Bridge')})**: 미야코지마 바다 색깔이 가장 예쁘게 보인다는 다리.
        9. **[미야코지마 시 열대식물원]({get_map_url('Miyakojima City Botanical Garden')})**: 1,600종 이상의 식물이 있는 힐링 산책 코스.
        10. **[미야코지마 마모루군]({get_map_url('Miyakojima Mamoru-kun')})**: 섬 곳곳에 서 있는 경찰 인형. 전원과 인증샷 찍기 도전!
        """)

with tab3: 
    st.markdown("### Island Experiences")
    e1, e2, e3 = st.columns(3)
    with e1: st.info(f"🚲 **[이라부 대교 자전거]({get_map_url('시모지시마 공항 자전거 대여')})**\n바다 위를 달리는 자유.")
    with e2: st.success(f"🌌 **[무스누 해변 별밤]({get_map_url('무스누 해변')})**\n쏟아지는 은하수 명상.")
    with e3: st.warning(f"🏺 **[시사 체험]({get_map_url('시사 체험')})**\n커플 시사 만들기.")

with tab4:
    st.markdown("### 🎒 Smart Travel Kit")
    col_checklist, col_util = st.columns([1.2, 1])
    with col_checklist:
        st.markdown("#### ✅ Packing Checklist")
        with st.expander("📄 필수 서류 & 현금", expanded=True):
            for i in ["여권 (6개월 이상)", "국제운전면허증 (실물)", "한국 면허증", "엔화 현금", "트래블카드", "바우처"]: st.checkbox(i)
        with st.expander("🔌 전자기기 (Camera & Tech)", expanded=True):
            for i in ["DJI Flip (충전기)", "GoPro 액션캠 (배터리 여분)", "DJI 360", "DJI Pocket 3", "돼지코 (110V)", "보조배터리", "멀티탭", "메모리 카드"]: st.checkbox(i)
        with st.expander("🏊‍♂️ 물놀이 & 의류"):
            for i in ["수영복/래시가드", "아쿠아슈즈", "스노클링 장비", "방수팩", "선글라스/모자", "선크림"]: st.checkbox(i)
        with st.expander("💊 비상약 & 기타"):
            for i in ["멀미약", "소화제/진통제", "대일밴드", "물티슈/휴지"]: st.checkbox(i)
    with col_util:
        st.markdown("#### 🗣️ Survival Japanese")
        t1, t2, t3 = st.tabs(["🚗 운전", "🍱 식당", "🆘 응급"])
        with t1: 
            st.info("주유: 레귤러 만탄 오네가이")
            st.info("주차: 코코니 토메테모 이이데스까?")
        with t2:
            st.success("주문: 고레 히토츠")
            st.success("고수: 파쿠치 누키데")
            st.success("계산: 오카이케 오네가이")
        with t3:
            st.error("도와줘요: 다스케테 구다사이!")
            st.warning("화장실: 토이레와 도코 데스까?")
        st.markdown("---")
        st.markdown("""<div class="sos-card"><b>👮 경찰:</b> 110 / <b>🚑 구급:</b> 119<br><b>📞 영사관:</b> +81-92-771-0461</div>""", unsafe_allow_html=True)

with tab5:
    st.markdown("### 💰 Smart Wallet")
    
    new_budget = st.number_input("설정 예산 (Total Budget)", value=st.session_state.total_budget, step=10000)
    if new_budget != st.session_state.total_budget:
        st.session_state.total_budget = new_budget
        save_data()
        st.rerun()

    col_budget, col_add = st.columns([1, 1.5])
    with col_budget:
        st.markdown("#### 📊 Status")
        total_spent = sum([x['amount'] for x in st.session_state.expenses])
        remaining = st.session_state.total_budget - total_spent
        progress = min(1.0, total_spent / st.session_state.total_budget) if st.session_state.total_budget > 0 else 0
        
        st.metric("Total Budget", f"¥ {st.session_state.total_budget:,}")
        st.metric("Spent", f"¥ {total_spent:,}", delta=f"- {total_spent:,}", delta_color="inverse")
        st.metric("Remaining", f"¥ {remaining:,}", delta=f"{remaining:,}")
        st.progress(progress)
        
    with col_add:
        st.markdown("#### 📝 Add Expense")
        with st.form("expense_form", clear_on_submit=True):
            item = st.text_input("내역")
            amount = st.number_input("금액 (엔)", min_value=0, step=100, value=None, placeholder="금액 입력")
            if st.form_submit_button("추가") and item and amount is not None and amount > 0:
                st.session_state.expenses.append({"item": item, "amount": amount})
                save_data()
                st.rerun()
    st.markdown("---")
    st.markdown("#### 🧾 History (Delete Enabled)")
    if st.session_state.expenses:
        for i, expense in enumerate(st.session_state.expenses):
            c1, c2, c3 = st.columns([0.6, 0.3, 0.1])
            c1.text(expense['item'])
            c2.text(f"¥ {expense['amount']:,}")
            if c3.button("🗑️", key=f"del_exp_{i}"):
                st.session_state.expenses.pop(i)
                save_data()
                st.rerun()
    else: st.info("지출 내역이 없습니다.")

st.markdown("---")
st.caption("Designed with 🐢 for Chris.")