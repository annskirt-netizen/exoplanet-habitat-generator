import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random

# 웹페이지 설정
st.set_page_config(page_title="3D 외계 행성 및 골디락스 존 시뮬레이터", layout="wide")

st.title("🌌 3D 외계 행성 및 골디락스 존 물리 시뮬레이터")
st.write("항성과 행성의 3차원 공간 배치, 얇은 궤도 선, 그리고 사용자가 직접 조절하는 중력 및 물리 환경을 시뮬레이션합니다.")

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

# 2. 사이드바: 환경 설정
st.sidebar.header("⚙️ 1단계: 항성(별) 선택")
selected_star = st.sidebar.selectbox("분석할 천체 선택", df["Star_Name"])

star_row = df[df["Star_Name"] == selected_star].iloc[0]
L = float(star_row["Luminosity"])
desc = star_row["Description"]

st.info(f"📌 **선택된 천체 정보:** {desc}")

# 골디락스 존 계산
d_inner = (L / 1.1) ** 0.5
d_outer = (L / 0.53) ** 0.5

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 2단계: 행성 물리 환경 설정")
planet_distance = st.sidebar.slider("공전궤도 반지름 (AU)", 0.001, float(max(d_outer * 1.5, 5.0)), 1.0)

# ⭐ 사용자가 중력을 직접 입력할 수 있는 슬라이더 추가!
user_gravity = st.sidebar.slider("행성 표면 중력 직접 입력 (G, 지구=1.0)", 0.05, 10.0, 1.0)

atm_pressure = st.sidebar.slider("대기압 (지구=1.0 atm)", 0.0, 100.0, 1.0)
gas_composition = st.sidebar.selectbox(
    "주요 대기 성분 (기체 상태)",
    ["질소-산소계 (N2/O2 - 지구형)", "이산화탄소 온실계 (CO2 - 금성형)", "메탄-수소계 (CH4/H2 - 원시형)", "대기 희박/없음 (Vacuum)"]
)

# 3. 거주 가능성 판정
st.subheader("🔭 종합 생명체 거주 가능성 판정")

temp_status = "normal"
if d_inner <= planet_distance <= d_outer:
    temp_msg = "온도 적절 (Goldilocks Zone)"
elif planet_distance < d_inner:
    temp_msg = "너무 뜨거움 (Too Hot)"
    temp_status = "hot"
else:
    temp_msg = "너무 차가움 (Too Cold)"
    temp_status = "cold"

gravity_ok = (0.3 <= user_gravity <= 3.0)
pressure_ok = (0.2 <= atm_pressure <= 5.0)

is_habitable = False
if temp_status == "normal" and gravity_ok and pressure_ok and gas_composition != "대기 희박/없음 (Vacuum)":
    is_habitable = True
    st.success(f"🎉 **최상급 거주 가능 행성!**\n- 온도: {temp_msg}\n- 사용자 입력 중력: {user_gravity} G (적절)\n- 대기 상태 안정적")
else:
    st.warning(f"⚠️ **극한 환경 행성**\n- 온도: {temp_msg}\n- 중력: {user_gravity} G ({'적절' if gravity_ok else '주의: 생명체가 살기엔 너무 강하거나 약한 중력'})\n- 대기압/기체: {atm_pressure} atm ({gas_composition})")

# 요약 지표
col1, col2, col3 = st.columns(3)
col1.metric("입력된 표면 중력", f"{user_gravity} G", "사용자 설정")
col2.metric("대기압", f"{atm_pressure} atm", gas_composition.split()[0])
col3.metric("거주 가능 영역", f"{d_inner:.2f} ~ {d_outer:.2f} AU")

# 4. 3차원(3D) 시각화 구현 (Plotly 3D Scatter & Orbit Lines)
st.markdown("---")
st.subheader("🌐 항성과 행성의 3차원(3D) 공간 시뮬레이션")
st.write("마우스로 3D 그래프를 회전시키거나 확대/축소하여 항성과 행성의 입체적인 위치를 확인할 수 있습니다.")

fig = go.Figure()

# 중앙의 항성 (노란색/오렌지색 대형 구체)
fig.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[0],
    mode='markers+text',
    marker=dict(size=20, color='orange', symbol='circle'),
    text=[selected_star],
    textposition="top center",
    name="항성 (Star)"
))

