import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import glob
import os

# 페이지 레이아웃 설정
st.set_page_config(page_title="우리은하 외계행성계 시뮬레이터", layout="wide")

# 1. NASA 데이터 로드 (다운받은 NASA CSV 파일 자동 인식 및 표준 컬럼 매핑)
@st.cache_data
def load_nasa_data():
    csv_files = [f for f in glob.glob("*.csv*") if "requirements" not in f.lower()]
    target_file = None
    for f in csv_files:
        if f.startswith("PS_") or "exoplanet" in f.lower():
            target_file = f
            break
    if not target_file and csv_files:
        target_file = csv_files[0]

    if target_file and os.path.exists(target_file):
        try:
            raw_df = pd.read_csv(target_file, comment='#', low_memory=False)
            if 'hostname' in raw_df.columns:
                stars_df = raw_df.groupby('hostname', as_index=False).first()
                df = pd.DataFrame()
                df["Star_Name"] = stars_df["hostname"]
                if "st_lum" in stars_df.columns:
                    df["Luminosity"] = stars_df["st_lum"].apply(
                        lambda x: round(10 ** float(x), 6) if pd.notnull(x) else 1.0
                    )
                else:
                    df["Luminosity"] = 1.0
                df["Mass"] = stars_df["st_mass"].fillna(1.0) if "st_mass" in stars_df.columns else 1.0
                df["Spectral_Type"] = stars_df["st_spectype"].fillna("Unknown") if "st_spectype" in stars_df.columns else "Unknown"
                disc_method = stars_df["discoverymethod"].fillna("Unknown") if "discoverymethod" in stars_df.columns else "Unknown"
                sy_pnum = stars_df["sy_pnum"].fillna(1).astype(int) if "sy_pnum" in stars_df.columns else 1
                df["Description"] = "확인된 행성 수: " + sy_pnum.astype(str) + "개 | 주요 관측법: " + disc_method.astype(str)
                return df, raw_df, target_file
            else:
                return raw_df, None, target_file
        except Exception as e:
            st.error(f"데이터 파일({target_file}) 로드 중 오류 발생: {e}")

    data = {
        "Star_Name": ["Sun (태양계)", "TRAPPIST-1", "Proxima Centauri"],
        "Luminosity": [1.0, 0.00052, 0.0017],
        "Mass": [1.0, 0.09, 0.12],
        "Spectral_Type": ["G2V", "M8V", "M5.5V"],
        "Description": ["태양계", "트라피스트-1", "프록시마"]
    }
    return pd.DataFrame(data), None, "내장 기본 데이터"

df, raw_planets_df, loaded_filename = load_nasa_data()

st.sidebar.title("🌌 우주 탐사 메뉴")
st.sidebar.caption(f"📂 로드된 데이터: `{loaded_filename}`")
page = st.sidebar.radio("이동할 페이지 선택", ["1. 별 선택 & 우리은하 별 도감", "2. 타원궤도 시뮬레이터 & 생물학 분석"])

if "selected_star_name" not in st.session_state or st.session_state["selected_star_name"] not in df["Star_Name"].values:
    st.session_state["selected_star_name"] = df["Star_Name"].iloc[0]

