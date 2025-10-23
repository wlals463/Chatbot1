# app.py
# Streamlit 근로장려금 계산기 – 2024년 버전 (시각화 포함)
# 실행: streamlit run app.py

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="2024년 근로장려금 계산기", page_icon="💰", layout="centered")

st.title("💰 2024년 근로장려금 계산기")
st.caption("비공식 참고용 계산기 • 국세청 홈택스 공식 계산 결과와 다를 수 있습니다.")

with st.expander("ℹ️ 계산 기준 안내", expanded=False):
    st.markdown("""
    - 2024년 귀속 근로장려금 기준으로 작성된 간이 계산기입니다.  
    - 가구유형별 최대 지급액과 총소득 상한은 **국세청 공개자료**를 기반으로 합니다.  
    - 재산이 **1억 4천만 원 초과 ~ 2억 4천만 원 이하**이면 **50% 감액**,  
      **2억 4천만 원 초과** 시 **지급 제외(재산기준 초과)** 됩니다.
    """)

# ------------------------------
# 1️⃣ 기준 파라미터 (2024년 귀속)
# ------------------------------
PARAMS = {
    "단독":   {"max": 1_650_000, "upper_income": 22_000_000, "phase_in_start": 4_000_000,  "peak_start": 9_000_000,  "peak_end": 14_000_000},
    "홑벌이": {"max": 2_850_000, "upper_income": 32_000_000, "phase_in_start": 7_000_000,  "peak_start": 14_000_000, "peak_end": 21_000_000},
    "맞벌이": {"max": 3_300_000, "upper_income": 44_000_000, "phase_in_start": 8_000_000,  "peak_start": 17_000_000, "peak_end": 26_000_000},
}

# ------------------------------
# 2️⃣ 사용자 입력
# ------------------------------
col1, col2 = st.columns(2)
with col1:
    hh_type = st.selectbox("가구유형", options=["단독", "홑벌이", "맞벌이"])
with col2:
    income = st.number_input("연간 총소득(원)", value=10_000_000, step=100_000, min_value=0)

property_value = st.number_input("재산가액(원)", value=50_000_000, step=1_000_000, min_value=0)

st.divider()

# ------------------------------
# 3️⃣ 근로장려금 계산 함수
# ------------------------------
def calc_eitc(income: int, params: dict) -> int:
    """소득에 따른 근로장려금 계산 (선형 근사)"""
    max_amt = params["max"]
    s = params["phase_in_start"]
    peak_start = params["peak_start"]
    peak_end = params["peak_end"]
    upper = params["upper_income"]

    if income < s:
        return 0
    if s <= income < peak_start:
        span = peak_start - s
        return int(max_amt * (income - s) / span)
    if peak_start <= income <= peak_end:
        return int(max_amt)
    if peak_end < income < upper:
        span = upper - peak_end
        return int(max_amt * (upper - income) / span)
    return 0

def apply_property_adjustment(amount: int, prop: int) -> tuple[int, str]:
    """재산 기준 감액 또는 제외"""
    if prop <= 140_000_000:
        return amount, "정상 지급"
    elif 140_000_000 < prop <= 240_000_000:
        return int(amount * 0.5), "재산기준 감액(50%)"
    else:
        return 0, "재산기준 초과(미지급)"

# ------------------------------
# 4️⃣ 결과 계산
# ------------------------------
params = PARAMS[hh_type]
base_amount = calc_eitc(income, params)
final_amount, note = apply_property_adjustment(base_amount, property_value)

# ------------------------------
# 5️⃣ 결과 출력
# ------------------------------
st.subheader("📊 계산 결과")
st.metric(label="예상 근로장려금 지급액", value=f"{final_amount:,.0f} 원")
st.write(f"💬 지급유형: **{note}**")

with st.expander("📋 계산 상세"):
    st.write({
        "가구유형": hh_type,
        "총소득": f"{income:,} 원",
        "재산가액": f"{property_value:,} 원",
        "기본 산정액": f"{base_amount:,} 원",
        "최종 지급액": f"{final_amount:,} 원",
        "재산 판정": note,
    })

# ------------------------------
# 6️⃣ 그래프 시각화
# ------------------------------
st.divider()
st.subheader("📈 총소득 대비 지급액 시각화")

incomes = list(range(0, params["upper_income"] + 1, 500_000))
amounts = [calc_eitc(i, params) for i in incomes]
adjusted_amounts = [apply_property_adjustment(a, property_value)[0] for a in amounts]

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(incomes, amounts, label="기본 산정액", linestyle="--", alpha=0.6)
ax.plot(incomes, adjusted_amounts, label="재산 반영 후 지급액", linewidth=2)

ax.set_title(f"{hh_type} 가구 – 총소득 vs 지급액")
ax.set_xlabel("총소득 (원)")
ax.set_ylabel("지급액 (원)")
ax.legend()
ax.grid(True, linestyle=":", alpha=0.5)

st.pyplot(fig)

# ------------------------------
# 7️⃣ 참고
# ------------------------------
st.divider()
st.markdown("""
**참고:**  
- 단독: 총소득 2,200만 원 미만 / 최대 165만 원  
- 홑벌이: 총소득 3,200만 원 미만 / 최대 285만 원  
- 맞벌이: 총소득 4,400만 원 미만 / 최대 330만 원  
- 재산 1.4억~2.4억: 지급액의 50% 감액  
- 재산 2.4억 초과: 지급 제외
""")
