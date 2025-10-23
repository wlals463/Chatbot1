# app.py
# Streamlit Earned Income Tax Credit (근로장려금) Calculator – 2025
# 모드 1: 선형 근사(기본값), 모드 2: 산정표 CSV 업로드
# 실행: streamlit run app.py

import io
import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="2025 근로장려금 계산기", page_icon="🧮", layout="centered")

st.title("🧮 2025 근로장려금 계산기")
st.caption("비공식 참고용 • 국세청 고시/산정표 공개 시 CSV 업로드로 정확 계산 가능")

with st.expander("ℹ️ 사용 전 알아두기", expanded=False):
    st.markdown(
        """
        - **기본 모드(선형 근사)**는 가구유형별 최대지급액·총소득 상한을 바탕으로 *상승→최대→감액* 구간을 **선형 근사**합니다.  
        - **산정표 업로드 모드**는 나중에 확보되는 공식 산정표(총급여액 등 ↔ 지급액 표)를 CSV로 올려서 그 표를 그대로 조회합니다.  
        - 총소득/총급여액 등, 재산요건, 감액(재산 1.4~2.4억 구간 50% 감액 등)과 같은 추가 규정은 실제 지급액에 영향을 줄 수 있으니, **홈택스 계산기**와 함께 교차확인하세요.
        """
    )

# ------------------------------
# 1) 기본 파라미터(2025 적용 가정/최근 기준)
# ------------------------------
# - 최대지급액: 단독 1,650,000 / 홑벌이 2,850,000 / 맞벌이 3,300,000 (원)
# - 총소득 상한(미만): 단독 22,000,000 / 홑벌이 32,000,000 / 맞벌이 44,000,000 (원)
# - 선형 근사용 구간은 보수적으로 설정(필요시 우측 사이드바에서 조정 가능)
DEFAULT_PARAMS = {
    "단독":   {"max": 1_650_000, "upper_income": 22_000_000, "phase_in_start": 4_000_000,  "peak_start": 9_000_000},
    "홑벌이": {"max": 2_850_000, "upper_income": 32_000_000, "phase_in_start": 7_000_000,  "peak_start": 14_000_000},
    "맞벌이": {"max": 3_300_000, "upper_income": 44_000_000, "phase_in_start": 8_000_000,  "peak_start": 17_000_000},
}
# phase_out_end는 총소득 상한(upper_income)과 동일하게 보고 peak_end는 (peak_start + (upper - peak_start)*0.35)처럼
# 임의 비율로 설정할 수도 있지만, 우측 사이드에서 직접 조정 가능하도록 둡니다.
for k, v in DEFAULT_PARAMS.items():
    v["peak_end"] = int(v["peak_start"] + (v["upper_income"] - v["peak_start"]) * 0.35)

# ------------------------------
# 사이드바: 모드 선택 & 파라미터 튜닝
# ------------------------------
st.sidebar.header("⚙️ 계산 모드 / 파라미터")
mode = st.sidebar.radio(
    "계산 모드",
    ["선형 근사(기본)", "산정표 CSV 업로드"],
    index=0,
    help="공식 산정표가 있을 때는 CSV 업로드 모드를 사용하세요."
)

# 파라미터 조정 옵션 (관리자/테스터용)
with st.sidebar.expander("세부 파라미터(선형 근사) 조정", expanded=False):
    edit_type = st.selectbox("가구유형 선택(조정용)", options=list(DEFAULT_PARAMS.keys()))
    p = DEFAULT_PARAMS[edit_type]
    p["max"] = st.number_input("최대 지급액(원)", value=int(p["max"]), step=50_000)
    p["upper_income"] = st.number_input("총소득 상한(원, 미만)", value=int(p["upper_income"]), step=500_000)
    p["phase_in_start"] = st.number_input("상승구간 시작 소득(원)", value=int(p["phase_in_start"]), step=500_000)
    p["peak_start"] = st.number_input("최대구간 시작 소득(원)", value=int(p["peak_start"]), step=500_000)
    p["peak_end"] = st.number_input("최대구간 종료 소득(원)", value=int(p["peak_end"]), step=500_000)

# ------------------------------
# 입력창
# ------------------------------
col1, col2 = st.columns(2)
with col1:
    hh_type = st.selectbox("가구유형", options=["단독", "홑벌이", "맞벌이"])
with col2:
    income = st.number_input("연간 총소득(원)", value=10_000_000, step=100_000, min_value=0)

st.divider()

