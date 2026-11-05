import streamlit as st
import pandas as pd
import plotly.express as px
import random

# 웹페이지 제목
st.title("🌌 태양계 및 유명 외계행성계 골디락스 존 시뮬레이터")
st.write("유로파, 타이탄이 속한 태양계부터 트라피스트-1 같은 유명 외계행성계까지 생명체 거주 가능성을 분석합니다.")

# 1. 내가 만든 stars.csv 파일 불러오기
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("stars.csv")
    except:
        data = {
            "Star_Name": ["Sun (태양계)", "TRAPPIST-1"],
            "Luminosity": [1.0, 0.00052],
            "Mass": [1.0, 0.09],
            "Description": ["태양계 기본 데이터", "트라피스트-1계"]
        }
        df = pd.DataFrame(data)
    return df

df = load_data()

# 2. 항성/천체 선택 및 변수 조절
st.sidebar.header("⚙️ 시뮬레이션 설정")
selected_star = st.sidebar.selectbox("분석할 천체/항성 선택", df["Star_Name"])

# 선택한 천체의 정보 가져오기
star_row = df[df["Star_Name"] == selected_star].iloc[0]
L = float(star_row["Luminosity"])
desc = star_row["Description"]

# 메인 화면에 천체 설명 띄우기
st.info(f"📌 **선택한 천체 정보:** {desc}")

# 골디락스 존 계산 공식 (하버드 공식 기반)
d_inner = (L / 1.1) ** 0.5
d_outer = (L / 0.53) ** 0.5

st.sidebar.write(f"**광도($L$):** {L} (태양 기준)")
st.sidebar.write(f"**생명체 거주 가능 영역:** {d_inner:.2f} AU ~ {d_outer:.2f} AU")

# 행성 궤도 거리 슬라이더
planet_distance = st.slider("가상 행성(또는 위성)의 공전궤도 반지름 (AU)", 0.001, float(max(d_outer * 1.5, 5.0)), 1.0)

# 3. 판정 결과 화면
st.subheader("🔭 거주 가능성 판정 결과")
if d_inner <= planet_distance <= d_outer:
    st.success(f"🎉 **거주 가능 (Goldilocks Zone)!** 이 거리에 위치한 천체는 액체 상태의 물이 존재할 수 있습니다.")
    is_habitable = True
elif planet_distance < d_inner:
    st.error(f"🔥 **너무 뜨거움 (Too Hot)!** 항성과 너무 가까워 표면의 물이 모두 증발합니다.")
    is_habitable = False
else:
    st.error(f"❄️ **너무 차가움 (Too Cold)!** 항성과 너무 멀어 표면의 물이 꽁꽁 얼어붙습니다. (※ 단, 유로파처럼 조석 가열로 내부 바다가 존재할 수도 있어요!)")
    is_habitable = False

# 4. 시각화 그래프 (Plotly)
fig = px.scatter(x=[planet_distance], y=[0], text=["내 행성"], title=f"[{selected_star}] 주변 골디락스 존과 위치")
fig.add_vrect(x0=d_inner, x1=d_outer, fillcolor="green", opacity=0.2, line_width=0, annotation_text="Goldilocks Zone")
fig.update_xaxes(title="거리 (AU)")
fig.update_yaxes(visible=False)
st.plotly_chart(fig)

# 5. 가상 외계 생물 생성기 (재미 요소)
st.markdown("---")
st.subheader("👽 맞춤형 가상 외계 생물 도감")
if st.button("외계 생물 프로필 소환하기!"):
    eyes = random.choice([2, 4, 6, 8])
    skin_color = random.choice(["초록색 젤리형", "보라색 털복숭이", "은빛 금속성 비늘", "투명한 얼음형"])
    breath = random.choice(["메탄 호흡", "산소 호흡", "규소 기반 에너지 흡수"])
    
    if is_habitable:
        st.balloons()
        st.success(f"✨ **[거주 가능 지역 생명체]**\n- **눈 개수:** {eyes}개\n- **신체 특징:** {skin_color}\n- **호흡 방식:** {breath}\n- **설명:** 온화한 환경 속에서 풍부한 액체 물을 바탕으로 진화한 생명체입니다!")
    else:
        st.warning(f"⚠️ **[극한 환경 탐사 생명체]**\n- **눈 개수:** {eyes}개\n- **신체 특징:** {skin_color} (극한 환경 특화 방어막)\n- **호흡 방식:** {breath}\n- **설명:** 표면은 얼어붙었거나 뜨겁지만, 지하 바다나 특수 환경에서 적응해 살아가는 생물입니다.")
