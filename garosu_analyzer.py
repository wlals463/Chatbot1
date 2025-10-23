import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="가공 거래 의심 탐지기", layout="wide")

st.title("💰 가공 거래 의심 탐지 자동분석기")
st.caption("은행 계좌 거래내역과 세금계산서 내역을 비교하여 의심 거래를 탐지합니다.")

# 파일 업로드
bank_file = st.file_uploader("📂 은행 거래내역 파일 업로드 (xlsx)", type=["xlsx"])
tax_file = st.file_uploader("📄 세금계산서 파일 업로드 (xlsx)", type=["xlsx"])

# 비교 함수
def compare_transactions(bank_df, tax_df):
    results = []
    for _, b in bank_df.iterrows():
        bank_date = pd.to_datetime(b["거래연월일"])
        bank_name = str(b["상대 계좌주"])
        bank_amt = float(b["입출금액"])
        matched = False
        
        for _, t in tax_df.iterrows():
            tax_date = pd.to_datetime(t["세금계산서 발급일"])
            tax_name = str(t["품목명"])
            tax_amt = float(t["합계"])
            
            if (bank_name in tax_name) or (tax_name in bank_name):
                if abs((bank_date - tax_date).days) <= 3 and abs(bank_amt - tax_amt) <= 1000:
                    matched = True
                    results.append({
                        "은행날짜": bank_date.date(),
                        "상대계좌주": bank_name,
                        "입출금액": bank_amt,
                        "세금계산서발급일": tax_date.date(),
                        "품목명": tax_name,
                        "세금계산서금액": tax_amt,
                        "비교결과": "일치",
                        "의심유형": "정상 거래"
                    })
                    break
                    
        if not matched:
            results.append({
                "은행날짜": bank_date.date(),
                "상대계좌주": bank_name,
                "입출금액": bank_amt,
                "세금계산서발급일": None,
                "품목명": None,
                "세금계산서금액": None,
                "비교결과": "불일치",
                "의심유형": "가공 또는 누락 의심"
            })
    return pd.DataFrame(results)

# 실행
if bank_file and tax_file:
    bank_df = pd.read_excel(bank_file)
    tax_df = pd.read_excel(tax_file)

    st.success("✅ 파일 업로드 완료! 분석 중입니다...")
    result_df = compare_transactions(bank_df, tax_df)

    st.subheader("📊 분석 결과 미리보기")
    st.dataframe(result_df, use_container_width=True)

    # 결과 엑셀 파일로 변환
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="결과")
    output.seek(0)

    st.download_button(
        label="📥 분석 결과 엑셀 다운로드",
        data=output,
        file_name="가공거래_분석결과.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Top5 의심 거래자 표시
    suspicious_df = result_df[result_df["의심유형"].str.contains("의심")]
    if not suspicious_df.empty:
        top5 = (
            suspicious_df.groupby("상대계좌주")["입출금액"]
            .sum()
            .reset_index()
            .sort_values("입출금액", ascending=False)
            .head(5)
        )
        st.subheader("🚨 가공 거래 의심자 금액별 TOP 5")
        st.table(top5)
    else:
        st.info("가공 거래 의심 내역이 없습니다 ✅")
else:
    st.warning("두 개의 엑셀 파일을 모두 업로드해주세요.")
