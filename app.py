import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import random

# 페이지 레이아웃 설정
st.set_page_config(page_title="우리은하 외계행성계 시뮬레이터", layout="wide")

# 1. 데이터 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("stars.csv")
    except:
        data = {
            "Star_Name": ["Sun (태양계)", "TRAPPIST-1", "Proxima Centauri"],
            "Luminosity": [1.0, 0.00052, 0.0017],
            "Mass": [1.0, 0.09, 0.12],
            "Spectral_Type": ["G2V", "M8V", "M5.5V"],
            "Description": ["태양계", "트라피스트-1", "프록시마"]
        }
        df = pd.DataFrame(data)
    return df

df = load_data()

# 2. 왼쪽 상단 메인 네비게이션 (페이지 분리)
st.sidebar.title("🌌 우주 탐사 메뉴")
page = st.sidebar.radio("이동할 페이지 선택", ["1. 별 선택 & 우리은하 별 도감", "2. 타원궤도 시뮬레이터 & 생물학 분석"])

# 세션 상태에 선택한 별 저장 (페이지 이동 간 공유)
if "selected_star_name" not in st.session_state:
    st.session_state["selected_star_name"] = df["Star_Name"].iloc[0]

# ==========================================
# PAGE 1: 별 선택 및 데이터 탐색 페이지
# ==========================================
if page == "1. 별 선택 & 우리은하 별 도감":
    st.title("⭐ 1단계: 탐사할 항성(별) 선택")
    st.write("우리은하 내 분석 가능한 항성 목록입니다. 원하는 별을 먼저 선택한 후 2단계 시뮬레이터 페이지로 이동하세요.")

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_star = st.selectbox(
            "탐사할 항성을 선택하세요",
            df["Star_Name"],
            index=int(df[df["Star_Name"] == st.session_state["selected_star_name"]].index[0])
        )
        st.session_state["selected_star_name"] = selected_star
        st.success(f"✅ 현재 선택된 항성: **{selected_star}**")
        st.info("왼쪽 메뉴에서 '2. 타원궤도 시뮬레이터 & 생물학 분석'으로 이동하세요!")

    with col2:
        star_info = df[df["Star_Name"] == selected_star].iloc[0]
        st.subheader(f"📊 {selected_star} 상세 프로필")
        st.write(f"- **분류/스펙트럼:** {star_info.get('Spectral_Type', 'N/A')}")
        st.write(f"- **광도 (태양=1.0):** {star_info['Luminosity']}")
        st.write(f"- **질량 (태양=1.0):** {star_info['Mass']}")
        st.write(f"- **특징:** {star_info['Description']}")

    st.markdown("---")
    st.subheader("📋 전체 등록된 우리은하 항성 데이터베이스")
    st.dataframe(df, use_container_width=True)

