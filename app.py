import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def monthly_payment(principal, annual_rate, years):
    monthly_rate = annual_rate / 100 / 12
    months = years * 12
    if monthly_rate == 0:
        return principal / months
    return (principal * monthly_rate) / (1 - (1 + monthly_rate) ** -months)

def generate_amortization(loan, fixed_years, mortgage_years, fixed_rate, floating_rate):
    total_months = mortgage_years * 12
    monthly_fixed = monthly_payment(loan, fixed_rate, mortgage_years)
    monthly_floating = monthly_payment(loan, floating_rate, mortgage_years - fixed_years)

    balance = loan
    data = []

    for month in range(1, total_months + 1):
        year = (month - 1) // 12 + 1
        rate = fixed_rate if year <= fixed_years else floating_rate
        monthly_rate = rate / 100 / 12
        payment = monthly_fixed if year <= fixed_years else monthly_floating
        interest = balance * monthly_rate
        principal = payment - interest
        balance -= principal
        data.append([year, month, round(payment, 2), round(principal, 2), round(interest, 2), round(balance, 2)])

    df = pd.DataFrame(data, columns=["Year", "Month", "Payment", "Principal", "Interest", "Remaining Balance"])
    yearly = df.groupby("Year")[["Principal", "Interest"]].sum().reset_index()
    return yearly, df

def main():
    st.title("🏠 Dubai Mortgage Analyzer with Charts")

    st.sidebar.header("Input Details")
    property_price = st.sidebar.number_input("Property Price (AED)", value=2000000, step=10000)
    down_payment_pct = st.sidebar.slider("Down Payment (%)", 0, 100, 20)
    mortgage_years = st.sidebar.slider("Mortgage Term (years)", 5, 30, 25)
    fixed_years = st.sidebar.slider("Fixed Rate Duration (years)", 1, min(10, mortgage_years), 3)
    fixed_rate = st.sidebar.number_input("Fixed Interest Rate (%)", value=3.99, step=0.01)
    eibor_rate = st.sidebar.number_input("Current EIBOR (%)", value=3.5, step=0.01)
    trustee_fee = st.sidebar.number_input("Trustee Fee (AED)", value=5000, step=500)

    # Constants
    dld_fee_pct = 4
    agent_fee_pct = 2

    # Calculations
    down_payment = (down_payment_pct / 100) * property_price
    loan_amount = property_price - down_payment
    agent_fee = (agent_fee_pct / 100) * property_price
    dld_fee = (dld_fee_pct / 100) * property_price
    total_upfront_cost = down_payment + dld_fee + trustee_fee + agent_fee
    floating_rate = eibor_rate + 1.5

    # Monthly payment
    monthly_fixed = monthly_payment(loan_amount, fixed_rate, mortgage_years)
    monthly_floating = monthly_payment(loan_amount, floating_rate, mortgage_years - fixed_years)
    total_fixed = monthly_fixed * fixed_years * 12
    total_floating = monthly_floating * (mortgage_years - fixed_years) * 12
    total_payment = total_fixed + total_floating
    total_interest = total_payment - loan_amount

    st.subheader("📋 Mortgage Summary")
    st.write(f"**Loan Amount:** AED {loan_amount:,.2f}")
    st.write(f"**Down Payment:** AED {down_payment:,.2f}")
    st.write(f"**Total Upfront Cost:** AED {total_upfront_cost:,.2f}")
    st.write(f"**Monthly Payment (Fixed):** AED {monthly_fixed:,.2f}")
    st.write(f"**Monthly Payment (Floating):** AED {monthly_floating:,.2f}")
    st.write(f"**Total Interest Paid:** AED {total_interest:,.2f}")
    st.write(f"**Total Paid (Principal + Interest):** AED {total_payment:,.2f}")

    # Amortization Table
    yearly_amort, full_amort = generate_amortization(
        loan_amount, fixed_years, mortgage_years, fixed_rate, floating_rate
    )

    st.subheader("📊 Annual Breakdown: Principal vs Interest")
    st.bar_chart(yearly_amort.set_index("Year"))

    st.subheader("📈 Cumulative Repayment Over Time")
    yearly_amort["Cumulative Principal"] = yearly_amort["Principal"].cumsum()
    yearly_amort["Cumulative Interest"] = yearly_amort["Interest"].cumsum()
    st.line_chart(yearly_amort.set_index("Year")[["Cumulative Principal", "Cumulative Interest"]])

    st.subheader("🥧 Total Repayment Breakdown")
    fig, ax = plt.subplots()
    ax.pie(
        [loan_amount, total_interest],
        labels=["Principal", "Interest"],
        autopct='%1.1f%%',
        colors=["#4CAF50", "#F44336"]
    )
    ax.set_title("Total Mortgage Repayment")
    st.pyplot(fig)

if __name__ == "__main__":
    main()
