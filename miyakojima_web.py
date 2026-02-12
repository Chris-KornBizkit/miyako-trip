import streamlit as st
import pandas as pd
import os
import urllib.parse
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import requests
import folium
from streamlit_folium import st_folium
import random # [NEW] 룰렛용

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Miyako Blue 🐢", page_icon="🐢", layout="wide")

# [NEW] Stargazing Mode (다크 모드 토글) 로직
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# 다크 모드 CSS 적용
if st.session_state.dark_mode:
    page_bg = """
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .wave-header { background: linear-gradient(90deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #b0bec5; box-shadow: none; }
    .card { background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #333; }
    .stMarkdown, .stText, h1, h2, h3, h4, p, li { color: #e0e0e0 !important; }
    a { color: #4fc3f7 !important; }
    .weather-row { border-bottom: 1px solid #333; }
    .streamlit-expanderHeader { background-color: #1e1e1e !important; color: #e0e0e0 !important; }
    </style>
    """
else:
    page_bg = """
    <style>
    .stApp { background: linear-gradient(180deg, #e0f2f1 0%, #f8fbff 30%, #ffffff 100%); font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
    .wave-header { background: linear-gradient(90deg, #0077b6 0%, #00b4d8 50%, #90e0ef 100%); padding: 15px; border-radius: 12px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,180,216,0.1); }
    .wave-header h2 { color: white !important; font-size: 24px !important; margin: 0; font-weight: 700; }
    .wave-header p { font-size: 14px; margin: 5px 0 0 0; opacity: 0.9; }
    .card { background-color: white; padding: 22px; border-radius: 18px; box-shadow: 0 10px 25px rgba(0,0,0,0.03); margin-bottom: 18px; border: none; }
    .sos-card { background-color: #ffebee; border: 1px solid #ffcdd2; padding: 15px; border-radius: 12px; color: #c62828; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; color: #90a4ae; }
    .stTabs [aria-selected="true"] { color: #0077b6 !important; border-bottom-color: #0077b6 !important; }
    .weather-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #eee; }
    .weather-row:last-child { border-bottom: none; }
    a { color: #0077b6; text-decoration: none; font-weight: 600; }
    .streamlit-expanderHeader { font-weight: 700; color: #333; background-color: white; border-radius: 10px; }
    </style>
    """
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

# 데이터 로딩
d_day = (datetime(2026, 2, 16).date() - datetime.now(pytz.timezone('Asia/Seoul')).date()).days
weather_3days = get_miyako_weather_3days()
current_rate = get_exchange_rate()

# Session State (지출, 일기)
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'total_budget' not in st.session_state: st.session_state.total_budget = 150000
if 'diary' not in st.session_state: st.session_state.diary = [] # [NEW] 일기 저장소