if page == "1. 별 선택 & 우리은하 별 도감":
    st.title("⭐ 1단계: 탐사할 항성(별) 선택")
    st.write(f"NASA 실제 데이터(`{loaded_filename}`) 기반 총 **{len(df):,}개**의 항성이 로드되었습니다. 원하는 별을 선택한 후 2단계 시뮬레이터로 이동하세요.")

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_star = st.selectbox(
            "탐사할 항성을 선택하세요 (검색 가능)",
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

        if raw_planets_df is not None and 'hostname' in raw_planets_df.columns:
            star_planets = raw_planets_df[raw_planets_df['hostname'] == selected_star].drop_duplicates(subset=['pl_name'])
            if not star_planets.empty:
                st.markdown("**🪐 이 항성을 공전하는 실제 발견된 외계행성:**")
                cols_to_show = [c for c in ['pl_name', 'pl_orbsmax', 'pl_orbeccen', 'pl_rade', 'pl_bmasse', 'pl_eqt'] if c in star_planets.columns]
                st.dataframe(star_planets[cols_to_show], use_container_width=True)

    st.markdown("---")
    st.subheader("📋 전체 등록된 NASA 항성 데이터베이스")
    st.dataframe(df, use_container_width=True)

else:
    selected_star = st.session_state["selected_star_name"]
    star_row = df[df["Star_Name"] == selected_star].iloc[0]
    L = max(float(star_row["Luminosity"]), 1e-6)

    st.title(f"🔭 {selected_star} 시스템 - 타원궤도 & 생물학 정밀 시뮬레이터")

    d_inner = (L / 1.1) ** 0.5
    d_outer = (L / 0.53) ** 0.5

    default_a = float(np.clip((d_inner + d_outer) / 2, 0.001, 10.0))
    default_e = 0.1
    default_rad = 1.0
    default_mass = 1.0

    if raw_planets_df is not None and 'hostname' in raw_planets_df.columns:
        star_planets = raw_planets_df[raw_planets_df['hostname'] == selected_star].drop_duplicates(subset=['pl_name'])
        if not star_planets.empty:
            st.sidebar.markdown("---")
            st.sidebar.subheader("🪐 NASA 실측 행성 프리셋")
            planet_options = ["직접 커스텀 설정"] + star_planets['pl_name'].dropna().tolist()
            selected_preset = st.sidebar.selectbox("실측 행성 데이터 불러오기", planet_options)
            
            if selected_preset != "직접 커스텀 설정":
                p_row = star_planets[star_planets['pl_name'] == selected_preset].iloc[0]
                if 'pl_orbsmax' in p_row and pd.notnull(p_row['pl_orbsmax']):
                    default_a = float(p_row['pl_orbsmax'])
                if 'pl_orbeccen' in p_row and pd.notnull(p_row['pl_orbeccen']):
                    default_e = float(np.clip(p_row['pl_orbeccen'], 0.0, 0.8))
                if 'pl_rade' in p_row and pd.notnull(p_row['pl_rade']):
                    default_rad = float(np.clip(p_row['pl_rade'], 0.5, 15.0))
                if 'pl_bmasse' in p_row and pd.notnull(p_row['pl_bmasse']):
                    default_mass = float(np.clip(p_row['pl_bmasse'], 0.1, 300.0))

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ 행성 물리 변수")
    
    eccentricity = st.sidebar.slider("궤도 이심률 e (0=원, 0.8=납작한 타원)", 0.0, 0.8, default_e, 0.01)
    max_a = float(max(d_outer * 1.5, default_a * 1.5, 5.0))
    a = st.sidebar.slider("궤도 장반경 a (AU)", 0.001, max_a, float(np.clip(default_a, 0.001, max_a)))
    
    gravity_mode = st.sidebar.radio("중력 설정 방식", ["직접 입력 / 슬라이더", "자동 계산 (질량/반지름)"])
    if gravity_mode == "직접 입력 / 슬라이더":
        calc_g = float(np.clip(default_mass / (default_rad ** 2), 0.05, 20.0))
        col_g1, col_g2 = st.sidebar.columns([2, 1])
        with col_g1:
            gravity_slider = st.slider("표면 중력 드래그 (G)", 0.05, 20.0, calc_g, 0.05)
        with col_g2:
            gravity = st.number_input("직접 입력", min_value=0.05, max_value=50.0, value=gravity_slider, step=0.1)
        planet_radius = st.sidebar.slider("행성 반지름 (지구=1.0)", 0.5, 15.0, float(np.clip(default_rad, 0.5, 15.0)))
    else:
        planet_mass = st.sidebar.slider("행성 질량 (지구=1.0)", 0.1, 300.0, float(np.clip(default_mass, 0.1, 300.0)))
        planet_radius = st.sidebar.slider("행성 반지름 (지구=1.0)", 0.5, 15.0, float(np.clip(default_rad, 0.5, 15.0)))
        gravity = planet_mass / (planet_radius ** 2)

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ 대기 조건")
    col_p1, col_p2 = st.sidebar.columns([2, 1])
    with col_p1:
        atm_slider = st.slider("대기압 드래그 (atm)", 0.0, 100.0, 1.0, 0.1)
    with col_p2:
        atm_pressure = st.number_input("직접 입력", min_value=0.0, max_value=1000.0, value=atm_slider, step=0.5)

    gas_composition = st.sidebar.selectbox("주요 대기 성분", ["질소-산소계 (N2/O2)", "이산화탄소 온실계 (CO2)", "메탄-수소계 (CH4/H2)", "수소-헬륨 가스계 (H2/He)", "대기 희박/없음 (Vacuum)"])

    r_min = a * (1 - eccentricity)
    r_max = a * (1 + eccentricity)

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

    st.subheader("📌 종합 분석 결과")
    if is_habitable and gravity_ok and pressure_ok and gas_composition != "대기 희박/없음 (Vacuum)":
        st.success(f"🎉 **최상급 거주 가능 행성!**\n- 궤도 특성: {orbit_status}\n- 표면 중력: {gravity:.2f} G | 대기압: {atm_pressure} atm")
    else:
        st.warning(f"⚠️ **특수/극한 환경 행성**\n- 궤도 특성: {orbit_status}\n- 표면 중력: {gravity:.2f} G | 대기압: {atm_pressure} atm")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("근일점 (가장 가까운 거리)", f"{r_min:.3f} AU")
    col2.metric("원일점 (가장 먼 거리)", f"{r_max:.3f} AU")
    col3.metric("표면 중력", f"{gravity:.2f} G")
    col4.metric("궤도 이심률 (e)", f"{eccentricity:.2f}")

    st.markdown("---")
    st.subheader("🌌 3D 타원 궤도 파노라마 시각화")

    theta = np.linspace(0, 2 * np.pi, 200)
    r_orbit = a * (1 - eccentricity**2) / (1 + eccentricity * np.cos(theta))
    x_orbit = r_orbit * np.cos(theta)
    y_orbit = r_orbit * np.sin(theta)
    z_orbit = np.zeros_like(theta)

    x_in = d_inner * np.cos(theta)
    y_in = d_inner * np.sin(theta)
    x_out = d_outer * np.cos(theta)
    y_out = d_outer * np.sin(theta)

    p_x = x_orbit[0]
    p_y = y_orbit[0]

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers+text',
        marker=dict(size=22, color='gold', symbol='circle'),
        name=f"항성: {selected_star}",
        text=[selected_star], textposition="top center"
    ))

    fig.add_trace(go.Scatter3d(
        x=x_in, y=y_in, z=z_orbit, mode='lines',
        line=dict(color='lightgreen', width=2, dash='dot'), name='Goldilocks 안쪽'
    ))
    fig.add_trace(go.Scatter3d(
        x=x_out, y=y_out, z=z_orbit, mode='lines',
        line=dict(color='darkgreen', width=2, dash='dot'), name='Goldilocks 바깥쪽'
    ))

    fig.add_trace(go.Scatter3d(
        x=x_orbit, y=y_orbit, z=z_orbit, mode='lines',
        line=dict(color='cyan', width=3), name=f'타원 궤도 (e={eccentricity})'
    ))

    marker_size = float(np.clip(8 * (planet_radius ** 0.5), 6, 25))
    fig.add_trace(go.Scatter3d(
        x=[p_x], y=[p_y], z=[0], mode='markers+text',
        marker=dict(size=marker_size, color='deepskyblue', symbol='circle'),
        name='행성 위치', text=["내 행성"], textposition="top center"
    ))

    fig.update_layout(
        scene=dict(xaxis_title='X (AU)', yaxis_title='Y (AU)', zaxis_title='Z (AU)', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=30), height=550
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🧬 물리·화학적 환경 연동 외계 생명체 생물학 예측")
    
    if st.button("외계 생명체 정밀 프로필 분석하기!"):
        if "이산화탄소" in gas_composition:
            blood_color = "보라색/구리 기반 (헤모시아닌 변형 - 구리 성분 결합)"
            blood_desc = "고농도 CO2 환경에서 산소 및 에너지를 운반하기에 효율적인 구리 중심 수송 단백질"
        elif "메탄" in gas_composition or "수소-헬륨" in gas_composition:
            blood_color = "투명한 탄화수소/암모니아 체액"
            blood_desc = "극저온 또는 고압 가스 환경에서 얼거나 기화하지 않는 지질/탄화수소 기반 순환액"
        elif "대기 희박" in gas_composition:
            blood_color = "결정화된 젤리형 뉴클레오산 체액"
            blood_desc = "진공 및 강한 우주 방사선에 세포가 파괴되지 않도록 보호하는 특수 체액"
        else:
            blood_color = "붉은색 (철 기반 헤모글로빈)"
            blood_desc = "풍부한 산소를 신속하게 사지로 전달하는 철분 결합 순환계"

        if gravity > 2.0 or atm_pressure > 10.0:
            neuron_type = "초고속 초전도성 실리콘 뉴런망"
            neuron_desc = "높은 압력과 중력으로 인한 신체 지연을 극복하기 위해 신호 전달 속도가 전선 수준으로 빠름"
        elif eccentricity > 0.4:
            neuron_type = "휴면기(동면) 제어 이중 신경계"
            neuron_desc = "타원 궤도로 인해 행성이 원일점으로 멀어지는 혹한기 동안 대사를 멈추고 휴면하는 감각 스위치 보유"
        else:
            neuron_type = "시냅스 광화학 신경망"
            neuron_desc = "지구 생물과 유사한 화학 물질 기반 전도 신경망"

        if gravity > 2.5:
            skeleton = "외골격 중장갑 구조 (낮고 넓은 체형, 다리 6~8개)"
        elif gravity < 0.5:
            skeleton = "공기주머니 기반의 극도로 가벼운 유기골격 (부유형 또는 길쭉한 체형)"
        else:
            skeleton = "내부 척추 골격 구조 (균형 잡힌 다족 또는 직립 체형)"

        if is_habitable:
            st.balloons()
        
        st.markdown(f"""
        * **🩸 체액/혈액 특성:** `{blood_color}`
          * *생리학적 원리:* {blood_desc}
        * **🧠 신경계/뉴런 구조:** `{neuron_type}`
          * *생리학적 원리:* {neuron_desc}
        * **🦴 골격 및 외형:** `{skeleton}`
        * **🔄 계절 적응력:** `e={eccentricity}`로 인해 **{'연중 일정한 기후 적응' if eccentricity < 0.2 else '극심한 주기의 동면/기상 반복 생체 리듬'}**을 가짐
        """)