# ------------------------------
# 모드 2: CSV 업로드(산정표)
# ------------------------------
uploaded_df = None
if mode == "산정표 CSV 업로드":
    st.subheader("📄 산정표 CSV 업로드")
    st.markdown(
        """
        **CSV 포맷 예시**  
        - 컬럼: `household_type,income,amount`  
        - 예)  
          ```
          household_type,income,amount
          단독,0,0
          단독,4000000,100000
          단독,9000000,1650000
          단독,22000000,0
          ...
          맞벌이,8000000,120000
          맞벌이,17000000,3300000
          맞벌이,44000000,0
          ```
        - 동일 가구유형에 대해 **income(원)** 오름차순 행들이 있어야 하며, 앱은 해당 가구유형의 **선형보간**으로 계산합니다.
        """
    )
    file = st.file_uploader("CSV 파일 업로드", type=["csv"])
    if file:
        try:
            df = pd.read_csv(file)
            required_cols = {"household_type", "income", "amount"}
            if not required_cols.issubset(set(df.columns)):
                st.error("CSV 컬럼 명이 올바르지 않습니다. 필요한 컬럼: household_type, income, amount")
            else:
                uploaded_df = df.copy()
                st.success("산정표를 불러왔습니다.")
                st.dataframe(uploaded_df.head(20))
        except Exception as e:
            st.error(f"CSV 읽기 오류: {e}")

# ------------------------------
# 계산 로직
# ------------------------------
def calc_linear_amount(income: int, params: dict) -> int:
    """선형 근사: 상승구간 → 최대구간 → 감액구간"""
    max_amt = params["max"]
    s = params["phase_in_start"]
    peak_start = params["peak_start"]
    peak_end = params["peak_end"]
    upper = params["upper_income"]

    if income < s:
        return 0
    # 상승구간
    if s <= income < peak_start:
        span = peak_start - s
        return int(max_amt * (income - s) / span) if span > 0 else 0
    # 최대구간(plateau)
    if peak_start <= income <= peak_end:
        return int(max_amt)
    # 감액구간
    if peak_end < income < upper:
        span = upper - peak_end
        return max(0, int(max_amt * (upper - income) / span)) if span > 0 else 0
    # 상한 이상
    return 0

def calc_from_table(income: int, hh_type: str, table: pd.DataFrame) -> int:
    """업로드된 산정표로 계산 (가구유형별 선형 보간)"""
    sub = table.query("household_type == @hh_type").copy()
    if sub.empty:
        return 0
    sub = sub.sort_values("income")
    xs = sub["income"].to_list()
    ys = sub["amount"].to_list()
    if income <= xs[0]:
        return int(ys[0])
    if income >= xs[-1]:
        return int(ys[-1])
    # 구간 탐색 후 선형보간
    for i in range(1, len(xs)):
        if xs[i-1] <= income <= xs[i]:
            x0, x1 = xs[i-1], xs[i]
            y0, y1 = ys[i-1], ys[i]
            if x1 == x0:
                return int(y0)
            t = (income - x0) / (x1 - x0)
            return int(y0 + t * (y1 - y0))
    return 0

# 실제 계산
if mode == "산정표 CSV 업로드" and isinstance(uploaded_df, pd.DataFrame):
    amount = calc_from_table(income, hh_type, uploaded_df)
else:
    amount = calc_linear_amount(income, DEFAULT_PARAMS[hh_type])

# ------------------------------
# 결과 표시
# ------------------------------
st.subheader("결과")
st.metric(label="예상 근로장려금 지급액", value=f"{amount:,.0f} 원")

with st.expander("📌 계산 가정(요약)"):
    p = DEFAULT_PARAMS[hh_type]
    st.write(
        {
            "가구유형": hh_type,
            "최대지급액(원)": p["max"],
            "총소득 상한(원, 미만)": p["upper_income"],
            "상승구간 시작(원)": p["phase_in_start"],
            "최대구간 시작(원)": p["peak_start"],
            "최대구간 종료(원)": p["peak_end"],
        }
    )

st.divider()
st.markdown(
    """
    ### 참고/출처
    - 국세청 자주묻는질문(’25.5월 정기신청) – 총소득 기준: 단독 2,200만 / 홑벌이 3,200만 / 맞벌이 4,400만 **미만** :contentReference[oaicite:2]{index=2}  
    - 근로장려금 제도 안내(가구유형 정의·소득 개념 등) :contentReference[oaicite:3]{index=3}  
    """
)
