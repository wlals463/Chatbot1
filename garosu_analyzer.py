import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="가공 거래 의심 탐지", layout="wide")

st.title("💰 가공 거래 의심 탐지 시스템")
st.write("은행 거래내역과 세금계산서 내역을 비교하여 가공 의심 거래를 탐지합니다.")

# -------------------------------
# 1️⃣ 파일 업로드
# -------------------------------
bank_file = st.file_uploader("📁 은행 거래내역 엑셀 파일을 업로드하세요", type=["xlsx"])
tax_file = st.file_uploader("📁 세금계산서 엑셀 파일을 업로드하세요", type=["xlsx"])

if bank_file and tax_file:
    # -------------------------------
    # 2️⃣ 데이터 불러오기
    # -------------------------------
    bank_df = pd.read_excel(bank_file)
    tax_df = pd.read_excel(tax_file)

    st.subheader("📄 은행 거래내역 미리보기")
    st.dataframe(bank_df.head())

    st.subheader("📄 세금계산서 내역 미리보기")
    st.dataframe(tax_df.head())

    # 날짜 컬럼 처리
    bank_df["거래연월일"] = pd.to_datetime(bank_df["거래연월일"], errors="coerce")
    tax_df["세금계산서 발급일"] = pd.to_datetime(tax_df["세금계산서 발급일"], errors="coerce")

    # -------------------------------
    # 3️⃣ 비교 로직
    # -------------------------------
    results = []

    for _, bank_row in bank_df.iterrows():
        bank_date = bank_row["거래연월일"]
        bank_name = str(bank_row["상대 계좌주"]).strip()
        bank_amt = float(bank_row["입출금액"])
        match_found = False

        for _, tax_row in tax_df.iterrows():
            tax_date = tax_row["세금계산서 발급일"]
            tax_item = str(tax_row["품목명"]).strip()
            tax_amt = float(tax_row["합계"])

            # 이름 유사 + 날짜 ±3일 + 금액 ±1000원
            if (bank_name in tax_item or tax_item in bank_name) and abs((bank_date - tax_date).days) <= 3:
                if abs(bank_amt - tax_amt) <= 1000:
                    match_found = True
                    break

        if not match_found:
            results.append({
                "거래연월일": bank_date,
                "상대 계좌주": bank_name,
                "입출금액": bank_amt,
                "의심유형": "가공 또는 누락 의심"
            })

    result_df = pd.DataFrame(results)

    # -------------------------------
    # 4️⃣ 결과 요약 / 시각화
    # -------------------------------
    if not result_df.empty:
        st.success("✅ 분석 완료! 아래는 가공 의심 거래 내역입니다.")
        st.dataframe(result_df)

        # TOP 5 (금액별)
        top5 = result_df.groupby("상대 계좌주")["입출금액"].sum().abs().sort_values(ascending=False).head(5).reset_index()
        top5.columns = ["상대 계좌주", "의심금액 합계"]

        st.subheader("⚠️ 가공 거래 의심자 Top 5 (금액 기준)")
        st.table(top5)

    else:
        st.info("모든 거래가 정상으로 판별되었습니다 🎉")

else:
    st.warning("두 파일(은행 거래 + 세금계산서)을 모두 업로드하세요.")