# 궤도를 나타내는 얇은 원형 선 (Thin Orbit Line)
import numpy as np
theta = np.linspace(0, 2 * np.pi, 100)
orbit_x = planet_distance * np.cos(theta)
orbit_y = planet_distance * np.sin(theta)
orbit_z = np.zeros_like(theta)

fig.add_trace(go.Scatter3d(
    x=orbit_x, y=orbit_y, z=orbit_z,
    mode='lines',
    line=dict(color='rgba(0, 255, 255, 0.4)', width=2),  # 얇고 부드러운 청록색 궤도 선
    name="행성 공전 궤도"
))

# 골디락스 존 안쪽/바깥쪽 경계 궤도선 표시 (시각적 입체감)
inner_x = d_inner * np.cos(theta)
inner_y = d_inner * np.sin(theta)
fig.add_trace(go.Scatter3d(
    x=inner_x, y=inner_y, z=np.zeros_like(theta),
    mode='lines',
    line=dict(color='rgba(0, 255, 0, 0.2)', width=1, dash='dash'),
    name="골디락스 존 안쪽 경계"
))

outer_x = d_outer * np.cos(theta)
outer_y = d_outer * np.sin(theta)
fig.add_trace(go.Scatter3d(
    x=outer_x, y=outer_y, z=np.zeros_like(theta),
    mode='lines',
    line=dict(color='rgba(0, 255, 0, 0.2)', width=1, dash='dash'),
    name="골디락스 존 바깥쪽 경계"
))

# 행성 위치 (푸른색 또는 붉은색 구체)
planet_color = 'dodgerblue' if is_habitable else 'indianred'
fig.add_trace(go.Scatter3d(
    x=[planet_distance], y=[0], z=[0],
    mode='markers+text',
    marker=dict(size=8, color=planet_color, symbol='circle'),
    text=[f"내 행성 (중력 {user_gravity}G)"],
    textposition="bottom center",
    name="가상 행성 (Planet)"
))

# 3D 레이아웃 디자인 정돈
fig.update_layout(
    scene=dict(
        xaxis_title='X 거리 (AU)',
        yaxis_title='Y 거리 (AU)',
        zaxis_title='Z 거리 (AU)',
        bgcolor='rgba(10, 10, 25, 1)' # 우주 느낌의 어두운 배경
    ),
    margin=dict(l=0, r=0, b=0, t=30),
    legend=dict(x=0, y=0.9)
)

st.plotly_chart(fig, use_container_width=True)

# 5. 맞춤형 외계 생물 생성기
st.markdown("---")
st.subheader("👽 중력 및 물리 환경 맞춤형 가상 외계 생물 도감")

if st.button("맞춤형 외계 생물 소환하기!"):
    if user_gravity > 2.0:
        body_shape = f"낮고 납작한 거대한 골격 (입력된 고중력 {user_gravity}G를 버티기 위해 지면과 밀착됨)"
    elif user_gravity < 0.5:
        body_shape = f"키가 크고 유연한 홀쭉한 형태 (입력된 저중력 {user_gravity}G 환경에 최적화됨)"
    else:
        body_shape = f"안정적인 사지와 균형 잡힌 구조 (입력된 표준 중력 {user_gravity}G 적응형)"

    if "이산화탄소" in gas_composition:
        respiration = "CO2 정화 다중 호흡 기관 및 산성 방어 외골격"
    elif "메탄" in gas_composition:
        respiration = "메탄 기반 화학 대사 기관 및 어둠 적응 눈"
    elif "대기 희박" in gas_composition:
        respiration = "방사선과 진공을 견디는 단단한 보호막"
    else:
        respiration = "산소-질소 기반 고효율 허파 호흡"

    eyes = random.choice([2, 4, 6, 8])
    
    if is_habitable:
        st.balloons()
        st.success(f"✨ **[거주 가능 행성 생명체]**\n- **눈 개수:** {eyes}개\n- **신체 형태:** {body_shape}\n- **호흡 방식:** {respiration}\n- **설명:** 골디락스 존과 사용자가 설정한 중력/대기 조건이 조화를 이루어 고등 생명체로 진화했습니다!")
    else:
        st.warning(f"⚠️ **[극한 환경 생물]**\n- **눈 개수:** {eyes}개\n- **신체 형태:** {body_shape}\n- **호흡 방식:** {respiration}\n- **설명:** 혹독한 물리 환경 속에서 독특하게 진화한 생물입니다.")
