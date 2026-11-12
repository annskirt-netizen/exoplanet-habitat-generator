
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import glob

st.set_page_config(
    page_title="우리은하 외계행성 탐사",
    page_icon="🌌",
    layout="wide"
)

# NASA 데이터 로드
@st.cache_data
def load_data():
    files = glob.glob("*.csv")
    file = next((f for f in files if f.startswith("PS_")), None)

    if file:
        raw = pd.read_csv(file, comment="#", low_memory=False)
        s = raw.groupby("hostname", as_index=False).first()

        def get_col(col, default):
            if col in s.columns:
                return s[col]
            return pd.Series(default, index=s.index)

        df = pd.DataFrame({
            "Star_Name": s["hostname"],
            "Luminosity": 10 ** pd.to_numeric(get_col("st_lum", 0), errors="coerce").fillna(0),
            "Mass": pd.to_numeric(get_col("st_mass", 1), errors="coerce").fillna(1),
            "Spectral_Type": get_col("st_spectype", "Unknown").fillna("Unknown"),
            "RA": pd.to_numeric(get_col("ra", np.nan), errors="coerce"),
            "Dec": pd.to_numeric(get_col("dec", np.nan), errors="coerce"),
            "Distance": pd.to_numeric(get_col("sy_dist", np.nan), errors="coerce"),
            "Description": get_col("sy_pnum", 0).fillna(0).astype(int).astype(str) + "개 행성"
        })
        return df, raw

    df = pd.DataFrame({
        "Star_Name": ["Sun (태양계)", "TRAPPIST-1", "Proxima Centauri"],
        "Luminosity": [1, 0.00052, 0.0017],
        "Mass": [1, 0.09, 0.12],
        "Spectral_Type": ["G2V", "M8V", "M5.5V"],
        "RA": [0, 346, 217],
        "Dec": [0, -5, -62],
        "Distance": [0, 12.5, 1.3],
        "Description": ["태양계", "트라피스트-1", "프록시마"]
    })
    return df, None


df, raw = load_data()

if "star" not in st.session_state:
    st.session_state.star = df.iloc[0]["Star_Name"]

if "page" not in st.session_state:
    st.session_state.page = "별 탐사 지도"


# 별 상세 정보 팝업
@st.dialog("⭐ 항성 상세 정보")
def star_popup(name):
    s = df[df.Star_Name == name].iloc[0]

    st.title("🌟 " + name)
    st.write("스펙트럼:", s.Spectral_Type)
    st.write("광도:", round(s.Luminosity, 6))
    st.write("질량:", round(s.Mass, 3))
    st.write("특징:", s.Description)

    if raw is not None:
        planets = raw[raw.hostname == name].drop_duplicates("pl_name")
        st.subheader("🪐 발견된 외계행성")

        if not planets.empty:
            cols = [c for c in ["pl_name", "pl_orbsmax", "pl_orbeccen", "pl_rade", "pl_bmasse", "pl_eqt"] if c in planets.columns]
            st.dataframe(planets[cols], use_container_width=True)
        else:
            st.info("등록된 행성이 없습니다.")

    if st.button("🚀 이 항성 탐사하기", type="primary", use_container_width=True):
        st.session_state.star = name
        st.session_state.page = "행성 시뮬레이터"
        st.rerun()


# 메뉴
st.sidebar.title("🌌 우주 탐사 메뉴")
page = st.sidebar.radio(
    "페이지 선택",
    ["별 탐사 지도", "행성 시뮬레이터"],
    key="page"
)


# ==================================
# 1. 3D 별 탐사 지도
# ==================================

