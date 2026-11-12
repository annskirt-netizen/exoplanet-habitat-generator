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

    gas_composition = st.sidebar.selectbox(
        "주요 대기 성분",
        ["질소-산소계 (N2/O2)", "이산화탄소 온실계 (CO2)", "메탄