# 3. 사이드바
with st.sidebar:
    st.header("🛫 Trip Dashboard")
    
    # [NEW] Stargazing Mode Toggle
    st.toggle("🌌 Stargazing Mode", value=st.session_state.dark_mode, on_change=toggle_theme)
    if st.session_state.dark_mode:
        st.caption("별 관측을 위해 화면을 어둡게 합니다.")

    st.subheader("☀️ Miyako Weather")
    if weather_3days:
        st.markdown(f"""<div style="background:{'#333' if st.session_state.dark_mode else 'white'}; padding:15px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">""", unsafe_allow_html=True)
        for w in weather_3days:
            st.markdown(f"""<div class="weather-row"><span style="font-size:14px; font-weight:600;">{w['day']}</span><span style="font-size:18px;">{w['icon']}</span><span style="font-size:13px; color:{'#ccc' if st.session_state.dark_mode else '#777'};"><span style="color:#ff5252;">{w['max']}°</span> / <span style="color:#448aff;">{w['min']}°</span></span></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # [NEW] Menu Roulette
    st.subheader("🎲 Menu Roulette")
    if st.button("오늘 뭐 먹지? (Pick!)"):
        restaurants = ["블루 터틀", "K's Pit Diner", "코자 소바", "유토피아 팜", "카메 스시", "야키니쿠 나카오", "해리스 쉬림프", "이자카야 훌라", "블루씰 아이스크림"]
        pick = random.choice(restaurants)
        st.success(f"🎉 당첨! **{pick}** 가자!")

    st.markdown("---")
    
    # 환율
    st.subheader("💴 JPY Calc")
    st.caption(f"Rate: 100¥ = {current_rate:.1f}₩")
    jpy_input = st.number_input("JPY", value=1000, step=100)
    st.success(f"🇰🇷 {int(jpy_input * (current_rate / 100)):,} 원")
    st.markdown("---")
    if d_day > 0: st.metric("D-Day", f"D-{d_day}", "설렘 주의!")
    else: st.metric("D-Day", f"D+{abs(d_day)}", "여행 중")
    st.markdown("---")
    
    # BGM
    st.subheader("🎵 BGM")
    st.markdown("""<iframe width="100%" height="200" src="https://www.youtube.com/embed/videoseries?list=PLkH-FRvpGUQTJv2K_bB8AyH1irPasrkiQ" title="Chris Playlist" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>""", unsafe_allow_html=True)
    st.caption("Chris's Pick 🎧")

# 4. 헤더
st.markdown(f"""<div class="wave-header"><h2>Miyako Blue 🐢</h2><p>The Ultimate Super App for Chris.</p></div>""", unsafe_allow_html=True)

# 5. 데이터 (내용 절대 보존)
itinerary_data = [
    ["2/16 (월)", "11:00", "도착", "시모지시마 공항", "렌터카 수령", 20000, "바다 위에 떠 있는 듯한 활주로로 유명한 공항입니다. 도착하자마자 느껴지는 습한 바다 내음과 함께 여행이 시작됩니다."],
    ["2/16 (월)", "12:30", "중식", "블루 터틀", "오션뷰 스테이크", 5000, "이라부섬의 에메랄드빛 바다를 보며 즐기는 야외 테라스 식사. 육즙 가득한 스테이크와 진한 커리가 일품인 뷰 맛집입니다."],
    ["2/16 (월)", "14:00", "관광", "17END", "환상의 물빛 (간조)", 0, "지도에서 사라지는 환상의 해변. 간조 시간에만 하얀 모래섬이 드러나며, 전 세계 어디서도 보기 힘든 투명한 '미야코 블루'의 절정을 선사합니다."],
    ["2/16 (월)", "16:00", "숙소", "힐튼 미야코지마", "체크인", 0, "이라부 대교가 한눈에 보이는 럭셔리 리조트. 로비에서 보는 석양이 예술이며, 신축 호텔다운 쾌적함과 최고의 서비스를 자랑합니다."],
    ["2/16 (월)", "17:00", "쇼핑", "산에이 시티", "마트/의류 쇼핑", 5000, "현지인들의 라이프스타일을 엿볼 수 있는 대형 마트. 호텔에서 먹을 간식과 오키나와 한정 맥주, 그리고 무인양품 쇼핑을 즐겨보세요."],
    ["2/16 (월)", "19:00", "석식", "K's Pit Diner", "미국 감성 다이너", 6000, "1950년대로 시간 여행을 온 듯한 올드카와 힙한 인테리어. 육즙 터지는 미야코규 햄버거와 스테이크는 맥주를 부르는 맛입니다."],
    ["2/17 (화)", "10:00", "관광", "요나하 마에하마", "동양 최고 비치", 0, "동양의 몰디브라 불리는 곳. 7km나 이어지는 눈부신 백사장과 비현실적인 파란 바다의 조화는 멍하니 바라만 봐도 힐링이 됩니다."],
    ["2/17 (화)", "12:00", "중식", "코자 소바", "두툼 삼겹살 소바", 2500, "일반적인 오키나와 소바와는 다릅니다. 그릇을 덮어버릴 만큼 거대한 삼겹살 조림이 올라가 부드러운 식감과 깊은 국물 맛을 자랑합니다."],
    ["2/17 (화)", "13:30", "관광", "히가시 헨나자키", "웅장한 절벽 뷰", 500, "섬의 동쪽 끝, 2km에 달하는 곶이 바다를 향해 뻗어 있습니다. 거친 파도와 웅장한 절벽, 하얀 등대가 어우러진 대자연의 파노라마입니다."],
    ["2/17 (화)", "15:00", "쇼핑", "크로스 포인트", "기념품/리조트룩", 5000, "시기에 리조트 단지 내에 위치한 세련된 쇼핑몰. 미야코지마의 감성을 담은 소품과 황금 거북이 빵 등 유니크한 기념품이 가득합니다."],
    ["2/17 (화)", "16:00", "디저트", "유토피아 팜", "망고 파르페", 2000, "농장에서 직접 재배한 애플망고를 듬뿍 올린 파르페. 꽃들이 만발한 온실 속에서 즐기는 달콤한 휴식은 여행의 피로를 씻어줍니다."],
    ["2/17 (화)", "17:00", "쇼핑", "아타라스 시장", "현지 과일/빵", 2000, "미야코지마의 부엌. 당도 높은 현지 과일(망고, 파인애플)과 갓 구운 빵, 도시락 등을 저렴하게 구입하여 현지인 기분을 내보세요."],
    ["2/17 (화)", "19:00", "석식", "힐튼 디너 뷔페", "호텔 럭셔리 만찬", 16000, "셰프가 즉석에서 요리해주는 라이브 스테이션과 신선한 해산물. 분위기 좋은 호텔 레스토랑에서 즐기는 로맨틱하고 배부른 저녁입니다."],
    ["2/18 (수)", "09:00", "투어", "거북이 스노클링", "야비지 거북이", 15000, "세계적인 산호초 지대 '야비지' 또는 거북이 포인트로 떠납니다. 눈앞에서 유유히 헤엄치는 바다거북과의 만남은 평생 잊지 못할 추억이 됩니다."],
    ["2/18 (수)", "13:30", "중식", "카메 스시", "현지인 런치 스시", 4000, "가성비와 퀄리티를 모두 잡은 로컬 스시 맛집. 미야코지마 근해에서 잡은 신선한 생선으로 만든 초밥을 합리적인 가격에 즐길 수 있습니다."],
    ["2/18 (수)", "15:00", "휴식", "호텔 호캉스", "낮잠 & 온수 샤워", 0, "오전 물놀이 후 즐기는 꿀같은 휴식. 호텔의 푹신한 침구에서 낮잠을 자거나 따뜻한 물로 샤워하며 저녁 일정을 위해 에너지를 충전합니다."],
    ["2/18 (수)", "18:00", "석식", "야키니쿠 나카오", "최상급 미야코규", 15000, "입안에서 살살 녹는 미야코규의 진수. 화려한 마블링의 소고기를 숯불에 구워 먹는 맛은 여행의 하이라이트라 할 수 있습니다."],
    ["2/18 (수)", "20:30", "관광", "별빛 드라이브", "무스누 해변", 0, "가로등 하나 없는 해변, 차 시동을 끄면 쏟아질 듯한 별들이 머리 위로 펼쳐집니다. 운이 좋으면 은하수까지 볼 수 있는 낭만적인 밤입니다."],
    ["2/19 (목)", "11:00", "브런치", "해리스 쉬림프", "갈릭 쉬림프", 3500, "하와이 노스쇼어 스타일의 갈릭 쉬림프 트럭. 이케마 대교를 바라보며 먹는 탱글탱글한 새우와 밥의 조화는 실패 없는 맛입니다."],
    ["2/19 (목)", "13:00", "관광", "이라부 대교", "드라이브", 0, "일본에서 무료로 건널 수 있는 가장 긴 다리(3,540m). 양옆으로 펼쳐진 그라데이션 바다 위를 달리는 드라이브는 미야코지마 여행의 백미입니다."],
    ["2/19 (목)", "15:00", "쇼핑", "이온타운 미나미", "다이소/맥스밸류", 10000, "귀국 전 마지막 쇼핑 타임. 다이소 아이디어 상품, 일본 컵라면, 곤약젤리 등 지인들에게 줄 선물과 생필품을 털어갈 기회입니다."],
    ["2/19 (목)", "18:30", "석식", "이자카야 훌라", "현지 감성 다이닝", 8000, "오키나와 민요가 흘러나오는 활기찬 분위기. 고야 참프루, 라후테 등 오키나와 향토 요리와 오리온 생맥주로 여행의 마지막 밤을 불태우세요."],
    ["2/19 (목)", "20:30", "후식", "블루씰 아이스크림", "소금우유맛", 1000, "오키나와에 왔다면 1일 1블루씰! 단짠단짠의 정석 '소금우유맛' 아이스크림으로 입가심하며 아쉬운 마음을 달래봅니다."],
    ["2/20 (금)", "10:00", "이동", "렌터카 반납", "주유소 경유", 3000, "여행의 마무리. 차량 상태를 확인하고 주유소에 들러 '레귤러 만탄(가득)'을 외치세요. 공항 송영 버스를 타고 출국장으로 이동합니다."],
    ["2/20 (금)", "12:00", "출발", "인천행", "진에어 귀국", 0, "아쉬움을 뒤로하고 일상으로 돌아가는 시간. 창밖으로 멀어지는 미야코 블루를 눈에 담으며 다음 여행을 기약합니다."]
]
df_itinerary = pd.DataFrame(itinerary_data, columns=["날짜", "시간", "구분", "장소", "요약", "비용", "설명"])

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
    
    # [NEW] One-Line Diary
    st.markdown("#### 📝 One-Line Diary (Today's Vibe)")
    with st.form("diary_form"):
        note = st.text_input("오늘 가장 좋았던 순간은?")
        submit_note = st.form_submit_button("기록하기 (Save)")
        if submit_note and note:
            timestamp = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%m/%d %H:%M")
            st.session_state.diary.append(f"[{timestamp}] {note}")
            st.success("기록되었습니다! 💾")
            st.rerun()
    
    if st.session_state.diary:
        st.info("\n\n".join(st.session_state.diary))

    c1, c2 = st.columns(2)
    df_cost = pd.DataFrame({"항목": ["식비", "교통", "투어/입장", "쇼핑/기타"], "비용": [66000, 23000, 24500, 22000]})
    with c1: st.dataframe(df_cost, use_container_width=True)
    with c2: st.plotly_chart(px.pie(df_cost, values='비용', names='항목', hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r), use_container_width=True)

with tab_map:
    st.markdown("### 🗺️ Grand Map Dashboard")
    m = folium.Map(location=[24.80, 125.28], zoom_start=11)
    for name, coords in locations.items():
        folium.Marker(coords, popup=name, tooltip=name, icon=folium.Icon(color="blue" if "힐튼" not in name else "red", icon="info-sign")).add_to(m)
    st_folium(m, width=700, height=500)

with tab1: # 모바일 스크롤 최적화
    day_sel = st.selectbox("Select Your Day", df_itinerary['날짜'].unique())
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.markdown(f"##### {day_sel} Schedule")
        for _, r in df_itinerary[df_itinerary['날짜'] == day_sel].iterrows():
            with st.expander(f"⏰ {r['시간']} | {r['장소']} ({r['구분']})"):
                st.markdown(f"**💡 {r['요약']}**")
                st.write(r['설명'])
                st.link_button(f"📍 구글 지도 보기", get_map_url(r['장소']))
    with col_r:
        idx = list(df_itinerary['날짜'].unique()).index(day_sel) + 1
        if os.path.exists(f"0{idx}.png"): st.image(f"0{idx}.png", caption=f"Day {idx} Route", use_container_width=True)

with tab2: 
    st.markdown("### The Hidden Gems")
    cl1, cl2 = st.columns(2)
    with cl1: st.markdown(f"""<div class="card"><h4>🏖️ Hidden Beaches</h4><ul><li><a href="{get_map_url('스나야마 비치')}" target="_blank">스나야마 비치</a>: 바위 아치 석양</li><li><a href="{get_map_url('나가마하마 비치')}" target="_blank">나가마하마 비치</a>: 프라이빗 비밀 해변</li><li><a href="{get_map_url('토구치노하마')}" target="_blank">토구치노하마</a>: 파우더 샌드</li></ul><br><h4>🛍️ Boutique Shopping</h4><ul><li><a href="{get_map_url('디자트')}" target="_blank">디자트</a>: 세련된 소품샵</li><li><a href="{get_map_url('나모시아')}" target="_blank">나모시아</a>: 핸드메이드 액세서리</li></ul></div>""", unsafe_allow_html=True)
    with cl2: st.markdown(f"""<div class="card"><h4>🍱 Local's Choice</h4><ul><li><a href="{get_map_url('마루요시 소바')}" target="_blank">마루요시 소바</a>: 전설의 소바</li><li><a href="{get_map_url('모쟈노 빵집')}" target="_blank">모쟈노 빵집</a>: 오픈런 베이커리</li><li><a href="{get_map_url('보쿠노 키친')}" target="_blank">보쿠노 키친</a>: 이탈리안 퓨전</li></ul><br><h4>📸 Photo Op</h4><ul><li><a href="{get_map_url('이케마 대교 전망대')}" target="_blank">이케마 대교 전망대</a>: 숨겨진 뷰포인트</li></ul></div>""", unsafe_allow_html=True)

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
        with st.expander("🔌 전자기기 & 촬영"):
            for i in ["돼지코 (110V)", "보조배터리", "멀티탭", "충전 케이블", "삼각대/셀카봉"]: st.checkbox(i)
        with st.expander("🏊‍♂️ 물놀이 & 의류"):
            for i in ["수영복/래시가드", "아쿠아슈즈", "스노클링 장비", "방수팩", "선글라스/모자", "선크림"]: st.checkbox(i)
        with st.expander("💊 비상약 & 기타"):
            for i in ["멀미약", "소화제/진통제", "대일밴드", "물티슈/휴지"]: st.checkbox(i)
    with col_util:
        st.markdown("#### 🗣️ Survival Japanese")
        t1, t2, t3 = st.tabs(["🚗 운전", "🍱 식당", "🆘 응급"])
        with t1: 
            st.info("주유: 레귤러 만탄 오네가이 (일반 가득)")
            st.info("주차: 코코니 토메테모 이이데스까? (주차 돼요?)")
        with t2:
            st.success("주문: 고레 히토츠 (이거 하나)")
            st.success("고수: 파쿠치 누키데 (고수 빼고)")
            st.success("계산: 오카이케 오네가이 (계산요)")
        with t3:
            st.error("도와줘요: 다스케테 구다사이!")
            st.warning("화장실: 토이레와 도코 데스까?")
        st.markdown("---")
        st.markdown("""<div class="sos-card"><b>👮 경찰:</b> 110 / <b>🚑 구급:</b> 119<br><b>📞 영사관:</b> +81-92-771-0461</div>""", unsafe_allow_html=True)

with tab5:
    st.markdown("### 💰 Smart Wallet (Budget Tracker)")
    col_budget, col_add = st.columns([1, 1.5])
    with col_budget:
        st.markdown("#### 📊 Budget Status")
        total_spent = sum([x['amount'] for x in st.session_state.expenses])
        remaining = st.session_state.total_budget - total_spent
        progress = min(1.0, total_spent / st.session_state.total_budget)
        st.metric("Total Budget", f"¥ {st.session_state.total_budget:,}")
        st.metric("Total Spent", f"¥ {total_spent:,}", delta=f"- {total_spent:,}")
        st.metric("Remaining", f"¥ {remaining:,}", delta=f"{remaining:,}", delta_color="normal")
        st.progress(progress)
    with col_add:
        st.markdown("#### 📝 Add Expense")
        with st.form("expense_form"):
            item = st.text_input("내역 (예: 점심, 기념품)")
            amount = st.number_input("금액 (엔)", min_value=0, step=100)
            submit = st.form_submit_button("추가 (Add)")
            if submit and item and amount > 0:
                st.session_state.expenses.append({"item": item, "amount": amount})
                st.success(f"✅ {item} (¥{amount:,}) 추가됨!")
                st.rerun()
    st.markdown("---")
    st.markdown("#### 🧾 History")
    if st.session_state.expenses: st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True)
    else: st.info("아직 지출 내역이 없습니다.")

st.markdown("---")
st.caption("Designed with 🐢 for Chris.")