# ==========================================
# PAGE 2: 시뮬레이션 및 생물학 예측 페이지
# ==========================================
else:
    selected_star = st.session_state["selected_star_name"]
    star_row = df[df["Star_Name"] == selected_star].iloc[0]
    L = float(star_row["Luminosity"])

    st.title(f"🔭 {selected_star} 시스템 - 타원궤도 & 생물학 정밀 시뮬레이터")

    # 골디락스 존 경계 계산 (AU)
    d_inner = (L / 1.1) ** 0.5
    d_outer = (L / 0.53) ** 0.5

    # 사이드바 변수 설정
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ 행성 물리 변수")
    
    # 타원 궤도 핵심 변수: 이심률(Eccentricity) 추가
    eccentricity = st.sidebar.slider("궤도 이심률 e (0=원, 0.8=매우 납작한 타원)", 0.0, 0.8, 0.1, 0.05)
    a = st.sidebar.slider("궤도 장반경 a (AU)", 0.001, float(max(d_outer * 1.5, 5.0)), 1.0)
    
    gravity_mode = st.sidebar.radio("중력 설정 방식", ["자동 계산 (질량/반지름)", "직접 입력"])
    if gravity_mode == "직접 입력":
        gravity = st.sidebar.slider("표면 중력 (지구=1.0G)", 0.05, 10.0, 1.0)
        planet_radius = st.sidebar.slider("행성 반지름 (지구=1.0)", 0.5, 3.0, 1.0)
    else:
        planet_mass = st.sidebar.slider("행성 질량 (지구=1.0)", 0.1, 10.0, 1.0)
        planet_radius = st.sidebar.slider("행성 반지름 (지구=1.0)", 0.5, 3.0, 1.0)
        gravity = planet_mass / (planet_radius ** 2)

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ 대기 조건")
    atm_pressure = st.sidebar.slider("대기압 (atm)", 0.0, 100.0, 1.0)
    gas_composition = st.sidebar.selectbox(
        "주요 대기 성분",
        ["질소-산소계 (N2/O2)", "이산화탄소 온실계 (CO2)", "메탄-수소계 (CH4/H2)", "대기 희박/없음 (Vacuum)"]
    )

    # 타원 궤도 근일점(r_min)과 원일점(r_max) 계산
    r_min = a * (1 - eccentricity)
    r_max = a * (1 + eccentricity)

    # 온도/거리 상태 판정 (타원 궤도로 인한 계절 변화 고려)
    if d_inner <= r_min and r_max <= d_outer:
        orbit_status = "안정적 거주 가능 (연중 골디락스 존 유지)"
        is_habitable = True
    elif r_min <= d_outer and r_max >= d_inner:
        orbit_status = "극심한 계절 변화 (타원 궤도로 인해 일부 기간만 골디락스 존 통과)"
        is_habitable = False
    elif r_max < d_inner:
        orbit_status = "극도로 뜨거움 (항성과 너무 가까움)"
        is_habitable = False
    else:
        orbit_status = "극도로 차가움 (항성과 너무 묾)"
        is_habitable = False

    gravity_ok = (0.3 <= gravity <= 3.0)
    pressure_ok = (0.2 <= atm_pressure <= 5.0)

    # 결과 판정 박스
    st.subheader("📌 종합 분석 결과")
    if is_habitable and gravity_ok and pressure_ok and gas_composition != "대기 희박/없음 (Vacuum)":
        st.success(f"🎉 **최상급 거주 가능 행성!**\n- 궤도 특성: {orbit_status}\n- 표면 중력: {gravity:.2f} G | 대기압: {atm_pressure} atm")
    else:
        st.warning(f"⚠️ **특수/극한 환경 행성**\n- 궤도 특성: {orbit_status}\n- 표면 중력: {gravity:.2f} G | 대기압: {atm_pressure} atm")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("근일점 (가장 가까운 거리)", f"{r_min:.2f} AU")
    col2.metric("원일점 (가장 먼 거리)", f"{r_max:.2f} AU")
    col3.metric("표면 중력", f"{gravity:.2f} G")
    col4.metric("궤도 이심률 (e)", f"{eccentricity:.2f}")

    # 3D 타원 궤도 시각화
    st.markdown("---")
    st.subheader("🌌 3D 타원 궤도 파노라마 시각화")

    theta = np.linspace(0, 2 * np.pi, 200)
    # 극좌표 타원 공식: r = a(1 - e^2) / (1 + e * cos(theta))
    r_orbit = a * (1 - eccentricity**2) / (1 + eccentricity * np.cos(theta))
    x_orbit = r_orbit * np.cos(theta)
    y_orbit = r_orbit * np.sin(theta)
    z_orbit = np.zeros_like(theta)

    # 골디락스 존 (원형 영역 표시)
    x_in = d_inner * np.cos(theta)
    y_in = d_inner * np.sin(theta)
    x_out = d_outer * np.cos(theta)
    y_out = d_outer * np.sin(theta)

    # 행성 위치 (근일점 위치인 theta=0에 배치)
    p_x = x_orbit[0]
    p_y = y_orbit[0]

    fig = go.Figure()

    # 항성 (타원의 초점에 위치해야 하지만 시각적 편의를 위해 원점에 배치)
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers+text',
        marker=dict(size=22, color='gold', symbol='circle'),
        name=f"항성: {selected_star}",
        text=[selected_star], textposition="top center"
    ))

    # 골디락스 영역
    fig.add_trace(go.Scatter3d(
        x=x_in, y=y_in, z=z_orbit, mode='lines',
        line=dict(color='lightgreen', width=2, dash='dot'), name='Goldilocks 안쪽'
    ))
    fig.add_trace(go.Scatter3d(
        x=x_out, y=y_out, z=z_orbit, mode='lines',
        line=dict(color='darkgreen', width=2, dash='dot'), name='Goldilocks 바깥쪽'
    ))

    # 타원 궤도 선
    fig.add_trace(go.Scatter3d(
        x=x_orbit, y=y_orbit, z=z_orbit, mode='lines',
        line=dict(color='cyan', width=2), name=f'타원 궤도 (e={eccentricity})'
    ))

    # 내 행성
    fig.add_trace(go.Scatter3d(
        x=[p_x], y=[p_y], z=[0], mode='markers+text',
        marker=dict(size=10 * planet_radius, color='deepskyblue', symbol='circle'),
        name='행성 위치', text=["내 행성"], textposition="top center"
    ))

    fig.update_layout(
        scene=dict(xaxis_title='X (AU)', yaxis_title='Y (AU)', zaxis_title='Z (AU)', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=30), height=550
    )
    st.plotly_chart(fig, use_container_width=True)

    # 🧬 외계 생명체 정밀 생물학적 특징 예측기
    st.markdown("---")
    st.subheader("🧬 물리·화학적 환경 연동 외계 생명체 생물학 예측")
    
    if st.button("외계 생명체 정밀 프로필 분석하기!"):
        # 1. 혈액/순환계 (기체 및 방사선 기반)
        if "이산화탄소" in gas_composition:
            blood_color = "보라색/구리 기반 (헤모시아닌 변형 - 구리 성분 결합)"
            blood_desc = "고농도 CO2 환경에서 산소 및 에너지를 운반하기에 효율적인 구리 중심 수송 단백질"
        elif "메탄" in gas_composition:
            blood_color = "투명한 탄화수소 체액"
            blood_desc = "극저온 메탄 바다 환경에서 얼지 않는 지질/탄화수소 기반 순환액"
        elif "대기 희박" in gas_composition:
            blood_color = "결정화된 젤리형 뉴클레오산 체액"
            blood_desc = "진공 및 강한 우주 방사선에 세포가 파괴되지 않도록 보호하는 특수 체액"
        else:
            blood_color = "붉은색 (철 기반 헤모글로빈)"
            blood_desc = "풍부한 산소를 신속하게 사지로 전달하는 철분 결합 순환계"

        # 2. 신경계/뉴런 (중력 및 대기압 기반)
        if gravity > 2.0 or atm_pressure > 10.0:
            neuron_type = "초고속 초전도성 실리콘 뉴런망"
            neuron_desc = "높은 압력과 중력으로 인한 신체 지연을 극복하기 위해 신호 전달 속도가 전선 수준으로 빠름"
        elif eccentricity > 0.4:
            neuron_type = "휴면기(동면) 제어 이중 신경계"
            neuron_desc = "타원 궤도로 인해 행성이 원일점으로 멀어지는 혹한기 동안 대사를 멈추고 휴면하는 감각 스위치 보유"
        else:
            neuron_type = "시냅스 광화학 신경망"
            neuron_desc = "지구 생물과 유사한 화학 물질 기반 전도 신경망"

        # 3. 신체 구조 및 골격
        if gravity > 2.5:
            skeleton = "외골격 중장갑 구조 (다리 6~8개)"
        elif gravity < 0.5:
            skeleton = "공기주머니 기반의 극도로 가벼운 유기골격 (부유형)"
        else:
            skeleton = "내부 척추 골격 구조"

        st.balloons() if is_habitable else None
        
        st.markdown(f"""
        * **🩸 체액/혈액 특성:** `{blood_color}`
          * *생리학적 원리:* {blood_desc}
        * **🧠 신경계/뉴런 구조:** `{neuron_type}`
          * *생리학적 원리:* {neuron_desc}
        * **🦴 골격 및 외형:** `{skeleton}`
        * **🔄 계절 적응력:** `이심률 e={eccentricity}`로 인해 **{'연중 일정한 기후 적응' if eccentricity < 0.2 else '극심한 주기의 동면/기상 반복 생체 리듬'}**을 가짐
        """)
