import streamlit as st
from components.calculator import show_mortgage_calculator
from components.comparison import show_buy_vs_rent

def main():
    st.set_page_config(
        page_title="Dubai Mortgage Analyzer",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 Dubai Mortgage Analyzer")

    tabs = st.tabs(["📊 Mortgage Calculator", "🏡 Buy vs Rent Comparison"])

    with tabs[0]:
        show_mortgage_calculator()

    with tabs[1]:
        show_buy_vs_rent()

if __name__ == "__main__":
    main()