if page == "별 탐사 지도":

    st.title("🌌 우리은하 3D 항성 탐사")
    st.write("3D 공간에서 별을 선택하고 실제 항성 정보를 확인하세요.")

    stars = df.dropna(subset=["RA", "Dec", "Distance"]).copy()
    stars = stars[stars.Distance > 0]

    if not stars.empty:
        ra = np.radians(stars.RA)
        dec = np.radians(stars.Dec)
        d = stars.Distance * 3.26156

        stars["X"] = d * np.cos(dec) * np.cos(ra)
        stars["Y"] = d * np.cos(dec) * np.sin(ra)
        stars["Z"] = d * np.sin(dec)

        fig = go.Figure(go.Scatter3d(
            x=stars.X,
            y=stars.Y,
            z=stars.Z,
            mode="markers",
            marker=dict(
                size=4,
                color=np.log10(stars.Luminosity.clip(lower=1e-6)),
                colorscale="Plasma",
                opacity=0.85
            ),
            text=stars.Star_Name,
            hovertemplate="<b>%{text}</b><extra></extra>"
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#050914",
            height=620,
            margin=dict(l=0, r=0, t=20, b=0),
            scene=dict(
                xaxis_title="X (광년)",
                yaxis_title="Y (광년)",
                zaxis_title="Z (광년)",
                aspectmode="data",
                bgcolor="#050914"
            )
        )

        event = st.plotly_chart(
            fig,
            use_container_width=True,
            key="star_map",
            on_select="rerun",
            selection_mode="points"
        )

        if event.selection.points:
            idx = event.selection.points[0]["point_index"]
            st.session_state.star = stars.iloc[idx].Star_Name

    else:
        st.warning("3D 좌표 데이터가 없습니다. NASA CSV의 ra, dec, sy_dist 컬럼을 확인하세요.")

    st.divider()
    st.subheader("🔎 항성 검색")

    names = df.Star_Name.tolist()
    selected = st.selectbox(
        "탐사할 항성",
        names,
        index=names.index(st.session_state.star)
    )
    st.session_state.star = selected

    if st.button("⭐ 항성 상세 정보 보기", use_container_width=True):
        star_popup(selected)

    st.divider()
    st.subheader("📚 전체 항성 도감")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ==================================
# 2. 행성 시뮬레이터
# ==================================

else:

    name = st.session_state.star
    star = df[df.Star_Name == name].iloc[0]
    L = max(float(star.Luminosity), 1e-6)

    st.title(f"🔭 {name} 행성 시뮬레이터")

    inner = np.sqrt(L / 1.1)
    outer = np.sqrt(L / 0.53)

    a = st.sidebar.slider("궤도 장반경 (AU)", 0.001, max(5.0, outer * 1.5), float(np.clip((inner + outer) / 2, 0.001, max(5.0, outer * 1.5))))
    e = st.sidebar.slider("궤도 이심률", 0.0, 0.8, 0.1)
    mass = st.sidebar.slider("행성 질량 (지구=1)", 0.1, 300.0, 1.0)
    radius = st.sidebar.slider("행성 반지름 (지구=1)", 0.5, 15.0, 1.0)
    pressure = st.sidebar.slider("대기압 (atm)", 0.0, 100.0, 1.0)

    gas = st.sidebar.selectbox("대기 성분", [
        "질소-산소계 (N2/O2)",
        "이산화탄소 온실계 (CO2)",
        "메탄-수소계 (CH4/H2)",
        "수소-헬륨 가스계 (H2/He)",
        "대기 희박/없음 (Vacuum)"
    ])

    gravity = mass / radius**2
    rmin = a * (1-e)
    rmax = a * (1+e)

    habitable = inner <= rmin and rmax <= outer
    suitable = 0.3 <= gravity <= 3 and 0.2 <= pressure <= 5 and "Vacuum" not in gas

    st.subheader("📊 행성 환경 분석")

    if habitable and suitable:
        st.success("🎉 거주 가능 조건을 충족하는 행성!")
    else:
        st.warning("⚠️ 특수 또는 극한 환경 행성")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("근일점", f"{rmin:.3f} AU")
    c2.metric("원일점", f"{rmax:.3f} AU")
    c3.metric("표면 중력", f"{gravity:.2f} G")
    c4.metric("이심률", f"{e:.2f}")

    # 3D 타원궤도
    theta = np.linspace(0, 2*np.pi, 200)
    r = a*(1-e**2)/(1+e*np.cos(theta))

    fig = go.Figure()

    for radius_zone, color, label in [
        (inner, "lightgreen", "거주 가능 영역 안쪽"),
        (outer, "green", "거주 가능 영역 바깥쪽")
    ]:
        fig.add_trace(go.Scatter3d(
            x=radius_zone*np.cos(theta),
            y=radius_zone*np.sin(theta),
            z=np.zeros(200),
            mode="lines",
            line=dict(color=color, dash="dot"),
            name=label
        ))

    fig.add_trace(go.Scatter3d(
        x=r*np.cos(theta),
        y=r*np.sin(theta),
        z=np.zeros(200),
        mode="lines",
        line=dict(color="cyan", width=5),
        name="행성 궤도"
    ))

    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers",
        marker=dict(size=12, color="gold"),
        name=name
    ))

    fig.update_layout(
        template="plotly_dark",
        height=550,
        scene=dict(aspectmode="data")
    )

    st.plotly_chart(fig, use_container_width=True)

    # 외계 생명체 예측
    st.divider()
    st.subheader("🧬 외계 생명체 생물학 예측")

    if st.button("외계 생명체 분석하기", type="primary"):

        blood = (
            "구리 기반 보라색 체액" if "이산화탄소" in gas else
            "탄화수소 기반 체액" if "메탄" in gas or "수소-헬륨" in gas else
            "결정화된 젤리형 체액" if "Vacuum" in gas else
            "철 기반 붉은 혈액"
        )

        neuron = (
            "고밀도 신경망" if gravity > 2 else
            "휴면기 제어 신경계" if e > 0.4 else
            "화학적 신경망"
        )

        skeleton = (
            "낮고 넓은 외골격" if gravity > 2.5 else
            "가벼운 유기골격" if gravity < 0.5 else
            "내부 골격 구조"
        )

        st.success("생물학 프로필 분석 완료!")
        st.write("🩸 체액:", blood)
        st.write("🧠 신경계:", neuron)
        st.write("🦴 골격:", skeleton)
        st.write("🔄 계절 적응:", "안정적 기후" if e < 0.2 else "주기적 동면 가능성")

        if habitable:
            st.balloons()
