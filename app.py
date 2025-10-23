import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="세금계산서 가공거래 분석기", layout="wide")

st.title("💰 세금계산서 가공거래 분석 프로그램 (Streamlit 버전)")
st.markdown("---")

# 샘플 데이터 다운로드 링크
with open("hong_gildong_5accounts_transactions.csv", "rb") as f1, \
     open("hong_gildong_tax_invoices.xlsx", "rb") as f2:
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📂 샘플 은행계좌 파일 다운로드",
            data=f1,
            file_name="sample_bank_accounts.csv",
            mime="text/csv"
        )
    with col2:
        st.download_button(
            label="📊 샘플 세금계산서 파일 다운로드",
            data=f2,
            file_name="sample_tax_invoices.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")

# 파일 업로드
uploaded_bank = st.file_uploader("은행 계좌 내역 CSV 파일 업로드", type=["csv"])
uploaded_tax = st.file_uploader("세금계산서 엑셀 파일 업로드", type=["xlsx"])

if uploaded_bank and uploaded_tax:
    bank_df = pd.read_csv(uploaded_bank)
    tax_df = pd.read_excel(uploaded_tax)

    st.subheader("📄 업로드된 데이터 미리보기")
    st.write("은행 계좌 내역")
    st.dataframe(bank_df.head())
    st.write("세금계산서")
    st.dataframe(tax_df.head())

    # ---------------------------------------------
    # 일치 여부 판단
    # ---------------------------------------------
    def match_transactions(bank_df, tax_df):
        results = []
        for _, row in bank_df.iterrows():
            acc_no = str(row.get("본인계좌번호", ""))
            amt = abs(row.get("거래금액", 0))
            matched = tax_df[
                (tax_df["계좌번호"].astype(str) == acc_no)
                & (abs(tax_df["공급가액"] - amt) < 1)
            ]
            results.append("일치" if len(matched) > 0 else "불일치")
        bank_df["일치여부"] = results
        return bank_df

    bank_df = match_transactions(bank_df, tax_df)

    # ---------------------------------------------
    # 의심 거래 탐지 (본인계좌 간 고액거래)
    # ---------------------------------------------
    suspicious = bank_df[
        (bank_df["상대계좌주"].astype(str).str.contains("홍길동"))
        & (bank_df["거래금액"].abs() >= 1_000_000)
    ]
    suspicious["주의"] = "⚠️ 주의"
    suspicious_list = suspicious[["거래년월일", "본인계좌번호", "상대계좌번호", "거래금액", "주의"]]

    # ---------------------------------------------
    # 불일치 세금계산서 건수 및 금액
    # ---------------------------------------------
    matched_acc = bank_df.loc[bank_df["일치여부"] == "일치", "본인계좌번호"].unique()
    unmatched_invoices = tax_df[~tax_df["계좌번호"].isin(matched_acc)]
    unmatched_count = len(unmatched_invoices)
    unmatched_amount = unmatched_invoices["합계금액"].sum()

    # ---------------------------------------------
    # 타인과의 고액 거래 Top5
    # ---------------------------------------------
    others = bank_df[~bank_df["상대계좌주"].astype(str).str.contains("홍길동")]
    top5 = (
        others.groupby("상대계좌주")["거래금액"]
        .apply(lambda x: x.abs().sum())
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    top5.columns = ["거래처명", "총거래금액"]

    # ---------------------------------------------
    # 결과 표시
    # ---------------------------------------------
    st.markdown("---")
    st.subheader("📊 분석 결과")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="불일치 세금계산서 건수", value=f"{unmatched_count} 건")
    with col2:
        st.metric(label="불일치 세금계산서 총 금액", value=f"{unmatched_amount:,.0f} 원")

    st.markdown("### ⚠️ 의심 거래 목록 (본인계좌 간 100만원 이상 거래)")
    st.dataframe(suspicious_list, use_container_width=True)

    st.markdown("### 💵 타인과의 고액 거래 TOP5")
    st.dataframe(top5)

    # 그래프
    st.bar_chart(data=top5.set_index("거래처명"))

else:
    st.info("👆 은행계좌 CSV와 세금계산서 XLSX 파일을 모두 업로드하면 분석이 실행됩니다.")
