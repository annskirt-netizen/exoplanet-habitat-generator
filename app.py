import streamlit as st
import pandas as pd
import plotly.express as px
import random

# 웹페이지 제목
st.title("🌌 외계 행성 물리환경 및 생명체 거주 가능성 시뮬레이터")
st.write("항성 광도뿐만 아니라 **행성 궤도, 중력, 대기압, 기체 성분**을 종합적으로 고려하여 거주 가능성을 분석합니다.")

# 1. stars.csv 파일 불러오기
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("stars.csv")
    except:
        data = {
            "Star_Name": ["Sun (태양계)", "TRAPPIST-1"],
            "Luminosity": [1.0, 0.00052],
            "Mass": [1.0, 0.09],
            "Description": ["태양계", "트라피스트-1계"]
        }
        df = pd.DataFrame(data)
    return df

df = load_data()

# 2. 사이드바: 항성 및 행성 물리 변수 설정
st.sidebar.header("⚙️ 1단계: 항성(별) 선택")
selected_star = st.sidebar.selectbox("분석할 천체 선택", df["Star_Name"])

star_row = df[df["Star_Name"] == selected_star].iloc[0]
L = float(star_row["Luminosity"])
desc = star_row["Description"]

st.info(f"📌 **선택된 천체 정보:** {desc}")

# 골디락스 존 계산 (광도 기반 거리)
d_inner = (L / 1.1) ** 0.5
d_outer = (L / 0.53) ** 0.5

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 2단계: 행성 물리 환경 설정")
planet_distance = st.sidebar.slider("공전궤도 반지름 (AU)", 0.001, float(max(d_outer * 1.5, 5.0)), 1.0)
planet_mass = st.sidebar.slider("행성 질량 (지구=1.0 기준)", 0.1, 10.0, 1.0)
planet_radius = st.sidebar.slider("행성 반지름 (지구=1.0 기준)", 0.5, 3.0, 1.0)

# 중력 계산 공식 (표면 중력 g = 질량 / 반지름^2)
gravity = planet_mass / (planet_radius ** 2)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 3단계: 대기 및 기체 상태 설정")
atm_pressure = st.sidebar.slider("대기압 (기본 지구=1.0 atm)", 0.0, 100.0, 1.0)
gas_composition = st.sidebar.selectbox(
    "주요 대기 성분 (기체 상태)",
    ["질소-산소계 (N2/O2 - 지구형)", "이산화탄소 온실계 (CO2 - 금성형)", "메탄-수소계 (CH4/H2 - 목성위성/원시행성형)", "대기 희박/없음 (Vacuum)"]
)

# 3. 종합 거주 가능성 판정 로직
st.subheader("🔭 종합 생명체 거주 가능성 판정")

# 온도 요인 판정
temp_status = "normal"
if d_inner <= planet_distance <= d_outer:
    temp_msg = "온도 적절 (Goldilocks Zone)"
elif planet_distance < d_inner:
    temp_msg = "너무 뜨거움 (Too Hot)"
    temp_status = "hot"
else:
    temp_msg = "너무 차가움 (Too Cold)"
    temp_status = "cold"

# 대기 및 중력 가중치 부여
gravity_ok = (0.3 <= gravity <= 3.0)  # 너무 강하거나 약하면 생명체 거주 어려움
pressure_ok = (0.2 <= atm_pressure <= 5.0) # 너무 높거나 낮으면 압사 또는 증발

# 최종 판정
is_habitable = False
if temp_status == "normal" and gravity_ok and pressure_ok and gas_composition != "대기 희박/없음 (Vacuum)":
    is_habitable = True
    st.success(f"🎉 **최상급 거주 가능 행성 (Habitable Planet)!**\n- 거리: {temp_msg}\n- 표면 중력: {gravity:.2f} G (적절)\n- 대기압: {atm_pressure} atm 및 대기 성분이 안정적입니다.")
else:
    st.warning(f"⚠️ **극한 환경 행성 (Extreme Environment)**\n- 거리 상태: {temp_msg}\n- 표면 중력: {gravity:.2f} G ({'적절' if gravity_ok else '주의: 중력이 너무 강하거나 약함'})\n- 대기압/기체: {atm_pressure} atm ({gas_composition}) -> 생명체가 살아가기에 까다로운 환경입니다.")

# 물리 지표 요약 박스
col1, col2, col3 = st.columns(3)
col1.metric("표면 중력", f"{gravity:.2f} G", "지구 대비")
col2.metric("대기압", f"{atm_pressure} atm", gas_composition.split()[0])
col3.metric("거주 가능 영역", f"{d_inner:.2f} ~ {d_outer:.2f} AU")

# 4. 시각화 그래프 (Plotly)
fig = px.scatter(x=[planet_distance], y=[0], text=[f"내 행성 (중력 {gravity:.1f}G)"], title=f"[{selected_star}] 주변 골디락스 존과 행성 위치")
fig.add_vrect(x0=d_inner, x1=d_outer, fillcolor="green", opacity=0.2, line_width=0, annotation_text="Goldilocks Zone")
fig.update_xaxes(title="거리 (AU)")
fig.update_yaxes(visible=False)
st.plotly_chart(fig)

# 5. 물리 환경 연동 맞춤형 외계 생물 생성기
st.markdown("---")
st.subheader("👽 물리 환경 맞춤형 가상 외계 생물 도감")
st.write("설정하신 **중력, 대기압, 기체 성분**에 따라 진화한 맞춤형 생명체 프로필이 생성됩니다.")

if st.button("맞춤형 외계 생물 소환하기!"):
    # 중력에 따른 신체 특징 결정
    if gravity > 2.0:
        body_shape = "낮고 납작하며, 바닥에 밀착된 거대한 다리 다수 보유 (고중력 적응형)"
    elif gravity < 0.5:
        body_shape = "키가 매우 크고 홀쭉하며, 가벼운 뼈와 부유 기관 보유 (저중력 적응형)"
    else:
        body_shape = "균형 잡힌 사지와 안정적인 골격 구조"

    # 대기 및 기체에 따른 호흡/피부 특징 결정
    if "이산화탄소" in gas_composition:
        respiration = "CO2 필터링형 다중 폐 및 두꺼운 산성 보호 외골격"
    elif "메탄" in gas_composition:
        respiration = "메탄 화학반응 에너지 흡수 기관 및 암흑 속 적외선 감지 눈"
    elif "대기 희박" in gas_composition:
        respiration = "외부 충격과 방사선에 버티는 단단한 진공 밀폐형 방어막"
    else:
        respiration = "산소-질소 기반 고효율 허파와 유연한 피부 호흡"

    eyes = random.choice([2, 4, 6, 8, 10])
    
    if is_habitable:
        st.balloons()
        st.success(f"✨ **[안정형 고등 생명체 발견]**\n- **눈 개수:** {eyes}개\n- **신체 형태:** {body_shape}\n- **호흡 및 대사:** {respiration}\n- **설명:** 완벽한 골디락스 존과 적절한 중력 덕분에 지능을 가진 문명 단계로 진화했습니다!")
    else:
        st.warning(f"⚠️ **[극한 환경 특수 생명체 발견]**\n- **눈 개수:** {eyes}개\n- **신체 형태:** {body_shape}\n- **호흡 및 대사:** {respiration}\n- **설명:** 가혹한 중력과 대기 압력을 견디기 위해 신체 구조가 특이하게 진화한 생물입니다.")
